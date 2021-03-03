###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSaleB2BUsers(WebsiteSale):
    @http.route(auth='user')
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        return super().shop(
            page=page, category=category, search=search, ppg=ppg, **post)

    @http.route(auth='user')
    def product(self, product, category='', search='', **kwargs):
        return super().product(
            product, category=category, search=search, **kwargs)

    @http.route(auth='user')
    def pricelist_change(self, pl_id, **post):
        return super().pricelist_change(pl_id, **post)

    @http.route(auth='user')
    def pricelist(self, promo, **post):
        return super().pricelist(promo, **post)

    @http.route()
    def cart(self, access_token=None, revive='', **post):
        if request.website.is_public_user() and post.get('type') != 'popover':
            return request.redirect('/web/login?redirect=/shop/cart')
        return super().cart(
            access_token=access_token, revive=revive, **post)

    @http.route(auth='user')
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        return super().cart_update(
            product_id, add_qty=add_qty, set_qty=set_qty, **kw)

    @http.route(auth='user')
    def cart_update_json(
        self, product_id, line_id=None, add_qty=None, set_qty=None,
            display=True):
        return super().cart_update_json(
            product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty,
            display=display)

    @http.route(auth='user')
    def address(self, **kw):
        return super().address(**kw)

    @http.route(auth='user')
    def checkout(self, **post):
        return super().checkout(**post)

    @http.route(auth='user')
    def confirm_order(self, **post):
        return super().confirm_order(**post)

    @http.route(auth='user')
    def extra_info(self, **post):
        return super().extra_info(**post)

    @http.route(auth='user')
    def payment(self, **post):
        return super().payment(**post)

    @http.route(auth='user')
    def payment_transaction(
        self, acquirer_id, save_token=False, so_id=None, access_token=None,
            token=None, **kwargs):
        return super().payment_transaction(
            acquirer_id, save_token=save_token, so_id=so_id,
            access_token=access_token, token=token, **kwargs)

    @http.route(auth='user')
    def payment_token(self, pm_id=None, **kwargs):
        return super().payment_token(pm_id=pm_id, **kwargs)

    @http.route(auth='user')
    def payment_get_status(self, sale_order_id, **post):
        return super().payment_get_status(
            sale_order_id, **post)

    @http.route(auth='user')
    def payment_validate(
            self, transaction_id=None, sale_order_id=None, **post):
        return super().payment_validate(
            transaction_id=transaction_id, sale_order_id=sale_order_id, **post)

    @http.route(auth='user')
    def terms(self, **kw):
        return super().terms(**kw)

    @http.route(auth='user')
    def payment_confirmation(self, **post):
        return super().payment_confirmation(**post)

    @http.route(auth='user')
    def print_saleorder(self, **kwargs):
        return super().print_saleorder(**kwargs)

    @http.route(auth='user')
    def tracking_cart(self, **post):
        return super().tracking_cart(**post)

    @http.route(auth='user')
    def change_styles(self, id, style_id):
        return super().change_styles(id, style_id)

    @http.route(auth='user')
    def change_sequence(self, id, sequence):
        return super().change_sequence(id, sequence)

    @http.route(auth='user')
    def change_size(self, id, x, y):
        return super().change_size(id, x, y)

    @http.route(auth='user')
    def country_infos(self, country, mode, **kw):
        return super().country_infos(country, mode, **kw)

    @http.route(auth='user')
    def update_eshop_carrier(self, **post):
        return super().update_eshop_carrier(**post)

    @http.route(auth='user')
    def cart_options_update_json(
        self, product_id, add_qty=1, set_qty=0, goto_shop=None, lang=None,
            **kw):
        return super().cart_options_update_json(
            product_id, add_qty=add_qty, set_qty=set_qty, goto_shop=goto_shop,
            lang=lang, **kw)

    @http.route(auth='user')
    def create_product_variant(
        self, product_template_id, product_template_attribute_value_ids,
            **kwargs):
        return super().create_product_variant(
            product_template_id, product_template_attribute_value_ids,
            **kwargs)

    @http.route(auth='user')
    def show_optional_products_website(self, product_id, variant_values, **kw):
        return super().show_optional_products_website(
            product_id, variant_values, **kw)

    @http.route(auth='user')
    def optional_product_items_website(self, product_id, **kw):
        return super().optional_product_items_website(product_id, **kw)

    @http.route(auth='user')
    def get_combination_info_website(
            self, product_template_id, product_id, combination, add_qty, **kw):
        return super().get_combination_info_website(
            product_template_id, product_id, combination, add_qty, **kw)
