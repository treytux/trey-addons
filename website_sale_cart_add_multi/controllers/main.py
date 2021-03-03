# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import http
from openerp.http import request
from openerp.addons.website_sale.controllers.main import website_sale


class WebsiteSale(website_sale):
    @http.route(['/shop/cart/update_json_multi'],
                type='json', auth='public', methods=['post'], website=True)
    def cart_update_json_multi(self, products, display=True):
        data = {}
        order = request.website.sale_get_order(force_create=1)
        if order.state != 'draft':
            request.website.sale_reset()
            return data
        for p in products:
            data = order._cart_update(
                product_id=p[0],
                line_id=p[1],
                add_qty=p[2],
                set_qty=p[3],
            )
        if not order.cart_quantity:
            request.website.sale_reset()
            return data
        if not display:
            return data
        data['cart_quantity'] = order.cart_quantity
        data['website_sale.total'] = request.website._render(
            'website_sale.total', {
                'website_sale_order': request.website.sale_get_order()})
        return data
