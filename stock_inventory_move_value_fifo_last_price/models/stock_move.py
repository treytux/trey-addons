###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _run_valuation(self, quantity=None):
        res = super()._run_valuation(quantity=quantity)
        if 'inventory_done' not in self._context:
            return res
        if self.product_id.cost_method != 'fifo':
            return res
        if len(self.move_line_ids) != 1:
            return res
        in_move_lines = self.move_line_ids.search([
            ('product_id', '=', self.move_line_ids.product_id.id),
            ('lot_id', '=', self.move_line_ids.lot_id.id),
            ('date', '<', self.move_line_ids.date),
        ], order='id desc')
        price_unit = 0
        for in_move_line in in_move_lines:
            if in_move_line.move_id._is_in():
                price_unit = in_move_line.move_id.price_unit
                break
        else:
            price_unit = self.product_id.standard_price
        self.write({
            'price_unit': price_unit,
            'value': price_unit * self.product_uom_qty,
            'remaining_value': price_unit * self.remaining_qty,
        })
        return self.value
