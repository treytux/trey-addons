###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_cancel(self):
        self = self.with_context(allow_sale_cancel=True)
        return super(StockPicking, self).action_cancel()
