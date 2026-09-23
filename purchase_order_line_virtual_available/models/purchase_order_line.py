###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    virtual_available = fields.Float(
        compute='_compute_virtual_available',
        digits='Product Unit of Measure',
        string='Virtual available',
    )

    @api.depends('product_id', 'order_id.picking_type_id.warehouse_id')
    def _compute_virtual_available(self):
        for line in self:
            warehouse_id = line.order_id.picking_type_id.warehouse_id.id
            line.virtual_available = line.product_id.with_context(
                warehouse=warehouse_id).virtual_available
