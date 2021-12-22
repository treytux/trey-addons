###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrderConfirmAndPay(models.TransientModel):
    _name = 'sale.order.confirm_and_pay'
    _description = 'Wizard to confirm and pay a sale order'

    sale_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale order',
        required=True,
    )
    session_id = fields.Many2one(
        related='sale_id.session_id',
    )
    invoice_ids = fields.Many2many(
        related='sale_id.invoice_ids',
    )
    partner_id = fields.Many2one(
        related='sale_id.partner_id',
    )
    risk_exception = fields.Boolean(
        related='partner_id.risk_exception',
    )
    payment_journal_ids = fields.Many2many(
        related='session_id.team_id.payment_journal_ids',
    )
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        domain='[("id", "in", payment_journal_ids)]',
        string='Payment journal',
    )
    company_currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='sale_id.company_id.currency_id',
        readonly=True,
    )
    amount = fields.Monetary(
        string='Amount paid',
        currency_field='company_currency_id',
    )
    amount_total = fields.Monetary(
        string='Total',
        compute='_compute_amount',
        currency_field='company_currency_id',
    )
    amount_change = fields.Monetary(
        string='Change',
        compute='_compute_amount',
        currency_field='company_currency_id',
    )
    step = fields.Integer(
        string='step',
    )
    show_print_invoice = fields.Boolean(
        string='Show print invoice button',
    )

    @api.depends('sale_id', 'amount')
    def _compute_amount(self):
        for wizard in self:
            if not wizard.sale_id:
                continue
            wizard.amount_total = wizard.sale_id.amount_total
            wizard.amount_change = wizard.amount - wizard.amount_total

    def action_pay(self):
        self.ensure_one()
        self.sale_id.session_pay(self.amount_total, self.journal_id)
        self.step += 1
        self.show_print_invoice = True
        return self.action_print_invoice()

    def action_credit(self):
        self.ensure_one()
        self.sale_id.session_confirm()
        self.step += 1
        return self.action_print_picking()

    def action_confirm(self):
        self.ensure_one()
        self.sale_id.with_context(open_wizard=False).action_confirm()
        return {'type': 'ir.actions.act_window_close'}

    def action_print_picking(self):
        if not hasattr(self.sale_id.picking_ids, 'do_print_picking_valued'):
            report = self.env.ref('stock.action_report_delivery')
            return report.report_action(self.sale_id.picking_ids)
        # For compatibility print_formats_picking_valued
        return self.sale_id.picking_ids.do_print_picking_valued()

    def action_print_invoice(self):
        team_journal = self.session_id.team_id.simplified_journal_id
        if team_journal == self.sale_id.invoice_ids.journal_id:
            report = self.env.ref(
                'print_formats_account_ticket.'
                'report_account_invoice_ticket_create')
            return report.report_action(self.sale_id.invoice_ids)
        report = self.env.ref('account.account_invoices')
        return report.report_action(self.sale_id.invoice_ids)
