###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleB2B(WebsiteSale):
    @http.route(auth='user')
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        return super(WebsiteSaleB2B, self).shop(
            page=page, category=category, search=search, ppg=ppg, **post)

    @http.route(auth='user')
    def product(self, product, category='', search='', **kwargs):
        return super(WebsiteSaleB2B, self).product(
            product, category=category, search=search, **kwargs)

    @http.route(auth='user')
    def pricelist_change(self, pl_id, **post):
        return super(WebsiteSaleB2B, self).pricelist_change(pl_id, **post)

    @http.route(auth='user')
    def pricelist(self, promo, **post):
        return super(WebsiteSaleB2B, self).pricelist(promo, **post)

    @http.route(auth='user')
    def cart(self, access_token=None, revive='', **post):
        return super(WebsiteSaleB2B, self).cart(
            access_token=access_token, revive=revive, **post)

    @http.route(auth='user')
    def cart_update_json(
        self, product_id, line_id=None, add_qty=None, set_qty=None,
            display=True):
        return super(WebsiteSaleB2B, self).cart_update_json(
            product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty,
            display=display)

    @http.route(auth='user')
    def address(self, **kw):
        return super(WebsiteSaleB2B, self).address(**kw)

    @http.route(auth='user')
    def checkout(self, **post):
        return super(WebsiteSaleB2B, self).checkout(**post)

    @http.route(auth='user')
    def confirm_order(self, **post):
        return super(WebsiteSaleB2B, self).confirm_order(**post)

    @http.route(auth='user')
    def extra_info(self, **post):
        return super(WebsiteSaleB2B, self).extra_info(**post)

    @http.route(auth='user')
    def payment(self, **post):
        return super(WebsiteSaleB2B, self).payment(**post)

    @http.route(auth='user')
    def payment_transaction(
        self, acquirer_id, save_token=False, so_id=None, access_token=None,
            token=None, **kwargs):
        return super(WebsiteSaleB2B, self).payment_transaction(
            acquirer_id, save_token=save_token, so_id=so_id,
            access_token=access_token, token=token, **kwargs)

    @http.route(auth='user')
    def payment_token(self, pm_id=None, **kwargs):
        return super(WebsiteSaleB2B, self).payment_token(pm_id=pm_id, **kwargs)

    @http.route(auth='user')
    def payment_get_status(self, sale_order_id, **post):
        return super(WebsiteSaleB2B, self).payment_get_status(
            sale_order_id, **post)

    @http.route(auth='user')
    def payment_validate(
            self, transaction_id=None, sale_order_id=None, **post):
        return super(WebsiteSaleB2B, self).payment_validate(
            transaction_id=transaction_id, sale_order_id=sale_order_id, **post)

    @http.route(auth='user')
    def terms(self, **kw):
        return super(WebsiteSaleB2B, self).terms(**kw)

    @http.route(auth='user')
    def payment_confirmation(self, **post):
        return super(WebsiteSaleB2B, self).payment_confirmation(**post)

    @http.route(auth='user')
    def print_saleorder(self):
        return super(WebsiteSaleB2B, self).print_saleorder()

    @http.route(auth='user')
    def tracking_cart(self, **post):
        return super(WebsiteSaleB2B, self).tracking_cart(**post)

    @http.route(auth='user')
    def get_unit_price(self, product_ids, add_qty, **kw):
        return super(WebsiteSaleB2B, self).get_unit_price(
            product_ids, add_qty, **kw)

    @http.route(auth='user')
    def change_styles(self, id, style_id):
        return super(WebsiteSaleB2B, self).change_styles(id, style_id)

    @http.route(auth='user')
    def change_sequence(self, id, sequence):
        return super(WebsiteSaleB2B, self).change_sequence(id, sequence)

    @http.route(auth='user')
    def change_size(self, id, x, y):
        return super(WebsiteSaleB2B, self).change_size(id, x, y)

    @http.route(auth='user')
    def country_infos(self, country, mode, **kw):
        return super(WebsiteSaleB2B, self).country_infos(country, mode, **kw)
