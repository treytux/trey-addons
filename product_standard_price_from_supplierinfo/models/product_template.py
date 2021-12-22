###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.depends(
        'seller_ids', 'seller_ids.sequence', 'seller_ids.price',
        'seller_ids.discount',
        'variant_seller_ids', 'variant_seller_ids.sequence',
        'variant_seller_ids.price', 'variant_seller_ids.discount')
    def _compute_standard_price(self):
        super()._compute_standard_price()
        for template in self:
            if len(template.product_variant_ids) > 1:
                template.standard_price = 0.
            elif template.seller_ids:
                template.standard_price = (
                    template.seller_ids.sorted('sequence')[0].price_get())
            elif template.variant_seller_ids:
                template.standard_price = (
                    template.variant_seller_ids.sorted('sequence')[0].price_get())
