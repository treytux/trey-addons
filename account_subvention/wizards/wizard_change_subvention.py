###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models
from odoo.tools.float_utils import float_round


class WizardChangeSubvention(models.TransientModel):
    _name = 'wizard.change.subvention'
    _description = 'Wizard change subvention'

    subvention_percent = fields.Float(
        string='Subvention (%)',
        default=0.00,
        required=True,
    )
    lines = fields.One2many(
        comodel_name='wizard.change.subvention.line',
        inverse_name='wizard_id',
        string='Invoices',
    )
    state = fields.Selection(
        string='State',
        selection=[
            ('step_1', 'Step 1'),
            ('step_2', 'Step 2'),
            ('done', 'Done'),
        ],
        required=True,
        default='step_1',
    )
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        domain='[("type", "=", "general")]',
        required=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
    )

    @api.multi
    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {}}

    @api.multi
    def action_to_step_2(self):
        self.ensure_one()
        if self.subvention_percent == 0.00:
            raise exceptions.Warning(
                _('Please input % distinct to 0,00'))
        partner = self.env['account.invoice'].browse(
            self.env.context['active_id'])
        invoice_lines = self.env['account.invoice.line'].search([
            ('partner_id', '=', partner.id),
            ('subvention_percent', '!=', 0), ('subvention_id', '!=', False)])
        for invoice_line in invoice_lines:
            if invoice_line.invoice_id.type != 'out_invoice' and \
                    invoice_line.invoice_id.state not in ('paid', 'open'):
                continue
            self.env['wizard.change.subvention.line'].create({
                'wizard_id': self.id,
                'invoice_id': invoice_line.invoice_id.id,
                'invoice_line_id': invoice_line.id})
        self.write({'partner_id': partner.id, 'state': 'step_2'})
        return self._reopen_view()

    @api.multi
    def action_to_step_done(self):
        self.ensure_one()
        for line in self.lines:
            move_subvention = line.invoice_id.move_id.line_ids.filtered(
                lambda mv:
                    mv.subvention_id
                    and mv.subvention_percent
                    and mv.account_id == line.invoice_id.account_id[0]
            )
            if not move_subvention:
                raise exceptions.Warning(
                    _('Not account move subvention for invoice: %s') %
                    line.invoice_number)
            dp = self.env['decimal.precision'].precision_get('Account')
            new_subvention = float_round(
                line.invoice_line_price * self.subvention_percent / 100, dp)
            old_subvention = float_round(
                line.invoice_line_price
                * line.invoice_subvention_percent
                / 100, dp)
            amount_correction = new_subvention - old_subvention
            narration = _('''Invoice: %s Old Subvention: %s
                New Subvention: %s''') % (line.invoice_number,
                                          line.invoice_subvention_percent,
                                          self.subvention_percent)
            ref = _('Correction of invoice: %s') % line.invoice_number,
            new_move = self.env['account.move'].create({
                'journal_id': self.journal_id.id,
                'ref': ref[0],
                'narration': narration})
            if amount_correction > 0:
                move_lines = self.line_get_convert(
                    line=line, move_type='credit', amount=amount_correction,
                    ref=ref, move=new_move)
                for move_line in move_lines:
                    self.env['account.move.line'].create(move_line)
            else:
                move_lines = self.line_get_convert(
                    line=line, move_type='debit', amount=amount_correction,
                    ref=ref, move=new_move)
                for move_line in move_lines:
                    self.env['account.move.line'].create(move_line)
            line.invoice_line_id.subvention_percent = self.subvention_percent
            move_subvention.subvention_percent = self.subvention_percent
            self.partner_id.subvention_percent = self.subvention_percent
            line.invoice_id.message_post(body=narration)
            new_move.button_validate()

    @api.model
    def line_get_convert(
            self, line, move_type='credit', ref='/', amount=0.00, move=None):
        if move_type == 'credit':
            customer_line = {
                'partner_id': self.partner_id.id,
                'name': ref[0],
                'move_id': move.id,
                'debit': 0.00,
                'credit': amount,
                'account_id': line.invoice_id.account_id.id}
            subvention_line = {
                'partner_id': self.partner_id.id,
                'name': ref[0],
                'move_id': move.id,
                'debit': amount,
                'credit': 0.00,
                'account_id':
                    line.invoice_subvention_id.account_id.id}
        if move_type == 'debit':
            customer_line = {
                'partner_id': self.partner_id.id,
                'name': ref[0],
                'move_id': move.id,
                'debit': -amount,
                'credit': 0.00,
                'account_id': line.invoice_id.account_id.id}
            subvention_line = {
                'partner_id': self.partner_id.id,
                'name': ref[0],
                'move_id': move.id,
                'debit': 0.00,
                'credit': -amount,
                'account_id':
                    line.invoice_subvention_id.account_id.id}
        return customer_line, subvention_line


class WizardChangeSubventionLine(models.TransientModel):
    _name = 'wizard.change.subvention.line'
    _description = 'Wizard change subvention line'

    wizard_id = fields.Many2one(
        comodel_name='wizard.change.subvention',
        string='Wizard',
        ondelete='cascade',
        index=True,
        readonly=True,
        required=True,
    )
    invoice_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice',
    )
    invoice_date = fields.Date(
        related='invoice_id.date_invoice',
    )
    invoice_number = fields.Char(
        related='invoice_id.number',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        change_default=True,
        required=True,
        readonly=True,
        default=lambda self: self.env.user.company_id,
    )
    company_currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        string="Company Currency",
        readonly=True,
    )
    invoice_amount_untaxed = fields.Monetary(
        related='invoice_id.amount_untaxed',
        currency_field='company_currency_id',
    )
    invoice_amount_total = fields.Monetary(
        related='invoice_id.amount_total',
        currency_field='company_currency_id',
    )
    invoice_move_id = fields.Many2one(
        related='invoice_id.move_id',
    )
    invoice_line_id = fields.Many2one(
        comodel_name='account.invoice.line',
        string='Line',
    )
    invoice_subvention_percent = fields.Float(
        related='invoice_line_id.subvention_percent',
    )
    invoice_subvention_id = fields.Many2one(
        related='invoice_line_id.subvention_id',
    )
    invoice_line_price = fields.Monetary(
        related='invoice_line_id.price_subtotal',
        currency_field='company_currency_id',
    )
