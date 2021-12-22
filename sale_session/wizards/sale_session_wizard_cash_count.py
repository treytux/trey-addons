###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


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
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        domain='[("id", "in", payment_journal_ids), ("type", "=", "cash")]',
        string='Payment journal',
    )
    company_currency = fields.Many2one(
        string='Currency',
        related='session_id.company_id.currency_id',
        readonly=True,
        relation='res.currency',
    )
    type = fields.Selection(
        selection=[
            ('open', 'Open cash'),
            ('close', 'Close cash'),
        ],
        string='Type',
        required=True,
    )
    line_ids = fields.One2many(
        comodel_name='sale.session.wizard_cash_count.line',
        inverse_name='cash_count_id',
        string='Lines',
    )
    amount_total = fields.Monetary(
        string='Amount Total',
        compute='_compute_amount_total',
        currency_field='company_currency',
    )
    open_cash_count_total = fields.Monetary(
        related='session_id.open_cash_count_total',
        currency_field='company_currency',
    )
    close_cash_count_mismatch = fields.Monetary(
        string='Mismatch',
        compute='_compute_close_cash_count_mismatch',
        currency_field='company_currency',
    )

    @api.model
    def create(self, vals):
        wizard = super().create(vals)
        for value in wizard.team_id.get_cash_money_values():
            wizard.line_ids.create({
                'cash_count_id': wizard.id,
                'value': value,
            })
        return wizard

    def _compute_close_cash_count_mismatch(self):
        for wizard in self:
            if wizard.type != 'close' or not wizard.session_id.payment_ids:
                continue

    @api.depends('line_ids', 'line_ids.quantity')
    def _compute_amount_total(self):
        for wizard in self:
            wizard.amount_total = sum(
                wizard.line_ids.mapped('amount_subtotal'))
            if wizard.type != 'close':
                continue
            amount_cash_payment = wizard.session_id.payment_ids.filtered(
                lambda p: p.journal_id.type == 'cash').mapped('amount')
            wizard.close_cash_count_mismatch = sum(
                amount_cash_payment) - wizard.amount_total

    def action_confirm(self):
        self.ensure_one()
        cash_count_obj = self.env['sale.session.cash_count']
        for line in self.line_ids:
            cash_count_obj.create({
                'session_id': self.session_id.id,
                'type': self.type,
                'value': line.value,
                'quantity': line.quantity,
            })
        if self.type == 'close':
            return self.session_id.action_close()
        self.session_id.write({
            'balance_start': self.amount_total,
            'state': 'open',
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_get(self):
        self.ensure_one()
        action = self.env.ref(
            'sale_session.sale_session_wizard_cash_count_action').read()[0]
        if not self.line_ids:
            view = self.env.ref(
                'sale_session.sale_session_wizard_cash_count_editable_wizard')
            action['view_id'] = view.id
        action['res_id'] = self.id
        return action


class SaleSessionWizardCashCountLine(models.TransientModel):
    _name = 'sale.session.wizard_cash_count.line'
    _description = 'Cash count lines wizard'

    cash_count_id = fields.Many2one(
        comodel_name='sale.session.wizard_cash_count',
        string='Cash count',
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
