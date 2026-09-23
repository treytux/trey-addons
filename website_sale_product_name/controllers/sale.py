from odoo import http
from odoo.addons.sale.controllers.variant import \
    VariantController as SaleVariantController
from odoo.http import request


class VariantController(SaleVariantController):
    @http.route()
    def get_combination_info(
            self, product_template_id, product_id, combination, add_qty,
            pricelist_id, **kw):
        res = super().get_combination_info(
            product_template_id=product_template_id, product_id=product_id,
            combination=combination, add_qty=add_qty,
            pricelist_id=pricelist_id, **kw)
        if (
            'website_id' not in request.context
                or not request.context['website_id']):
            return res
        product_tmpl_id = res.get('product_template_id', False)
        if not product_tmpl_id:
            return res
        product = request.env['product.template'].browse(product_tmpl_id)
        if not product:
            return res
        res['display_name'] = product.website_name
        return res
