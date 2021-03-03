###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def _add_delivery_cost_to_so(self):
        self.ensure_one()
        if self.sale_id and self.sale_id.delivery_cost_to_sale_order:
            return super()._add_delivery_cost_to_so()
        return
