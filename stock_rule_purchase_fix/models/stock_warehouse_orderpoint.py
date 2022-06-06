###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockWarehouseOrderPoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    def _quantity_in_progress(self):
        res = super()._quantity_in_progress()
        purchase_order_line_obj = self.env['purchase.order.line']
        for orderpoint in self:
            lines = purchase_order_line_obj.search([
                ('order_id.picking_type_id.default_location_dest_id',
                 '=', orderpoint.location_id.id),
                ('product_id', '=', orderpoint.product_id.id),
                ('state', 'in', ('draft', 'sent', 'to approve')),
            ])
            res[orderpoint.id] = sum(lines.mapped('product_uom_qty'))
        return res
