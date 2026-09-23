###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    @api.multi
    def _apply_formula(self, rule, product, price, price_uom):
        if rule.compute_price != 'margin':
            return super()._apply_formula(rule, product, price, price_uom)
        cost = product.standard_price
        return cost / (1 - rule.percent_margin / 100)
