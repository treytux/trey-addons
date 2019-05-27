###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def _add_delivery_cost_to_so(self):
        self.ensure_one()
        if self.carrier_id.auto_shipping_cost:
            super()._add_delivery_cost_to_so()
