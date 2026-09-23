###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _compute_quantities_dict(
            self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        res = super()._compute_quantities_dict(
            lot_id, owner_id, package_id, from_date, to_date)
        mode = self.env.context.get('website_sale_stock_qty_mode')
        if mode == 'real':
            for product in self.with_context(
                    website_sale_stock_qty_mode=False):
                res[product.id]['free_qty'] = product.qty_available_real
                res[product.id]['virtual_available'] = (
                    product.qty_available_real)
        elif mode == 'forecasted':
            for product in self:
                res[product.id]['free_qty'] = (
                    res[product.id]['virtual_available'])
        return res
