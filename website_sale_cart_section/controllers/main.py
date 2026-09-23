###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):

    def get_section_list(self, sections):
        return [{
            'name': section.name,
            'sequence': section.sequence,
            'display_type': section.display_type,
            'linked_line_id': section.linked_line_id.id,
        } for section in sections]

    def get_line_section_data(self, line_dict):
        return {
            'name': line_dict['name'],
            'sequence': line_dict['sequence'],
            'display_type': line_dict['display_type'],
            'linked_line_id': line_dict['linked_line_id'],
        }

    @http.route()
    def cart(self, access_token=None, revive='', **post):
        order = request.website.sale_get_order()
        sect_type = 'line_section'
        sections = order.order_line.filtered(
            lambda ln: not ln.product_id.active
            and ln.display_type == sect_type)
        sections_list = self.get_section_list(sections)
        res = super().cart(access_token=access_token, revive=revive, **post)
        order = request.website.sale_get_order()
        for line in sections_list:
            order.update({
                'order_line': [(0, 0, self.get_line_section_data(line))]
            })
        if not order.order_line.filtered(
                lambda ln: ln.display_type != sect_type):
            order.order_line.filtered(
                lambda ln: not ln.product_id.active
                and ln.display_type == sect_type
            ).unlink()
            request.website.sale_reset()
        else:
            order.website_order_line = order and order.order_line
        return res

    @http.route(
        ['/shop/cart/update_json_multi_section'], type='json', auth='public',
        website=True)
    def cart_update_json_multi_section(self, **kw):
        order = request.website.sale_get_order(force_create=1)
        if order.state != 'draft':
            request.website.sale_reset()
            return {}
        products = kw['product_id']
        quantities = kw['set_qty']
        len_order_line = len(order.order_line)
        sequence = (
            len_order_line != 0
            and order.order_line[len_order_line - 1].sequence + 1 or 1)
        first_product = request.env['product.product'].browse(products[0])
        order.update({
            'order_line': [(0, 0, {
                'name': first_product.name,
                'display_type': 'line_section',
                'sequence': sequence})]
        })
        sequence += 1
        current_website = request.env['website'].get_current_website()
        pricelist = current_website.get_current_pricelist()
        if len(products) == len(quantities):
            for prdt, qty in zip(products, quantities):
                product = request.env['product.product'].sudo().browse(prdt)
                price_lst = product._get_combination_info_variant(
                    pricelist=pricelist)['price']
                order.update({
                    'order_line': [
                        (0, 0, {
                            'product_id': product.id,
                            'price_unit': price_lst,
                            'product_uom_qty': qty or 1,
                            'sequence': sequence}),
                    ]
                })
                sequence += 1
        return request.redirect('/shop/cart')

    @http.route()
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        order = request.website.sale_get_order()
        sect_type = 'line_section'
        minor_sequence = 100
        sections = order.order_line.filtered(
            lambda ln: not ln.product_id.active
            and ln.display_type == sect_type)
        if len(sections) != 0:
            for section in sections:
                if section.sequence < minor_sequence:
                    minor_sequence = section.sequence
        res = super().cart_update(
            product_id=product_id, add_qty=add_qty, set_qty=set_qty, **kw)
        order = request.website.sale_get_order()
        for line in order.order_line:
            if line.product_id.id == product_id:
                line.sequence = minor_sequence
        return res
