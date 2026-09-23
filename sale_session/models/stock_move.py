###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_assign(self, force_qty=False):
        if self.env.context.get('force_stock'):
            force_qty = True
        return super()._action_assign(force_qty=force_qty)
