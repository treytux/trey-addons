###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.depends(
        'seller_ids', 'seller_ids.sequence', 'seller_ids.price',
        'seller_ids.discount')
    def _compute_standard_price(self):
        super()._compute_standard_price()
        for template in self:
            if not template.seller_ids:
                continue
            if len(template.product_variant_ids) > 1:
                template.standard_price = 0.
            else:
                template.standard_price = (
                    template.seller_ids.sorted('sequence')[0].price_get())
