###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_return = fields.Boolean(
        string='Is Return',
    )
    state_return = fields.Selection([
        ('draft', 'Draft Return'),
        ('sent', 'Sent Return'),
        ('sale', 'Sale Return'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')],
        string='Sale Return Status',
        compute='_compute_state_return',
    )
    is_returnable = fields.Boolean(
        string='Is returnable',
        compute='_compute_is_returnable',
    )
    returnable_date_to = fields.Datetime(
        string='Returnable date to',
        compute='_compute_is_returnable',
    )
    parent_sale_order = fields.Many2one(
        comodel_name='sale.order',
        string='Parent Sale Order',
    )
    sale_order_return_count = fields.Integer(
        string='Return count',
        compute='_compute_sale_order_return_count',
    )

    @api.depends('state')
    def _compute_state_return(self):
        for sale in self:
            sale.state_return = sale.state

    @api.depends('order_line')
    def _compute_is_returnable(self):
        for order in self:
            order.is_returnable = any([
                line.is_returnable for line in order.order_line])
            order.returnable_date_to = order.order_line and max([
                line.returnable_date for line in order.order_line]) or False

    @api.model
    def create(self, vals):
        if vals.get('is_return') and 'name' not in vals:
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.return')
        return super().create(vals)

    def check_return_date(self, order):
        for line in order.order_line:
            if (
                line.parent_sale_order_line
                    and line.product_id.type == 'product'):
                parent_line = line.parent_sale_order_line
                if parent_line.returnable_date < order.date_order:
                    raise UserError(
                        _('Return time exceeded for product %s')
                        % line.product_id.name)

    @api.multi
    def action_confirm(self):
        for order in self:
            if not self.is_return:
                continue
            self.check_return_date(order)
        return super().action_confirm()

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        def recompute_origin(invoice):
            sale_names = list({
                s.order_id.name
                for i in invoice.invoice_line_ids
                for s in i.sale_line_ids})
            invoice.origin = ', '.join(sale_names)

        invoice_ids = super().action_invoice_create(grouped, final)
        for invoice in self.env['account.invoice'].browse(invoice_ids):
            if invoice.amount_total != 0:
                continue
            new_invoice = invoice.copy({
                'type': 'out_refund',
                'invoice_line_ids': False})
            for line in invoice.invoice_line_ids:
                if line.quantity > 0:
                    continue
                line.write({
                    'invoice_id': new_invoice.id,
                    'quantity': line.quantity * -1})
            for invoice in [new_invoice, invoice]:
                recompute_origin(invoice)
                invoice.compute_taxes()
            if new_invoice.amount_total == 0:
                new_invoice.unlink()
            else:
                invoice_ids.append(new_invoice.id)
        return invoice_ids

    @api.multi
    def _get_tax_amount_by_group(self):
        self.ensure_one()
        if not self.is_return:
            return super()._get_tax_amount_by_group()
        res = {}
        for line in self.order_line:
            price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
            qty = (line.product_uom_qty * -1) + line.qty_change
            taxes = line.tax_id.compute_all(
                price_reduce, quantity=qty,
                product=line.product_id,
                partner=self.partner_shipping_id)['taxes']
            for tax in line.tax_id:
                group = tax.tax_group_id
                res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                for t in taxes:
                    tax_ids = tax.children_tax_ids.ids
                    if t['id'] == tax.id or t['id'] in tax_ids:
                        res[group]['amount'] += t['amount']
                        res[group]['base'] += t['base']
        res = sorted(res.items(), key=lambda l: l[0].sequence)
        res = [
            (r[0].name, r[1]['amount'], r[1]['base'], len(res)) for r in res]
        return res

    @api.multi
    def _compute_type_name(self):
        super()._compute_type_name()
        for sale in self:
            if not sale.is_return:
                return
            sale.type_name = _('Request') if sale.state in (
                'draft', 'sent', 'cancel') else _('Return Order')

    @api.multi
    def _compute_sale_order_return_count(self):
        for sale in self:
            returns = self.env['sale.order'].search([
                ('parent_sale_order', '=', sale.id),
                ('is_return', '=', True)
            ])
            sale.sale_order_return_count = len(returns)
