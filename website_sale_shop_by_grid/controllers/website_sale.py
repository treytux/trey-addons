# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http
import openerp.addons.website_sale.controllers.main as main
from openerp.addons.web.http import request


class WebsiteSale(main.website_sale):
    @http.route(['/shop/cart/update_json_multi'],
                type='json', auth='public', methods=['post'], website=True)
    def cart_update_json_multi(self, product_id, line_id, add_qty=None,
                               set_qty=None, display=True):
        order = request.website.sale_get_order(force_create=1)
        if order.state != 'draft':
            request.website.sale_reset()
            return {}
        values = []
        for k, v in enumerate(product_id):
            value = order._cart_update(
                product_id=product_id[k],
                line_id=line_id[k] if line_id else None,
                add_qty=add_qty[k] if add_qty else None,
                set_qty=set_qty[k] if set_qty else None)
            if not order.cart_quantity:
                request.website.sale_reset()
                return []
            if not display:
                return None
            value['cart_quantity'] = order.cart_quantity
            value['website_sale.total'] = request.website._render(
                'website_sale.total', {
                    'website_sale_order': request.website.sale_get_order()})
        return values

    def limit_stock(self):
        return request.env['sale.config.settings'].sudo().search(
            [], order='id desc', limit=1).allow_shopping_with_stock_available

    def get_product_info(self, template):
        products = request.env['product.product'].sudo().search(
            [('product_tmpl_id', '=', template.id)])
        result = {}
        if not self.limit_stock():
            return None

        no_variants_product = len(template.product_variant_ids) == 1 and len(
            template.product_variant_ids[0].attribute_value_ids) == 0
        if no_variants_product:
            return int(template.sudo().qty_available)

        for p in products:
            attr_values = p.attribute_value_ids
            number_of_attr = len(attr_values.ids)
            if number_of_attr > 2:
                continue
            if number_of_attr == 2:
                attributes = [attr_values[0].id, attr_values[1].id]
                attributes.sort()
                key = '%s-%s' % (attributes[0], attributes[1])
            if number_of_attr == 1:
                attributes = [attr_values[0].id]
                key = '%s' % attributes[0]
            result[key] = p.qty_available > 0 and int(p.qty_available) or 0
        return result

    @http.route(['/shop/product/<model("product.template"):product>'],
                type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        r = super(WebsiteSale, self).product(
            product, category, search, **kwargs)
        sale_order_id = request.session['sale_order_id']
        sale_order_obj = request.env['sale.order']
        if sale_order_id:
            order = sale_order_obj.browse(sale_order_id)
            product_qtys = sale_order_obj.get_order_product_qtys(order)
            r.qcontext['get_order_product_qty'] = product_qtys
        r.qcontext['get_product_info'] = self.get_product_info
        return r
