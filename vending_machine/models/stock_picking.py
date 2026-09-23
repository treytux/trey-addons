###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_done(self):
        res = super().action_done()
        if self.sale_id.machine_ids and not self.sale_id.is_sale_deposit:
            machine = self.sale_id.machine_ids[0]
            machine.update_machine_stock_with_move_lines(self.move_lines)
        return res
