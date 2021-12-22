###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _set_standard_price(self, value):
        super()._set_standard_price(value)
        PriceHistory = self.env['product.standard_price.history']
        company_id = self._context.get(
            'force_company', self.env.user.company_id.id)
        markets = self.env['crm.team'].search([('is_market', '=', True)])
        for product in self:
            for market in markets:
                PriceHistory.create({
                    'product_id': product.id,
                    'market_cost': market.price_cost_compute(product, value),
                    'standard_price': value,
                    'company_id': company_id,
                    'team_id': market.id,
                })
