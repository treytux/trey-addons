# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http, fields
from openerp.http import request
try:
    from openerp.addons.website_myaccount.controllers.main import MyAccount
except ImportError:
    MyAccount = object


class MyAccountSaleCart(MyAccount):
    cart_scope = 'latest'
    cart_year = None
    cart_year_or_cart_scope = 'cart_scope'
    cart_states = ['draft']

    def _restart_cart_fields(self):
        self.cart_scope = 'latest'
        self.cart_year = None
        self.cart_year_or_cart_scope = 'cart_scope'

    def _prepare_cart_orders(self, saleorder_id=None, limit=None):
        env = request.env
        domain = [
            '|',
            ('partner_id', 'in', self._get_partner_ids()),
            ('message_follower_ids', 'in', self._get_follower_ids()),
            ('is_cart', '=', True)]
        if saleorder_id:
            domain.append(('id', '=', saleorder_id))
        sale_carts = env['sale.order'].sudo().search(domain, limit=limit)
        return sale_carts

    def _render_carts(self, sales, cart_year, cart_year_to,
                      cart_year_from, cart_scope):
            return request.website.render(
                'website_myaccount_sale_cart.carts', {
                    'carts': sales,
                    'cart_year': cart_year,
                    'cart_year_to': cart_year_to,
                    'cart_year_from': cart_year_from,
                    'cart_scope': cart_scope})

    @http.route([
        '/my/carts',
    ], type='http', auth='user', website=True)
    def carts(self, **post):
        sales = self._prepare_cart_orders()
        cart_year_to = fields.Datetime.from_string(
            fields.Datetime.now()).year
        cart_year_from = cart_year_to
        if not post or not sales:
            self._restart_cart_fields()
            return self._render_carts(
                sales, self.cart_year if self.cart_year else cart_year_to,
                cart_year_to, cart_year_from,
                self.cart_scope)
        if sales and sales[-1].date_order:
            cart_year_from = fields.Datetime.from_string(
                sales[-1].date_order).year
        cart_scope = post.get('cart_scope') if post.get('cart_scope') else None
        cart_year = post.get('cart_year') if post.get('cart_year') else None
        if cart_scope and not cart_year:
            self.cart_scope = cart_scope
            self.cart_year_or_cart_scope = 'cart_scope'
        if cart_year and not cart_scope:
            self.cart_year = cart_year
            self.cart_year_or_cart_scope = 'cart_year'
        if (not cart_year and not cart_scope and
                self.cart_year_or_cart_scope == 'cart_year'):
            cart_scope = None
            cart_year = self.cart_year
        if (not cart_year and not cart_scope and
                self.cart_year_or_cart_scope == 'cart_scope'):
            cart_year = None
            cart_scope = self.cart_scope
        domain = [('id', 'in', sales.ids)]
        limit = None
        if cart_scope == 'latest':
            limit = 20
        if cart_scope == 'all':
            limit = None
        if cart_year:
            cart_scope = 'no_cart_scope'
            date_from = '%s-01-01 00:00:00' % (cart_year)
            date_to = '%s-12-31 23:59:59' % (cart_year)
            domain.extend([
                ('date_order', '>=', date_from),
                ('date_order', '<=', date_to)])
        sales = request.env['sale.order'].sudo().search(
            domain, limit=limit, order='id DESC')
        return self._render_carts(
            sales, cart_year if cart_year else cart_year_to,
            cart_year_to, cart_year_from, cart_scope)

    @http.route([
        '/my/carts/recover/<int:cart_id>',
    ], type='http', auth='user', website=True)
    def recover_cart(self, cart_id, **post):
        if not cart_id:
            return self.carts(**post)
        sale_carts = self._prepare_cart_orders(saleorder_id=cart_id)
        if not sale_carts:
            return self.carts(**post)
        request.session['sale_order_id'] = cart_id
        return request.redirect('/shop/cart')
