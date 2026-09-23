###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _run_valuation(self, quantity=None):
        self.move_line_ids.create_move_line_relation()
        return super()._run_valuation(quantity=quantity)
