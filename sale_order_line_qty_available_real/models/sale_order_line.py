###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    qty_available_real = fields.Float(
        compute='_compute_qty_available_real',
        digits=dp.get_precision('Product Unit of Measure'),
        string='Real stock',
    )

    @api.one
    @api.depends('product_id', 'order_id.warehouse_id')
    def _compute_qty_available_real(self):
        product = self.product_id.with_context(
            warehouse=self.order_id.warehouse_id.id)
        self.qty_available_real = product.qty_available - product.outgoing_qty

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        res = super()._onchange_product_id_check_availability()
        if not self.product_id or not self.product_uom_qty:
            return res
        if self.product_id.type != 'product':
            return res
        if self._check_routing():
            return res
        res.pop('warning', None)
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        product_qty = self.product_uom._compute_quantity(
            self.product_uom_qty, self.product_id.uom_id)
        qty_compare = float_compare(
            self.qty_available_real, product_qty, precision_digits=precision)
        if qty_compare == -1:
            message = _(
                'You plan to sell %s %s but you only have %s %s available in '
                '%s warehouse.') % (
                    self.product_uom_qty, self.product_uom.name,
                    self.qty_available_real, self.product_uom.name,
                    self.order_id.warehouse_id.name)
            res['warning'] = {
                'title': _('Not enough inventory!'),
                'message': message}
        return res
