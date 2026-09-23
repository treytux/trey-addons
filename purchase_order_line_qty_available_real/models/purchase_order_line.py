###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    qty_available_real = fields.Float(
        string='Real stock',
        compute='_compute_qty_available_real',
        digits=dp.get_precision('Product Unit of Measure'),
    )

    @api.depends('product_id', 'order_id.picking_type_id')
    def _compute_qty_available_real(self):
        for line in self:
            line_wh = line.order_id.picking_type_id.warehouse_id
            if not line_wh:
                line.qty_available_real = 0
                continue
            product = line.product_id.with_context(warehouse=line_wh.id)
            line.qty_available_real = (
                product.qty_available - product.outgoing_qty)
