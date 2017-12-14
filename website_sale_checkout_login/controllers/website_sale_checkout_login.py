# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http
from openerp.http import request
import openerp.addons.website_sale.controllers.main as main
from openerp.addons.auth_oauth.controllers.main import OAuthLogin


class WebsiteSaleCheckoutLogin(http.Controller):
    @http.route(['/shop/login'], type='http', auth='public', website=True)
    def check_login(self, **post):
        oauth = OAuthLogin()
        require_term = request.website.request_accept_terms
        redirect = post.get('redirect', '/')
        if request.session.uid:
            return request.redirect('%s' % (redirect))
        return request.website.render(
            'website_sale_checkout_login.login',
            {'redirect': redirect,
             'request_accept_terms': require_term,
             'reset_password_enabled': True,
             'providers': oauth.list_providers()})


class WebsiteSale(main.website_sale):
    @http.route(['/shop/checkout'], type='http', auth='public', website=True)
    def checkout(self, **post):
        if not request.session.uid:
            return request.redirect('/shop/login?redirect=/shop/checkout')
        return super(WebsiteSale, self).checkout(**post)

    @http.route(['/shop/payment'], type='http', auth='public', website=True)
    def payment(self, **post):
        if not request.session.uid:
            return request.redirect('/shop/login?redirect=/shop/payment')
        return super(WebsiteSale, self).payment(**post)

    @http.route(['/shop/confirm_order'], type='http', auth='public',
                website=True)
    def confirm_order(self, **post):
        if not request.session.uid:
            return request.redirect('/shop/login?redirect=/shop/confirm_order')
        return super(WebsiteSale, self).confirm_order(**post)
