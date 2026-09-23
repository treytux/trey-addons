###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _search_qty_available_real_website(self, operator, value):
        product_obj = self.env['product.product']
        ids = product_obj._search_qty_available_real_website(
            operator, value)[0][2]
        stock_product_products = product_obj.search_read([
            ('id', 'in', ids),
        ], ['product_tmpl_id'])
        return list(
            set([item['product_tmpl_id'][0] for item in stock_product_products]))
