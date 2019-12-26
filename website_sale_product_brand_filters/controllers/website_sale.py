###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    @http.route()
    def shop(
            self, page=0, category=None, brand=None, search='', ppg=False,
            **post):
        res = super().shop(
            page=page, category=category, brand=brand, search=search, ppg=ppg,
            **post)
        res.qcontext['brands'] = (
            search and
            res.qcontext['products'].mapped('product_brand_id') or
            request.env['product.brand'].search([]))
        return res
