###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_open_standard_price_history(self):
        self.ensure_one()
        action = self.env.ref(
            'product_standard_price_history'
            '.product_standard_price_history_action').read()[0]
        action['context'] = {
            'search_default_product_id': self.product_variant_ids.ids,
        }
        return action
