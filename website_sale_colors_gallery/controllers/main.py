###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    def _get_gallery_unique_variant_colors(self, product_tmpls):
        color_attrs = {}
        for product_tmpl in product_tmpls:
            color_attrs[product_tmpl.id] = {}
            for product_id in product_tmpl.product_variant_ids:
                for attribute_value in (
                    product_id.attribute_value_ids.filtered(
                        lambda x: x.attribute_id.type == 'color')):
                    if attribute_value.id in color_attrs[product_tmpl.id]:
                        continue
                    color_attrs[product_tmpl.id].setdefault(
                        attribute_value.id, product_id)
            color_attrs[product_tmpl.id] = list(
                color_attrs[product_tmpl.id].values())
        return color_attrs

    @http.route()
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        res = super().shop(
            page=page, category=category, search=search, ppg=ppg, **post)
        res.qcontext['color_attrs'] = self._get_gallery_unique_variant_colors(
            res.qcontext['products'])
        return res
