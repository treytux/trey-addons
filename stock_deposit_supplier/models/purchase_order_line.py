###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _update_received_qty(self):
        res = super()._update_received_qty()
        deposit_supplier_picking_type = self.env.ref(
            'stock_deposit_supplier.deposit_supplier_picking_type')
        deposit_supplier_location = self.env.ref(
            'stock_deposit_supplier.deposit_supplier_location')
        for line in self:
            total = 0.0
            for move in line.move_ids:
                to_modify_total = (
                    move.product_id == line.product_id
                    and move.picking_type_id == deposit_supplier_picking_type
                    and move.state == 'done')
                if to_modify_total:
                    if move.location_id == deposit_supplier_location:
                        total += move.product_uom._compute_quantity(
                            move.product_uom_qty, line.product_uom)
                    if (
                        move.location_id.usage != 'supplier'
                        and move.location_dest_id == deposit_supplier_location
                    ):
                        total += move.product_uom._compute_quantity(
                            move.product_uom_qty, line.product_uom)
                    if (
                        move.location_id == deposit_supplier_location
                        and move.location_dest_id.usage == 'supplier'
                    ):
                        total -= move.product_uom._compute_quantity(
                            move.product_uom_qty, line.product_uom)
            line.qty_received -= total
        return res
