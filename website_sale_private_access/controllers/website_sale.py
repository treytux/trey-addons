###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSalePrivateAccess(WebsiteSale):
    @http.route()
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().shop(
            page=page, category=category, search=search, ppg=ppg, **post)

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().product(
            product, category=category, search=search, **kwargs)

    @http.route()
    def pricelist_change(self, pl_id, **post):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().pricelist_change(pl_id, **post)

    @http.route()
    def pricelist(self, promo, **post):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().pricelist(promo, **post)

    @http.route()
    def cart(self, access_token=None, revive='', **post):
        website = request.website
        if (
                website.is_public_user() and website.get_is_private_shop()
                and post.get('type') != 'popover'):
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().cart(
            access_token=access_token, revive=revive, **post)

    @http.route()
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().cart_update(
            product_id, add_qty=add_qty, set_qty=set_qty, **kw)

    @http.route()
    def cart_update_json(
        self, product_id, line_id=None, add_qty=None, set_qty=None,
            display=True):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().cart_update_json(
            product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty,
            display=display)

    @http.route()
    def address(self, **kw):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().address(**kw)

    @http.route()
    def checkout(self, **post):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().checkout(**post)

    @http.route()
    def confirm_order(self, **post):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().confirm_order(**post)

    @http.route()
    def extra_info(self, **post):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().extra_info(**post)

    @http.route()
    def payment(self, **post):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().payment(**post)

    @http.route()
    def payment_transaction(
        self, acquirer_id, save_token=False, so_id=None, access_token=None,
            token=None, **kwargs):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().payment_transaction(
            acquirer_id, save_token=save_token, so_id=so_id,
            access_token=access_token, token=token, **kwargs)

    @http.route()
    def payment_token(self, pm_id=None, **kwargs):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().payment_token(pm_id=pm_id, **kwargs)

    @http.route()
    def payment_get_status(self, sale_order_id, **post):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().payment_get_status(
            sale_order_id, **post)

    @http.route()
    def payment_validate(
            self, transaction_id=None, sale_order_id=None, **post):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().payment_validate(
            transaction_id=transaction_id, sale_order_id=sale_order_id, **post)

    @http.route()
    def terms(self, **kw):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().terms(**kw)

    @http.route()
    def payment_confirmation(self, **post):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().payment_confirmation(**post)

    @http.route()
    def print_saleorder(self, **kwargs):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().print_saleorder(**kwargs)

    @http.route()
    def tracking_cart(self, **post):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().tracking_cart(**post)

    @http.route()
    def change_styles(self, id, style_id):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().change_styles(id, style_id)

    @http.route()
    def change_sequence(self, id, sequence):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().change_sequence(id, sequence)

    @http.route()
    def change_size(self, id, x, y):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().change_size(id, x, y)

    @http.route()
    def country_infos(self, country, mode, **kw):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().country_infos(country, mode, **kw)

    @http.route()
    def update_eshop_carrier(self, **post):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().update_eshop_carrier(**post)

    @http.route()
    def cart_options_update_json(
        self, product_id, add_qty=1, set_qty=0, goto_shop=None, lang=None,
            **kw):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().cart_options_update_json(
            product_id, add_qty=add_qty, set_qty=set_qty, goto_shop=goto_shop,
            lang=lang, **kw)

    @http.route()
    def create_product_variant(
        self, product_template_id, product_template_attribute_value_ids,
            **kwargs):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().create_product_variant(
            product_template_id, product_template_attribute_value_ids,
            **kwargs)

    @http.route()
    def show_optional_products_website(self, product_id, variant_values, **kw):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().show_optional_products_website(
            product_id, variant_values, **kw)

    @http.route()
    def optional_product_items_website(self, product_id, **kw):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().optional_product_items_website(product_id, **kw)

    @http.route()
    def get_combination_info_website(
            self, product_template_id, product_id, combination, add_qty, **kw):
        website = request.website
        if website.is_public_user() and website.get_is_private_shop():
            full_path = request.httprequest.full_path
            return request.redirect(
                '/web/login?redirect=%s' % (full_path or '/shop'))
        return super().get_combination_info_website(
            product_template_id, product_id, combination, add_qty, **kw)
