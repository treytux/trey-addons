###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import math

from odoo import Command, _, api, exceptions, fields, models


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
    need_change_amount = fields.Boolean(
        string='Need change amount',
        compute='_compute_need_change_amount',
    )
    company_currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='sale_id.company_id.currency_id',
        readonly=True,
    )
    amount = fields.Monetary(
        string='Amount paid',
        readonly=False,
        compute='_compute_amount',
        compute_sudo=False,
        currency_field='company_currency_id',
    )
    amount_total = fields.Monetary(
        string='Total',
        compute='_compute_amount',
        compute_sudo=False,
        currency_field='company_currency_id',
    )
    amount_change = fields.Monetary(
        string='Change',
        compute='_compute_amount',
        compute_sudo=False,
        currency_field='company_currency_id',
        store=True,
    )
    step = fields.Integer(
        string='step',
    )
    show_print_invoice = fields.Boolean(
        string='Show print invoice button',
    )
    avoid_credit_sale_session = fields.Boolean(
        related='partner_id.avoid_credit_sale_session',
    )
    line_ids = fields.One2many(
        comodel_name='sale.order.confirm_and_pay.lot_line',
        inverse_name='wizard_id',
        string='lines',
    )
    multi_payment = fields.Boolean(
        string='Multi payment',
    )
    payment_line_ids = fields.One2many(
        comodel_name='sale.order.confirm_and_pay.line',
        inverse_name='wizard_id',
        string='Payment Lines',
    )

    @api.onchange('multi_payment')
    def onchange_multi_payment(self):
        self.payment_line_ids = [Command.clear()]
        self.amount = 0
        self.amount_change = 0

    def _compute_need_change_amount(self):
        for sale in self:
            sale.need_change_amount = sale.journal_id.type == 'cash'

    def fill_line_ids(self):
        self.ensure_one()
        wizard_line_obj = self.env['sale.order.confirm_and_pay.lot_line']
        lot_lines = self.sale_id.order_line.filtered(
            lambda ln: ln.product_id and ln.product_id.tracking != 'none')
        if not lot_lines:
            self.line_ids = False
            return
        for line in lot_lines:
            if lot_lines.product_id.tracking == 'serial':
                for _i in range(math.ceil(line.product_uom_qty)):
                    wizard_line_obj.create({
                        'wizard_id': self.id,
                        'product_id': line.product_id.id,
                        'quantity': 1,
                    })
                continue
            wizard_line_obj.create({
                'wizard_id': self.id,
                'product_id': line.product_id.id,
                'quantity': line.product_uom_qty,
            })

    def fill_lots(self, move_lines):
        move_lines = move_lines.filtered(
            lambda m: m.product_id.tracking != 'none')
        for move in move_lines:
            move._do_unreserve()
            lines = self.line_ids.filtered(
                lambda ln: ln.product_id == move.product_id)
            qty_done = 0
            for line in lines:
                qty_done += move._update_reserved_quantity(
                    move.product_uom_qty, line.quantity, move.location_id,
                    lot_id=line.lot_id, strict=False)
            if qty_done != move.product_uom_qty:
                raise exceptions.UserError(
                    _(
                        'It is not possible to perform the operation. Product '
                        '"[%s] %s" requires moving %s from location "%s" to '
                        'location "%s", you request move %s.'
                    ) % (
                        move.product_id.default_code or '',
                        move.product_id.name,
                        move.product_uom_qty,
                        move.location_id.name,
                        move.location_dest_id.name,
                        qty_done,
                    )
                )
            for stock_move_line in move.move_line_ids:
                stock_move_line.qty_done = stock_move_line.reserved_uom_qty

    @api.model_create_multi
    def create(self, vals):
        wizard = super().create(vals)
        wizard.fill_line_ids()
        wizard.step = 0 if wizard.line_ids else 1
        sales_team = wizard.session_id.team_id
        if 'amount' not in vals and sales_team.autocomplete_amount:
            wizard.amount = (
                wizard.session_id.team_id.autocomplete_amount
                and wizard.amount_total or 0.0)
        return wizard

    @api.depends(
        'sale_id', 'amount', 'payment_line_ids', 'payment_line_ids.amount')
    def _compute_amount(self):
        for wizard in self:
            if not wizard.sale_id:
                continue
            wizard.amount_total = wizard.sale_id.amount_total
            if wizard.payment_line_ids:
                wizard.amount = sum(wizard.payment_line_ids.mapped('amount'))
            wizard.amount_change = wizard.amount - wizard.amount_total

    def action_lot_confirm(self):
        self.step += 1
        return self._reopen_view()

    def action_pay(self):
        self.ensure_one()
        res = self.sale_id.session_pay(
            amount=self.amount_total, payment_journal=self.journal_id,
            payment_line_ids=self.payment_line_ids)
        if res is not True:
            return res
        self.step += 1
        self.show_print_invoice = True
        return self.action_print_invoice()

    def action_credit(self):
        self.ensure_one()
        res = self.sale_id.session_confirm()
        if res is not True:
            return res
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
        return self.sale_id.picking_ids.do_print_picking_valued()

    def action_print_invoice(self):
        team_journal = self.session_id.team_id.simplified_journal_id
        if team_journal == self.sale_id.invoice_ids.journal_id:
            report = self.env.ref(
                'print_formats_account_ticket.'
                'report_account_move_ticket_create')
            return report.report_action(self.sale_id.invoice_ids)
        report = self.env.ref('account.account_invoices')
        return report.report_action(self.sale_id.invoice_ids)

    def _reopen_view(self, ctx=None):
        view = self.env.ref('sale_session.sale_order_confirm_and_pay_wizard')
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'view_id': view.id,
            'target': 'new',
            'context': ctx or {},
        }


class SaleOrderConfirmAndPayPayLine(models.TransientModel):
    _name = 'sale.order.confirm_and_pay.line'
    _description = 'Sale session wizard payment lines'

    wizard_id = fields.Many2one(
        comodel_name='sale.order.confirm_and_pay',
        string='Wizard',
    )
    payment_journal_ids = fields.Many2many(
        related='wizard_id.payment_journal_ids',
    )
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Payment Method',
        domain='[("id", "in", payment_journal_ids)]',
        required=True,
    )
    company_currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='wizard_id.company_currency_id',
    )
    amount = fields.Monetary(
        string='Amount',
        required=True,
        currency_field='company_currency_id',
    )


class SaleOrderConfirmAndPayLotLine(models.TransientModel):
    _name = 'sale.order.confirm_and_pay.lot_line'
    _description = 'Wizard to confirm and and select lot lines'

    wizard_id = fields.Many2one(
        comodel_name='sale.order.confirm_and_pay',
        string='Wizard',
        required=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        readonly=True,
    )
    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Lot',
    )
    quantity = fields.Float(
        string='Quantity',
    )

    def action_split_line(self):
        pass
