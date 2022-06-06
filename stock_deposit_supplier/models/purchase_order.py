###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_approve(self, force=False):
        res = super().button_approve()
        deposit_supplier_picking_type = self.env.ref(
            'stock_deposit_supplier.deposit_supplier_picking_type')
        for purchase in self:
            warehouse = purchase.picking_type_id.warehouse_id
            create_linked_picking = (
                len(purchase.picking_ids) == 1
                and purchase.picking_type_id == deposit_supplier_picking_type
                and purchase.picking_type_id.is_supplier_deposit)
            if create_linked_picking:
                picking = purchase.picking_ids
                new_picking = picking.copy({
                    'location_id': picking.location_dest_id.id,
                    'location_dest_id': warehouse.lot_stock_id.id,
                    'move_lines': [(6, 0, [])],
                })
                for move in picking.move_lines:
                    move.copy({
                        'picking_id': new_picking.id,
                        'location_id': picking.location_dest_id.id,
                        'location_dest_id': warehouse.lot_stock_id.id,
                        'move_orig_ids': [(4, move.id)],
                    })
                new_picking.action_confirm()
        return res
