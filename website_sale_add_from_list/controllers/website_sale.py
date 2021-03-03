# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import json
from openerp import http, exceptions, _
from openerp.http import request
import openerp.addons.website_sale.controllers.main as website_sale


class WebsiteSale(website_sale.website_sale):
    def get_product_variants(self, product):
        currency_obj = request.env['res.currency']
        variants = []
        for v in product.product_variant_ids:
            values = [
                v.id,
                (
                    len(v.attribute_value_ids) == 0 and
                    v.name or
                    ' '.join(v.mapped('attribute_value_ids.name'))),
                v.qty_available,
                v.price,
            ]
            if request.website.pricelist_id.id != request.context['pricelist']:
                website_currency_id = request.website.currency_id.id
                currency_id = self.get_pricelist().currency_id.id
                price = currency_obj.compute(
                    website_currency_id, currency_id, v.lst_price)
                values.append(price)
            else:
                values.append(v.lst_price)
            values.append(v.price_extra)
            variants.append(values)
        return json.dumps(variants)

    def _compute_currency(self, price, from_currency, to_currency):
        return request.env['res.currency']._compute(
            from_currency, to_currency, price, context=request.context)

    @http.route(
        ['/shop/get_product_variants'], type='http', auth='public',
        website=True)
    def shop_get_product_variants(self, **post):
        product_id = post.get('product_id')
        if not product_id or not product_id.isdigit():
            raise exceptions.Warning(_('Product id value is mandatory.'))
        pricelist = self.get_pricelist()
        if not pricelist:
            raise exceptions.Warning(_('No pricelist found.'))
        product_tmpl = request.env['product.template'].with_context(
            pricelist=pricelist.id).sudo().browse(int(product_id))
        from_currency = request.env['product.price.type']._get_field_currency(
            'list_price', request.context)
        to_currency = pricelist.currency_id
        sale_order_id = request.session['sale_order_id']
        decimal_precision = request.env['decimal.precision'].precision_get(
            'Product Price')
        values = {
            'product_tmpl': product_tmpl,
            'from_currency': from_currency,
            'to_currency': to_currency,
            'compute_currency': self._compute_currency,
            'order_quantities': None,
            'decimal_precision': decimal_precision
        }
        if sale_order_id:
            sale_order_obj = request.env['sale.order']
            order = sale_order_obj.browse(sale_order_id)
            order_quantities = sale_order_obj.get_product_quantities(order)
            values['order_quantities'] = order_quantities
        return request.website.render(
            'website_sale_add_from_list.product_variants', values)
