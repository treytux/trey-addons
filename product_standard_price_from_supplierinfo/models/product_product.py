###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        res = super().create(vals)
        for product in res:
            if product.product_tmpl_id.product_variant_count == 1:
                continue
            product.standard_price = (
                product.product_tmpl_id.product_variant_ids[0].standard_price)
        return res
