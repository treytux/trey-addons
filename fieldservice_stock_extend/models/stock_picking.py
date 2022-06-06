###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _create_backorder(self):
        backorders = super()._create_backorder()
        for picking in self:
            if not picking.fsm_order_id:
                continue
            picking_backorders = backorders.filtered(
                lambda b: b.backorder_id == picking.id)
            picking_backorders.write({
                'fsm_order_id': picking.fsm_order_id.id,
            })
        return backorders
