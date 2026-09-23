###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    location_name = fields.Char(
        related='location_id.name',
        store=True,
        readonly=False,
    )

    @api.model
    def _get_removal_strategy_order(self, removal_strategy):
        if removal_strategy == 'location':
            return 'location_name, in_date ASC NULLS FIRST, id'
        return super()._get_removal_strategy_order(removal_strategy)
