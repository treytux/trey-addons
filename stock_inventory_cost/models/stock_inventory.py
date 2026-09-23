# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import models, fields, api


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    cost = fields.Float(
        string='Cost',
        compute='_compute_cost',
    )

    @api.depends('move_ids')
    def _compute_cost(self):
        for inventory in self:
            inventory_loss_loc = self.env.ref('stock.location_inventory')
            total_cost = 0
            for move in inventory.move_ids:
                if move.location_id == inventory_loss_loc:
                    sign = 1
                elif move.location_dest_id == inventory_loss_loc:
                    sign = - 1
                cost_price = move.product_id.standard_price
                move_qty = self.env['product.uom']._compute_qty(
                    move.product_uom.id,
                    move.product_uom_qty,
                    move.product_id.uom_po_id.id)
                total_cost += sign * move_qty * cost_price
            inventory.cost = total_cost
