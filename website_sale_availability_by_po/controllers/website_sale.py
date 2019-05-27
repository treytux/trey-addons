###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.tools.misc import format_date


class WebsiteSale(WebsiteSale):
    def _product_availability_format_date(self, res):
        for item in res.values():
            item['date_planned'] = item['date_planned'] and format_date(
                request.env, item['date_planned']) or item['date_planned']
        return res

    @http.route(
        ['/shop/product_availability'], type='json', auth='public',
        methods=['POST'], website=True, csrf=False)
    def product_availability(self, product_ids, **post):
        products = request.env['product.product'].browse(product_ids)
        res = products.exists().sudo().get_availability()
        return self._product_availability_format_date(res)
