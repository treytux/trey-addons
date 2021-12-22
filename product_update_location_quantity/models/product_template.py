###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class Product(models.Model):
    _inherit = 'product.template'

    def action_change_quantity_on_hand(self):
        default_product_id = self.env.context.get(
            'default_product_id', self.product_variant_id.id)
        product = self.env['product.product'].browse(default_product_id)
        return product.action_change_quantity_on_hand()
