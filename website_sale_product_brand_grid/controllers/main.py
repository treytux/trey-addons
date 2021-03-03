###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    @http.route()
    def shop(
            self, page=0, category=None, brand=None, search='', ppg=False,
            **post):
        res = super(WebsiteSale, self).shop(
            page=page, category=category, brand=brand, search=search, ppg=ppg,
            **post)
        path_info = request.httprequest.environ['PATH_INFO']
        if not brand or path_info != '/shop/brands':
            return res
        brand = request.env['product.brand'].browse(int(brand))
        if (not brand.main_attribute_id or not brand.sell_by_grid):
            return res
        main_attr = brand.main_attribute_id
        product_tmpls = request.env['product.template'].search([
            ('attribute_line_ids', 'in', main_attr.attribute_line_ids.ids),
            ('product_brand_id', '=', brand.id),
            ('website_published', '=', True)])
        grid_data = self._fill_grid(product_tmpls, main_attr)
        res.qcontext['grid_data'] = grid_data
        res.qcontext['main_attr_values'] = self._get_main_attr_value_ids(
            grid_data, brand.main_attribute_id.value_ids)
        res.qcontext['main_attribute_id'] = brand.main_attribute_id
        res.qcontext['grid'] = brand
        res.qcontext['cart_quantities'] = self._get_cart_quantities()
        return request.render(
            'website_sale_product_grid.products_grid', res.qcontext)
