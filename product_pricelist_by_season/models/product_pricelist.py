###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def _get_applicable_rules_domain(self, products, date):
        res = super()._get_applicable_rules_domain(
            products, date)
        season_ids = products.mapped('season_id').ids
        if not season_ids:
            return res
        res += [
            '|',
            ('product_season_id', '=', False),
            ('product_season_id', 'in', season_ids),
        ]
        return res
