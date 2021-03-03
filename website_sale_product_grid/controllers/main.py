###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json
from collections import OrderedDict

from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    def _get_main_attr_value_ids(self, grid_data, main_attr_value_ids):
        values = [
            k for i in grid_data.values() for k in i.keys() if k != 'default']
        return main_attr_value_ids.filtered(lambda a: a.id in values)

    def _get_cart_quantities(self, order=None):
        order = order or request.website.sale_get_order(
            force_create=1)
        cart_quantities = {}
        for line in order.order_line:
            cart_quantities.update({line.product_id.id: line.product_uom_qty})
        return json.dumps(cart_quantities)

    def _fill_grid(self, product_tmpls, main_attr):
        def get_attribute_values_sorted(values):
            return values.sorted(
                lambda v: v.attribute_id.sequence).mapped('sequence')

        grid = OrderedDict({})
        for tmpl in product_tmpls:
            attrs = tmpl.attribute_line_ids.mapped('attribute_id')
            attrs_row = attrs.filtered(
                lambda a: a != main_attr and a.create_variant != 'no_variant')
            variants = tmpl.product_variant_ids.sorted(
                lambda v: get_attribute_values_sorted(v.attribute_value_ids))
            for variant in variants:
                attrs = variant.attribute_value_ids.sorted(
                    lambda a: a.sequence)
                value_col = attrs.filtered(
                    lambda v: v.attribute_id == main_attr)
                value_row = attrs.filtered(
                    lambda v: v.attribute_id in attrs_row)
                key = '%s-%s' % (
                    tmpl.id, '-'.join([str(i) for i in value_row.ids]))
                item = grid.setdefault(key, {'default': variant})
                item[value_col.id] = variant
        return grid

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        res = super(WebsiteSale, self).product(
            product=product, category=category, search=search, **kwargs)
        if product.attribute_line_ids:
            res.qcontext['grid_data'] = self._fill_grid(
                [product], product.attribute_line_ids[0].attribute_id)
            res.qcontext['main_attr_values'] = (
                self._get_main_attr_value_ids(
                    res.qcontext['grid_data'],
                    product.attribute_line_ids[0].attribute_id.value_ids))
            res.qcontext['main_attribute_id'] = (
                product.attribute_line_ids[0].attribute_id)
        res.qcontext['cart_quantities'] = self._get_cart_quantities()
        return res
