##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _cal_move_weight(self):
        super()._cal_move_weight()
        default_weight_uom = self.env[
            'product.template']._get_weight_uom_id_from_ir_config_parameter()
        for move in self:
            from_uom = move.product_id.weight_uom_id or default_weight_uom
            to_uom = move.picking_id.weight_uom_id or default_weight_uom
            if from_uom == to_uom or not move.product_id.weight:
                continue
            qty = move.product_uom._compute_quantity(
                move.product_uom_qty, move.product_id.uom_id, round=False)
            unit_weight = from_uom._compute_quantity(
                move.product_id.weight, to_uom, round=False)
            move.weight = qty * unit_weight
