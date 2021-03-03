###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_return = fields.Boolean(
        related='order_id.is_return',
        string='Is Return',
    )
    qty_changed = fields.Float(
        compute='_get_to_invoice_qty',
        digits=dp.get_precision('Product Unit of Measure'),
        string='Changed',
    )
    qty_change = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'),
        string='Change',
    )
    qty_changed_to_invoice = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'),
        compute='_get_to_invoice_qty',
        string='Change to invoice',
    )
    qty_changed_invoiced = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'),
        compute='_get_invoice_qty',
        string='Change invoiced',
    )
    qty_returned = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'),
        compute='_get_to_invoice_qty',
        string='Returned',
    )
    qty_returned_to_invoice = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'),
        compute='_get_invoice_qty',
        string='Returned to invoice',
    )
    qty_returned_invoiced = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'),
        compute='_get_invoice_qty',
        string='Invoiced',
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        domain='[("usage", "=", "internal")]',
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
    )
    returnable_date = fields.Datetime(
        string='Returnable date',
        compute='_compute_returnable_date',
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

    @api.depends('order_id.confirmation_date', 'product_id.returnable_days')
    def _compute_returnable_date(self):
        for line in self:
            if line.is_return or not line.order_id.confirmation_date:
                continue
            line.returnable_date = (
                line.order_id.confirmation_date + relativedelta(
                    days=line.product_id.returnable_days)
            )

    @api.one
    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        if not self.is_return:
            return super()._compute_amount()
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        qty = (self.product_uom_qty * -1) + self.qty_change
        taxes = self.tax_id.compute_all(
            price, self.order_id.currency_id, qty, product=self.product_id,
            partner=self.order_id.partner_shipping_id)
        tax_amount = sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
        self.update({
            'price_tax': qty and tax_amount or 0.,
            'price_total': taxes['total_included'],
            'price_subtotal': taxes['total_excluded']})

    @api.one
    @api.depends(
        'qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state',
        'order_id.picking_ids', 'is_return', 'qty_change')
    def _get_to_invoice_qty(self):
        super()._get_to_invoice_qty()
        self.qty_returned = 0
        self.qty_changed = 0
        self.qty_returned_to_invoice = 0
        self.qty_changed_to_invoice = 0
        if not self.is_return:
            return
        if self.product_id.type == 'service':
            self.qty_returned = self.product_uom_qty
            self.qty_changed = self.qty_change
        else:
            self.qty_returned = sum([
                m.quantity_done for m in self.move_ids
                if m.is_return and m.state == 'done'])
            self.qty_changed = sum([
                m.quantity_done for m in self.move_ids
                if m.is_change and m.state == 'done'])
        self.qty_returned_to_invoice = max(
            self.qty_returned - self.qty_returned_invoiced, 0)
        self.qty_changed_to_invoice = max(
            self.qty_changed - self.qty_changed_invoiced, 0)
        self.qty_to_invoice = self.qty_returned_to_invoice

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

    @api.one
    @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.quantity')
    def _get_invoice_qty(self):
        def has_return(invoice_line):
            return any(
                [li for li in invoice_line.sale_line_ids if li.is_return])

        self.qty_invoiced = 0.0
        self.qty_returned_invoiced = 0.0
        self.qty_changed_invoiced = 0.0
        invoice_lines = [
            li for li in self.invoice_lines if li.invoice_id.state != 'cancel']
        for invoice_line in invoice_lines:
            qty = invoice_line.uom_id._compute_quantity(
                invoice_line.quantity, self.product_uom)
            if invoice_line.invoice_id.type == 'out_invoice':
                if has_return(invoice_line):
                    if qty < 0:
                        self.qty_returned_invoiced -= qty
                    else:
                        self.qty_changed_invoiced += qty
                else:
                    self.qty_invoiced += qty
            elif invoice_line.invoice_id.type == 'out_refund':
                if has_return(invoice_line):
                    if qty > 0:
                        self.qty_returned_invoiced += qty
                    else:
                        self.qty_changed_invoiced -= qty
                else:
                    self.qty_invoiced -= qty

    def invoice_line_create_vals(self, invoice_id, qty):
        self.ensure_one()
        if not self.is_return:
            return super().invoice_line_create_vals(invoice_id, qty)
        lines = super().invoice_line_create_vals(invoice_id, qty * -1)
        if self.qty_changed_to_invoice:
            lines += super().invoice_line_create_vals(
                invoice_id, self.qty_changed_to_invoice)
        return lines

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        if self.is_return:
            return {}
        return super()._onchange_product_id_check_availability()

    @api.onchange('order_id', 'product_id')
    def _onchange_location_id(self):
        self.location_id = (
            self.order_id
            and self.order_id.warehouse_id.lot_stock_id.id
            or None
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
