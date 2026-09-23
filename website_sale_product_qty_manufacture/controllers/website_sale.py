###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers import \
    variant as website_sale_variant


class WebsiteSaleVariantController(website_sale_variant.WebsiteSaleVariantController):

    @http.route()
    def get_combination_info_website(
        self, product_template_id, product_id, combination, add_qty, **kw
    ):
        kw['context'] = kw.get('context', {})
        kw['context'].update(qty_manufacture_add_to_virtual=True)
        return super().get_combination_info_website(
            product_template_id=product_template_id,
            product_id=product_id,
            combination=combination,
            add_qty=add_qty,
            **kw
        )
