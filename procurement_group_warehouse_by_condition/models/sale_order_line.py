###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order.line'

    @api.depends(
        'product_type', 'product_uom_qty', 'qty_delivered', 'state',
        'move_ids', 'product_uom')
    def _compute_qty_to_deliver(self):
        super()._compute_qty_to_deliver()
        for line in self:
            if line.order_id.warehouse_id.is_warehouse_by_condition:
                line.display_qty_widget = False
