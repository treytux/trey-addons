# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http, exceptions, _
from openerp.http import request
import openerp.addons.website_sale.controllers.main as website_sale


class WebsiteSale(website_sale.website_sale):

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        res = super(WebsiteSale, self).product(
            product=product, category='', search='', **kwargs)
        pricelist = self.get_pricelist()
        if not pricelist:
            raise exceptions.Warning(_('No pricelist found.'))
        res.qcontext['to_currency'] = pricelist.currency_id
        from_currency = request.env['product.price.type']._get_field_currency(
            'list_price', request.context)
        res.qcontext['from_currency'] = from_currency
        sale_order_id = request.session['sale_order_id']
        decimal_precision = request.env['decimal.precision'].precision_get(
            'Product Price')
        res.qcontext['decimal_precision'] = decimal_precision
        if sale_order_id:
            sale_order_obj = request.env['sale.order']
            order = sale_order_obj.browse(sale_order_id)
            order_quantities = sale_order_obj.get_product_quantities(order)
            res.qcontext['order_quantities'] = order_quantities
        return res
