###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    @api.one
    @api.depends(
        'categ_id', 'product_tmpl_id', 'product_id', 'compute_price',
        'fixed_price', 'pricelist_id', 'percent_price', 'price_discount',
        'price_surcharge'
    )
    def _get_pricelist_item_name_price(self):
        super()._get_pricelist_item_name_price()
        if self.categ_id:
            self.name = _('Category: %s') % (self.categ_id.complete_name)
