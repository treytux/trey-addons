###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    @http.route()
    def cart(self, access_token=None, revive='', **post):
        if request.website.is_public_user() and post.get('type') != 'popover':
            return request.redirect('/web/login?redirect=/shop/cart')
        return super().cart(
            access_token=access_token, revive=revive, **post)

    @http.route(auth='user')
    def extra_info(self, **post):
        return super().extra_info(**post)

    @http.route(auth='user')
    def checkout(self, **post):
        return super().checkout(**post)

    @http.route(auth='user')
    def address(self, **kw):
        return super().address(**kw)

    @http.route(auth='user')
    def payment(self, **post):
        return super().payment(**post)

    @http.route(auth='user')
    def payment_confirmation(self, **post):
        return super().payment_confirmation(**post)
