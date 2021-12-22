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
        for product in self:
            PriceHistory.create({
                'company_id': company_id,
                'product_id': product.id,
                'standard_price': value,
            })

    def action_open_standard_price_history(self):
        action = self.env.ref(
            'product_standard_price_history'
            '.product_standard_price_history_action').read()[0]
        action['context'] = {
            'search_default_product_id': self.ids,
        }
        return action
