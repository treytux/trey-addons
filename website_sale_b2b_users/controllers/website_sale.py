# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import http
from openerp.addons.website_sale.controllers.main import website_sale


class WebsiteSale(website_sale):
    @http.route(auth='user')
    def shop(self, page=0, category=None, search='', **post):
        return super(WebsiteSale, self).shop(
            page=page, category=category, search=search, **post)

    @http.route(auth='user')
    def product(self, product, category='', search='', **kwargs):
        return super(WebsiteSale, self).product(
            product=product, category=category, search=search, **kwargs)

    @http.route(auth='user')
    def product_comment(self, product_template_id, **post):
        return super(WebsiteSale, self).product_comment(
            product_template_id=product_template_id, **post)

    @http.route(auth='user')
    def pricelist(self, promo, **post):
        return super(WebsiteSale, self).pricelist(promo=promo, **post)

    @http.route(auth='user')
    def cart(self, **post):
        return super(WebsiteSale, self).cart(**post)

    @http.route(auth='user')
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        return super(WebsiteSale, self).cart_update(
            product_id=product_id, add_qty=add_qty, set_qty=set_qty, **kw)

    @http.route(auth='user')
    def cart_update_json(self, product_id, line_id, add_qty=None,
                         set_qty=None, display=True):
        return super(WebsiteSale, self).cart_update_json(
            product_id=product_id, line_id=line_id, add_qty=add_qty,
            set_qty=set_qty, display=display)

    @http.route(auth='user')
    def checkout(self, **post):
        return super(WebsiteSale, self).checkout(**post)

    @http.route(auth='user')
    def confirm_order(self, **post):
        return super(WebsiteSale, self).confirm_order(**post)

    @http.route(auth='user')
    def payment(self, **post):
        return super(WebsiteSale, self).payment(**post)

    @http.route(auth='user')
    def payment_transaction(self, acquirer_id):
        return super(WebsiteSale, self).payment_transaction(
            acquirer_id=acquirer_id)

    @http.route(auth='user')
    def payment_get_status(self, sale_order_id, **post):
        return super(WebsiteSale, self).payment_get_status(
            sale_order_id=sale_order_id, **post)

    @http.route(auth='user')
    def payment_validate(self, transaction_id=None, sale_order_id=None,
                         **post):
        return super(WebsiteSale, self).payment_validate(
            transaction_id=transaction_id, sale_order_id=sale_order_id, **post)

    @http.route(auth='user')
    def payment_confirmation(self, **post):
        return super(WebsiteSale, self).payment_confirmation(**post)

    @http.route(auth='user')
    def change_styles(self, id, style_id):
        return super(WebsiteSale, self).change_styles(
            id=id, style_id=style_id)

    @http.route(auth='user')
    def change_sequence(self, id, sequence):
        return super(WebsiteSale, self).change_sequence(
            id=id, sequence=sequence)

    @http.route(auth='user')
    def change_size(self, id, x, y):
        return super(WebsiteSale, self).change_size(id=id, x=x, y=y)

    @http.route(auth='user')
    def tracking_cart(self, **post):
        return super(WebsiteSale, self).tracking_cart(**post)

    @http.route(auth='user')
    def get_unit_price(self, product_ids, add_qty, use_order_pricelist=False,
                       **kw):
        return super(WebsiteSale, self).get_unit_price(
            product_ids=product_ids, add_qty=add_qty,
            use_order_pricelist=use_order_pricelist, **kw)
