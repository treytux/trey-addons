###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def product_inactive_orderpoint(self):
        for product in self:
            product.orderpoint_ids.unlink()
            product.active = False
