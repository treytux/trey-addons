###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    @api.multi
    def action_transfer(self):
        context = self.env.context.copy()
        context['batch'] = self
        self.env.context = context
        return super().action_transfer()
