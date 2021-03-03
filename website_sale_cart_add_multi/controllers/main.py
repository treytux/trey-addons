###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    @http.route(['/shop/cart/update_json_multi'],
                type='json', auth='public', methods=['post'], website=True)
    def cart_update_json_multi(self, product_id, line_id=None, add_qty=None,
                               set_qty=None, display=True):
        order = request.website.sale_get_order(force_create=1)
        if order.state != 'draft':
            request.website.sale_reset()
            return {}
        data = {
            'values': [],
            'cart_quantity': 0,
            'website_sale.cart_lines': '',
            'website_sale.short_cart_summary': '',
        }
        line_ids = {}
        for ol in order.order_line:
            line_ids[ol.product_id.id] = ol.id
        for k, _v in enumerate(product_id):
            value = order._cart_update(
                product_id=product_id[k],
                line_id=(
                    line_id
                    and line_id[k]
                    or (
                        product_id[k] in line_ids
                        and line_ids[product_id[k]]
                        or None
                    )
                ),
                add_qty=add_qty and add_qty[k] or None,
                set_qty=set_qty and set_qty[k] or None)
            data['values'].append(value)
        if not order.cart_quantity:
            request.website.sale_reset()
            return data
        order = request.website.sale_get_order()
        data['cart_quantity'] = order.cart_quantity
        from_currency = order.company_id.currency_id
        to_currency = order.pricelist_id.currency_id
        if not display:
            return data
        ir_ui_view = request.env['ir.ui.view']
        cart_lines = ir_ui_view.render_template(
            'website_sale.cart_lines', {
                'website_sale_order': order,
                'compute_currency': lambda price: from_currency._convert(
                    price, to_currency, order.company_id, fields.Date.today()),
                'date': fields.Date.today(),
                'suggested_products': order._cart_accessories()})
        short_cart_summary = ir_ui_view.render_template(
            'website_sale.short_cart_summary', {
                'website_sale_order': order,
                'compute_currency': lambda price: from_currency._convert(
                    price, to_currency, order.company_id,
                    fields.Date.today())})
        data['website_sale.cart_lines'] = cart_lines
        data['website_sale.short_cart_summary'] = short_cart_summary
        return data
