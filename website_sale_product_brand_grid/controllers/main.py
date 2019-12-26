###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json
from odoo import http, fields
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    def _get_cart_quantities(self, order=None):
        order = order or request.website.sale_get_order(
            force_create=1)
        cart_quantities = {}
        for l in order.order_line:
            cart_quantities.update({l.product_id.id: l.product_uom_qty})
        return json.dumps(cart_quantities)

    def _order_attrs(self, attrs):
        sorted_attrs = {}
        for attr in attrs:
            if attr.type == 'color':
                sorted_attrs.setdefault('color', {})
                sorted_attrs.update({'color': attr.value_ids})
            else:
                sorted_attrs.setdefault('attrs', {})
                sorted_attrs['attrs'].update({
                    attr: attr.value_ids.sorted(key=lambda r: r.name)})
        return sorted_attrs

    def _fill_grid(self, sorted_attrs, product_tmpls, grid, attribute, brand):
        product_model = request.env['product.product']
        for product_tmpl in product_tmpls:
            attributes = [
                attr_line.attribute_id.type for attr_line in
                product_tmpl.attribute_line_ids]
            if 'color' in attributes:
                grid[attribute].setdefault(product_tmpl, {})
                for color_attr in sorted_attrs['color']:
                    grid[attribute][product_tmpl].setdefault(color_attr, {
                        'product': False,
                        'lines': {}})
                    for attribute_value in brand.main_attribute_id.value_ids:
                        products = product_model.sudo().search([
                            ('attribute_value_ids', 'in', attribute_value.id),
                            ('attribute_value_ids', 'in', color_attr.ids),
                            ('product_tmpl_id', '=', product_tmpl.id),
                            ('product_brand_id', '=', brand.id)])
                        grid_color = grid[attribute][product_tmpl][color_attr]
                        if not products:
                            grid_color['lines'].update({
                                attribute_value: False})
                            continue
                        for product in products:
                            grid_color['product'] = product
                            grid_color['lines'].update({
                                attribute_value: product})
            else:
                grid[attribute].setdefault(product_tmpl, {})
                grid[attribute][product_tmpl].setdefault('no_color', {
                    'product': False,
                    'lines': {}})
                for attribute_value in brand.main_attribute_id.value_ids:
                    products = product_model.sudo().search([
                        ('attribute_value_ids', 'in', attribute_value.id),
                        ('product_tmpl_id', '=', product_tmpl.id),
                        ('product_brand_id', '=', brand.id)])
                    grid_no_color = grid[attribute][product_tmpl]['no_color']
                    if not products:
                        grid_no_color['lines'].update({attribute_value: False})
                        continue
                    for product in products:
                        grid_no_color['product'] = product
                        grid_no_color['lines'].update({
                            attribute_value: product})
        return grid

    @http.route()
    def shop(
            self, page=0, category=None, brand=None, search='', ppg=False,
            **post):
        res = super(WebsiteSale, self).shop(
            page=page, category=category, brand=brand, search=search, ppg=ppg,
            **post)
        path_info = request.httprequest.environ['PATH_INFO']
        if not brand or path_info != '/shop/brands':
            return res
        product_brand = request.env['product.brand'].browse(int(brand))
        if (
            not product_brand.main_attribute_id or
                not product_brand.sell_by_grid):
                return res
        sorted_attrs = self._order_attrs(res.qcontext['attributes'])
        grid = {}
        attribute = product_brand.main_attribute_id
        grid.setdefault(attribute, {})
        products = request.env['product.template'].search([
            ('attribute_line_ids', 'in', attribute.attribute_line_ids.ids),
            ('product_brand_id', '=', product_brand.id),
            ('website_published', '=', True)])
        res.qcontext['grid'] = self._fill_grid(
            sorted_attrs, products, grid, attribute, product_brand)
        res.qcontext['brand'] = product_brand
        res.qcontext['cart_quantities'] = self._get_cart_quantities()
        return request.render(
            'website_sale_product_brand_grid.products_grid', res.qcontext)

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        res = super(WebsiteSale, self).product(
            product=product, category=category, search=search, **kwargs)
        res.qcontext['cart_quantities'] = self._get_cart_quantities()
        return res

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
        for k, v in enumerate(product_id):
            value = order._cart_update(
                product_id=product_id[k],
                line_id=(
                    line_id and line_id[k] or (
                        product_id[k] in line_ids and
                        line_ids[product_id[k]] or None)),
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
