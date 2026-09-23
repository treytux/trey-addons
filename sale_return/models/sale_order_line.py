###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def _get_domain_location_id(self):
        return [
            '|',
            ('usage', '=', 'internal'),
            ('scrap_location', '=', True),
        ]

    is_return = fields.Boolean(
        related='order_id.is_return',
        string='Is Return',
    )
    qty_changed = fields.Float(
        compute='_compute_qty_to_invoice',
        compute_sudo=True,
        digits='Product Unit of Measure',
        string='Changed',
    )
    qty_change = fields.Float(
        digits='Product Unit of Measure',
        string='Change',
    )
    qty_changed_to_invoice = fields.Float(
        digits='Product Unit of Measure',
        compute='_compute_qty_to_invoice',
        compute_sudo=True,
        string='Change to invoice',
    )
    qty_changed_invoiced = fields.Float(
        digits='Product Unit of Measure',
        compute='_compute_invoice_qty',
        compute_sudo=True,
        string='Change invoiced',
    )
    qty_returned = fields.Float(
        digits='Product Unit of Measure',
        compute='_compute_qty_to_invoice',
        compute_sudo=True,
        string='Returned',
    )
    qty_returned_to_invoice = fields.Float(
        digits='Product Unit of Measure',
        compute='_compute_invoice_qty',
        compute_sudo=True,
        string='Returned to invoice',
    )
    qty_returned_invoiced = fields.Float(
        digits='Product Unit of Measure',
        compute='_compute_invoice_qty',
        compute_sudo=True,
        string='Invoiced',
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        domain=_get_domain_location_id,
        string='Location',
    )
    notes = fields.Text(
        string='Notes',
    )
    resolution = fields.Char(
        string='Resolution',
    )
    is_returnable = fields.Boolean(
        string='Is returnable',
        compute='_compute_is_returnable',
        compute_sudo=True,
    )
    returnable_date = fields.Datetime(
        string='Returnable date',
        compute='_compute_returnable_date',
        compute_sudo=True,
    )
    parent_sale_order_line = fields.Many2one(
        comodel_name='sale.order.line',
        string='Parent Sale Order line',
    )

    @api.model
    def _returnable_product_types(self):
        return ['product', 'consu']

    @api.depends('returnable_date', 'product_id.type')
    def _compute_is_returnable(self):
        for line in self:
            line.is_returnable = (
                line.returnable_date
                and line.returnable_date.date() >= fields.Date.today()
                and line.product_id.type in self._returnable_product_types()
            )

    @api.depends('order_id.date_order', 'product_id.returnable_days')
    def _compute_returnable_date(self):
        for line in self:
            if line.is_return or not line.order_id.date_order:
                continue
            line.returnable_date = (
                line.order_id.date_order + relativedelta(
                    days=line.product_id.returnable_days)
            )

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        if not all(self.mapped('is_return')):
            return super()._compute_amount()
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            qty = (line.product_uom_qty * -1) + line.qty_change
            taxes = line.tax_id.compute_all(
                price, line.order_id.currency_id, qty, product=line.product_id,
                partner=line.order_id.partner_shipping_id)
            tax_amount = sum(
                t.get('amount', 0.0) for t in taxes.get('taxes', []))
            line.update({
                'price_tax': qty and tax_amount or 0.,
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.depends(
        'qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state',
        'order_id.picking_ids', 'is_return', 'qty_change')
    def _compute_qty_to_invoice(self):
        super()._compute_qty_to_invoice()
        for line in self:
            line.qty_returned = 0
            line.qty_changed = 0
            line.qty_returned_to_invoice = 0
            line.qty_changed_to_invoice = 0
            if not line.is_return:
                continue
            if line.product_id.type == 'service':
                line.qty_returned = line.product_uom_qty
                line.qty_changed = line.qty_change
            else:
                line.qty_returned = sum([
                    m.quantity_done for m in line.move_ids
                    if m.is_return and m.state == 'done'])
                line.qty_changed = sum([
                    m.quantity_done for m in line.move_ids
                    if m.is_change and m.state == 'done'])
            line.qty_returned_to_invoice = max(
                line.qty_returned - line.qty_returned_invoiced, 0)
            line.qty_changed_to_invoice = max(
                line.qty_changed - line.qty_changed_invoiced, 0)
            line.qty_to_invoice = line.qty_returned_to_invoice

    @api.depends(
        'state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice',
        'qty_invoiced', 'qty_changed_invoiced', 'qty_returned_invoiced',
        'qty_change', 'qty_changed_to_invoice')
    def _compute_invoice_status(self):
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')

        def compare(a, b):
            return float_compare(a, b, precision_digits=precision)

        def is_to_invoice(line):
            return not float_is_zero(
                line.qty_to_invoice + line.qty_changed_to_invoice,
                precision_digits=precision)

        def is_upselling(line):
            return (
                line.state == 'sale'
                and line.product_id.invoice_policy == 'order'
                and compare(line.qty_delivered, line.product_uom_qty) == 1)

        def is_invoiced(line):
            return (
                compare(line.qty_changed_invoiced, line.qty_change) >= 0
                and compare(
                    line.qty_returned_invoiced, line.product_uom_qty) >= 0)

        super()._compute_invoice_status()
        for line in self:
            if not line.order_id.is_return:
                continue
            if is_to_invoice(line):
                line.invoice_status = 'to invoice'
            elif is_upselling(line):
                line.invoice_status = 'upselling'
            elif is_invoiced(line):
                line.invoice_status = 'invoiced'
            else:
                line.invoice_status = 'no'

    @api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity')
    def _compute_invoice_qty(self):
        def has_return(invoice_line):
            return any(
                [li for li in invoice_line.sale_line_ids if li.is_return])

        self.qty_invoiced = 0.0
        self.qty_returned_invoiced = 0.0
        self.qty_changed_invoiced = 0.0
        for line in self:
            invoice_lines = [
                li for li in line.invoice_lines if li.move_id.state != 'cancel']
            for invoice_line in invoice_lines:
                qty = invoice_line.product_uom_id._compute_quantity(
                    invoice_line.quantity, line.product_uom)
                if invoice_line.move_id.move_type == 'out_invoice':
                    if has_return(invoice_line):
                        if qty < 0:
                            line.qty_returned_invoiced += line.product_uom_qty
                            line.qty_changed_invoiced += line.qty_change
                        else:
                            line.qty_returned_invoiced -= line.product_uom_qty
                            line.qty_changed_invoiced -= line.qty_change
                    else:
                        line.qty_invoiced += qty
                elif invoice_line.move_id.move_type == 'out_refund':
                    if has_return(invoice_line):
                        if qty > 0:
                            line.qty_returned_invoiced += line.product_uom_qty
                            line.qty_changed_invoiced += line.qty_change
                        else:
                            line.qty_returned_invoiced -= line.product_uom_qty
                            line.qty_changed_invoiced -= line.qty_change
                    else:
                        line.qty_invoiced -= qty

    def _prepare_invoice_line(self, **optional_values):
        self.ensure_one()
        if not self.is_return:
            return super()._prepare_invoice_line(**optional_values)
        vals = super()._prepare_invoice_line(**optional_values)
        vals['quantity'] = -vals['quantity']
        if self.qty_changed_to_invoice:
            vals['quantity'] += self.qty_changed_to_invoice
        return vals

    @api.onchange('order_id', 'product_id')
    def _onchange_location_id(self):
        self.location_id = (
            self.is_return
            and self.order_id
            and self.order_id.warehouse_id.sale_return_default_location_id.id
            or self.order_id.warehouse_id.lot_stock_id.id or None
        )

    @api.onchange('qty_change')
    def _onchange_qty_change(self):
        if self.qty_change < 0:
            self.qty_change = 0
        elif self.qty_change > self.product_uom_qty:
            self.qty_change = self.product_uom_qty
            raise UserError(
                _('You can not change more units of returned, at most you '
                  'can return %s') % self.product_uom_qty)
