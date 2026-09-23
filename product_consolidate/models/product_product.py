###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def toogle_consolidate_products(self):
        for product in self:
            product.product_tmpl_id.toogle_consolidate_products()
        return True
