##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    @http.route(['/shop/empty-cart'], type='http', auth='public', website=True)
    def empty_cart(self):
        order = request.website.sale_get_order()
        if order:
            order.order_line.unlink()
        return request.redirect('/shop/cart')
