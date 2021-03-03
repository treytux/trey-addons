###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import date

from odoo import _, fields, models


class ProductBusinessUnit(models.Model):
    _inherit = 'product.business.unit'

    quotation_count = fields.Integer(
        compute='_compute_sales',
        string='Quotations',
        readonly=True,
    )
    quotation_order_count = fields.Integer(
        compute='_compute_sales',
        string='Quotation Orders',
        readonly=True,
    )
    quotation_amount = fields.Float(
        compute='_compute_sales',
        string='Quotations Revenues',
        readonly=True,
    )
    sale_count = fields.Integer(
        compute='_compute_sales',
        string='Sales',
        readonly=True,
    )
    sale_order_count = fields.Integer(
        compute='_compute_sales',
        string='Sale Orders',
        readonly=True,
    )
    sale_amount = fields.Float(
        compute='_compute_sales',
        string='Sales Revenues',
        readonly=True,
    )
    invoice_count = fields.Integer(
        compute='_compute_invoices',
        string='Sales',
        readonly=True,
    )
    invoice_order_count = fields.Integer(
        compute='_compute_invoices',
        string='Sale Orders',
        readonly=True,
    )
    invoice_amount = fields.Float(
        compute='_compute_invoices',
        string='Sales Revenues',
        readonly=True,
    )
    dashboard_graph_model = fields.Selection(
        selection_add=[
            ('sale.report', 'Sales'),
            ('account.invoice.report', 'Invoices'),
        ],
    )
    invoiced = fields.Integer(
        compute='_compute_invoices',
        string='Invoiced This Month',
        readonly=True,
        help=(
            'Invoice revenue for the current month. This is the amount the '
            'sales unit has invoiced this month. It is used to compute the '
            'progression ratio of the current and target revenue on the '
            'kanban view.'
        ),
    )
    invoiced_target = fields.Integer(
        string='Invoicing Target',
        help=(
            'Target of invoice revenue for the current month. This is the '
            'amount the sales unit estimates to be able to invoice this '
            'month.'
        ),
    )

    def _compute_sales(self):
        for unit in self:
            lines = self.env['sale.order.line'].search([
                ('product_id', '!=', False),
                ('product_id.unit_id', '=', unit.id)])
            quotation_lines = lines.filtered(
                lambda l: l.order_id.state in ['draft', 'sent'])
            sale_lines = lines.filtered(
                lambda l: l.order_id.state in ['sale', 'done'])
            unit.quotation_count = len(quotation_lines)
            unit.quotation_order_count = len(
                quotation_lines.mapped('order_id'))
            unit.quotation_amount = sum(
                quotation_lines.mapped('price_subtotal'))
            unit.sale_count = len(sale_lines)
            unit.sale_order_count = len(
                sale_lines.mapped('order_id'))
            unit.sale_amount = sum(sale_lines.mapped('price_subtotal'))

    def _compute_invoices(self):
        for unit in self:
            lines = self.env['account.invoice.line'].search([
                ('invoice_id.state', 'not in', ['cancel', 'draft']),
                ('product_id', '!=', False),
                ('product_id.unit_id', '=', unit.id)])
            unit.invoice_count = len(lines)
            unit.invoice_amount = sum(lines.mapped('price_subtotal'))
            invoices = lines.mapped('invoice_id')
            unit.invoice_order_count = len(invoices)
            month_invoices = invoices.filtered(
                lambda i:
                    i.date <= date.today()
                    and i.date >= date.today().replace(day=1)
            )
            unit.invoiced = sum(month_invoices.mapped('amount_untaxed_signed'))

    def update_invoiced_target(self, value):
        return self.write({'invoiced_target': round(float(value or 0))})

    def action_view_quotation_lines(self):
        self.ensure_one()
        lines = self.env['sale.order.line'].search([
            ('order_id.state', 'in', ['draft', 'sent']),
            ('product_id', '!=', False),
            ('product_id.unit_id', '=', self.id)])
        action = self.env.ref(
            'sale_business_unit.sale_order_line_quotation_action').read()[0]
        action['domain'] = [('id', 'in', lines.ids)]
        return action

    def action_view_sale_lines(self):
        self.ensure_one()
        lines = self.env['sale.order.line'].search([
            ('order_id.state', 'in', ['sale', 'done']),
            ('product_id', '!=', False),
            ('product_id.unit_id', '=', self.id)])
        action = self.env.ref(
            'sale_business_unit.sale_order_line_sale_action').read()[0]
        action['domain'] = [('id', 'in', lines.ids)]
        return action

    def action_view_invoice_lines(self):
        self.ensure_one()
        lines = self.env['account.invoice.line'].search([
            ('invoice_id.state', 'not in', ['cancel', 'draft']),
            ('product_id', '!=', False),
            ('product_id.unit_id', '=', self.id)])
        action = self.env.ref(
            'sale_business_unit.account_invoice_line_action').read()[0]
        action['domain'] = [('id', 'in', lines.ids)]
        return action

    def action_view_quotation(self):
        self.ensure_one()
        lines = self.env['sale.order.line'].search([
            ('order_id.state', 'in', ['draft', 'sent']),
            ('product_id', '!=', False),
            ('product_id.unit_id', '=', self.id)])
        action = self.env.ref('sale.action_quotations').read()[0]
        action.update({
            'domain': [('id', 'in', lines.mapped('order_id').ids)],
            'context': {},
        })
        return action

    def action_view_sale(self):
        self.ensure_one()
        lines = self.env['sale.order.line'].search([
            ('product_id', '!=', False),
            ('product_id.unit_id', '=', self.id)])
        sale_lines = lines.filtered(
            lambda l: l.order_id.state in ['sale', 'done'])
        action = self.env.ref('sale.action_orders').read()[0]
        action.update({
            'domain': [('id', 'in', sale_lines.mapped('order_id').ids)],
            'context': {},
        })
        return action

    def action_view_invoice(self):
        self.ensure_one()
        lines = self.env['account.invoice.line'].search([
            ('product_id', '!=', False),
            ('product_id.unit_id', '=', self.id)])
        invoice_lines = lines.filtered(
            lambda l: l.invoice_id.state not in ['cancel', 'draft'])
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        action.update({
            'domain': [('id', 'in', invoice_lines.mapped('invoice_id').ids)],
            'context': {},
        })
        return action

    def _graph_date_column(self):
        if self.dashboard_graph_model == 'sale.report':
            return 'confirmation_date'
        elif self.dashboard_graph_model == 'account.invoice.report':
            return 'date'
        return super()._graph_date_column()

    def _graph_y_query(self):
        if self.dashboard_graph_model == 'sale.report':
            return 'SUM(price_subtotal)'
        elif self.dashboard_graph_model == 'account.invoice.report':
            return 'SUM(price_total)'
        return super()._graph_y_query()

    def _extra_sql_conditions(self):
        if self.dashboard_graph_model == 'sale.report':
            return "AND state in ('sale', 'done')"
        elif self.dashboard_graph_model == 'account.invoice.report':
            return "AND state in ('open', 'in_payment', 'paid')"
        return super()._extra_sql_conditions()

    def _graph_title_and_key(self):
        if self.dashboard_graph_model == 'sale.report':
            return ['', _('Sales: Untaxed Total')]
        elif self.dashboard_graph_model == 'account.invoice.report':
            return ['', _('Invoices: Untaxed Total')]
        return super()._graph_title_and_key()
