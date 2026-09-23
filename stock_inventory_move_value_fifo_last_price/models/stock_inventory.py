###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    def _action_done(self):
        return super(StockInventory, self.with_context(
            inventory_done=True))._action_done()
