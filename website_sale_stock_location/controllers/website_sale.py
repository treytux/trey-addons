###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers import main


class WebsiteSale(main.WebsiteSale):

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        values = super().product(
            product, category=category, search=search, **kwargs)
        variants_stock = {}
        for variant in product.product_variant_ids:
            variants_stock.setdefault(variant.id, {
                'variant_id': variant.id,
                'locations': {},
            })
            for quant in variant.stock_quant_ids.sudo().filtered(
                    lambda q: q.location_id.usage == 'internal'):
                variants_stock[variant.id]['locations'].setdefault(
                    quant.location_id.complete_name, {
                        'location_id': '',
                        'location_name': '',
                        'product_uom_name': '',
                        'quantity': 0,
                    })
                variants_stock[variant.id]['locations'][
                    quant.location_id.complete_name][
                    'location_id'] = quant.location_id
                variants_stock[variant.id]['locations'][
                    quant.location_id.complete_name][
                    'location_name'] = quant.location_id.complete_name
                variants_stock[variant.id]['locations'][
                    quant.location_id.complete_name][
                    'product_uom_name'] = quant.product_uom_id.name
                variants_stock[variant.id]['locations'][
                    quant.location_id.complete_name][
                    'quantity'] += quant.quantity
        values.qcontext['variants_stock'] = variants_stock
        return values
