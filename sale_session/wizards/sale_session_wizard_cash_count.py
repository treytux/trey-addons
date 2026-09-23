###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, fields, models


class SaleSessionWizardCashCount(models.TransientModel):
    _name = 'sale.session.wizard_cash_count'
    _description = 'Wizard to cash count a session'

    session_id = fields.Many2one(
        comodel_name='sale.session',
        string='Sale Session',
        required=True,
        readonly=True,
    )
    team_id = fields.Many2one(
        related='session_id.team_id',
    )
    payment_journal_ids = fields.Many2many(
        related='session_id.team_id.payment_journal_ids',
    )
    type = fields.Selection(
        selection=[
            ('open', 'Open cash'),
            ('close', 'Close cash'),
        ],
        string='Type',
        required=True,
    )
    company_currency = fields.Many2one(
        string='Currency',
        related='session_id.company_id.currency_id',
        readonly=True,
        relation='res.currency',
    )
    journal_cash_count_ids = fields.One2many(
        comodel_name='sale.session.wizard_cash_count.journal',
        inverse_name='cash_count_id',
        string='Journal cash counts',
    )
    open_cash_count_total = fields.Monetary(
        related='session_id.open_cash_count_total',
        currency_field='company_currency',
    )

    @api.model
    def create(self, vals):
        wizard = super().create(vals)
        for journal in wizard.team_id.payment_journal_ids.filtered(
                lambda j: j.type == 'cash'):
            cash_count_journal = wizard.journal_cash_count_ids.create({
                'cash_count_id': wizard.id,
                'journal_id': journal.id,
            })
            for value in wizard.team_id.get_cash_money_values():
                cash_count_journal.line_ids.create({
                    'cash_count_journal_id': cash_count_journal.id,
                    'value': value,
                })
        return wizard

    def action_confirm(self):
        self.ensure_one()
        cash_count_obj = self.env['sale.session.cash_count']
        cash_count_line_obj = self.env['sale.session.cash_count_line']
        for journal_cash_count in self.journal_cash_count_ids:
            cash_count = cash_count_obj.create({
                'session_id': self.session_id.id,
                'journal_id': journal_cash_count.journal_id.id,
                'type': self.type,
            })
            for line in journal_cash_count.line_ids:
                cash_count_line_obj.create({
                    'cash_count_id': cash_count.id,
                    'value': line.value,
                    'quantity': line.quantity,
                })

        if self.type == 'close':
            return self.session_id.action_close()
        self.session_id.write({
            'cash_count_start': sum(self.mapped(
                'journal_cash_count_ids.amount_total')),
            'state': 'open',
        })
        if not self.session_id.open_cash_count_mismatch:
            return {'type': 'ir.actions.act_window_close'}
        reference = _('Mismatch when open sale session %s') % (
            self.session_id.name)
        journal = self.team_id.cash_payment_journal_id
        if not journal.default_debit_account_id:
            raise exceptions.UserError(
                _('Journal "%s" needs a default debit account') % journal.name)
        if not self.team_id.mismatch_account:
            raise exceptions.UserError(
                _('Team "%s" needs a mismatch account') % self.team_id.name)
        mismatch = self.session_id.open_cash_count_mismatch
        debit_vals = {
            'name': reference,
            'partner_id': self.session_id.company_id.partner_id.id,
            'debit': abs(mismatch) if mismatch > 0 else 0,
            'credit': abs(mismatch) if mismatch < 0 else 0,
            'account_id': journal.default_debit_account_id.id,
        }
        credit_vals = debit_vals.copy()
        credit_vals.update({
            'debit': debit_vals['credit'],
            'credit': debit_vals['debit'],
            'account_id': self.team_id.mismatch_account.id,
        })
        mismatch_move = self.env['account.move'].create({
            'ref': reference,
            'journal_id': journal.id,
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
        })
        self.session_id.mismatch_open_move_ids = [(4, mismatch_move.id)]
        return {'type': 'ir.actions.act_window_close'}

    def action_get(self):
        self.ensure_one()
        action = self.env.ref(
            'sale_session.sale_session_wizard_cash_count_action').read()[0]
        if not self.journal_cash_count_ids:
            view = self.env.ref(
                'sale_session.sale_session_wizard_cash_count_editable_wizard')
            action['view_id'] = view.id
        action['res_id'] = self.id
        return action


class SaleSessionWizardCashCountJournal(models.TransientModel):
    _name = 'sale.session.wizard_cash_count.journal'
    _description = 'Cash count journal wizard'

    cash_count_id = fields.Many2one(
        comodel_name='sale.session.wizard_cash_count',
        string='Cash count',
        ondelete='cascade',
        required=True,
        readonly=True,
    )
    line_ids = fields.One2many(
        comodel_name='sale.session.wizard_cash_count.journal_line',
        inverse_name='cash_count_journal_id',
        string='Lines',
    )
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        readonly=True,
    )
    company_currency = fields.Many2one(
        related='cash_count_id.company_currency',
        relation='res.currency',
        readonly=True,
    )
    amount_total = fields.Monetary(
        string='Amount Total',
        compute='_compute_amount_total',
        currency_field='company_currency',
    )
    close_cash_count_mismatch = fields.Monetary(
        string='Mismatch',
        compute='_compute_close_cash_count_mismatch',
        currency_field='company_currency',
    )

    def _compute_close_cash_count_mismatch(self):
        for wizard in self:
            if wizard.type != 'close' or not wizard.session_id.payment_ids:
                continue

    @api.depends('line_ids', 'line_ids.quantity')
    def _compute_amount_total(self):
        for wizard in self:
            wizard.amount_total = sum(
                wizard.line_ids.mapped('amount_subtotal'))
            wizard.close_cash_count_mismatch = (
                wizard.cash_count_id.team_id.get_actual_total_cash(
                    wizard.journal_id)
                - wizard.amount_total)


class SaleSessionWizardCashCountJournalLine(models.TransientModel):
    _name = 'sale.session.wizard_cash_count.journal_line'
    _description = 'Cash count lines wizard'

    cash_count_journal_id = fields.Many2one(
        comodel_name='sale.session.wizard_cash_count.journal',
        string='Cash count journal',
        ondelete='cascade',
        required=True,
        readonly=True,
    )
    value = fields.Float(
        string='Value',
    )
    quantity = fields.Float(
        string='Quantity',
    )
    amount_subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_amount_subtotal',
    )

    @api.depends('value', 'quantity')
    def _compute_amount_subtotal(self):
        for line in self:
            line.amount_subtotal = line.value * line.quantity
