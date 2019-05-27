###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
try:
    from odoo.addons.website_sale_product_brand.controllers.main import (
        WebsiteSale)
except ImportError:
    WebsiteSale = http.Controller


class WebsiteSaleB2B(WebsiteSale):

    @http.route(auth='user')
    def product_brands(self, **post):
        return super(WebsiteSaleB2B, self).product_brands(**post)
