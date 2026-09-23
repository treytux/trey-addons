###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def _run_fifo(self, move, quantity=None):
        tmp_value = super()._run_fifo(move, quantity=quantity)
        moves = move.product_id.stock_move_ids.filtered(
            lambda m: m.remaining_qty > 0 and m.state == 'done')
        moves = moves.sorted('date')
        if moves:
            move.product_id.standard_price = moves[0].price_unit
        return tmp_value
