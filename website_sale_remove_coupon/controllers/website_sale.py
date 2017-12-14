# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http
import openerp.addons.website_sale.controllers.main as main
from openerp.addons.web.http import request


class WebsiteSale(main.website_sale):
    @http.route(
        ['/shop/default-pricelist'], type='http', auth='public', website=True)
    def default_pricelist(self, **post):
        sale_order = request.website.sale_get_order()
        if not sale_order:
            return request.redirect('/shop/cart')
        pricelist_id = sale_order.partner_id.property_product_pricelist.id
        request.session['sale_order_code_pricelist_id'] = pricelist_id
        values = {'pricelist_id': pricelist_id}
        values.update(
            sale_order.onchange_pricelist_id(pricelist_id, None)['value'])
        sale_order.write(values)
        for line in sale_order.order_line:
            if line.exists():
                sale_order._cart_update(
                    product_id=line.product_id.id, line_id=line.id, add_qty=0)
        return request.redirect('/shop/cart')
