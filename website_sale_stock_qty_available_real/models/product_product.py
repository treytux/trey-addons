###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class Product(models.Model):
    _inherit = 'product.product'

    def _compute_quantities_dict(
            self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        res = super()._compute_quantities_dict(
            lot_id, owner_id, package_id, from_date, to_date)
        if self.env.context.get('website_sale_stock_available'):
            for product in self.with_context(
                    website_sale_stock_available=False):
                res[product.id]['virtual_available'] = (
                    product.qty_available_real)
        return res
