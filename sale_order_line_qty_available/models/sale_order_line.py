###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    qty_available = fields.Float(
        compute='_compute_qty_available',
        digits=dp.get_precision('Product Unit of Measure'),
        string='Quantity On Hand')

    @api.depends('product_id', 'order_id.warehouse_id')
    def _compute_qty_available(self):
        for order in self:
            order.qty_available = order.product_id.with_context(
                warehouse=order.order_id.warehouse_id.id).qty_available
