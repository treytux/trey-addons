###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from decimal import ROUND_HALF_UP, Decimal

from odoo import fields, http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    def get_pricelist_per_qty(self, product_tmpl, pricelist):
        res = {}
        for variant in product_tmpl.product_variant_ids:
            base_price = variant.list_price
            seen_quantities = set()
            items = pricelist._get_applicable_rules(
                variant, fields.Date.today())
            lines = []
            for item in items:
                qty = int(item.min_quantity)
                if qty in seen_quantities:
                    continue
                price = pricelist._get_product_price(
                    variant, qty, uom=variant.uom_id)
                if price is not None and price < base_price:
                    rounded_price = Decimal(str(price)).quantize(
                        Decimal('0.01'), rounding=ROUND_HALF_UP)
                    price_text = f"{qty}-{rounded_price:.2f}"
                    lines.append(price_text)
                    seen_quantities.add(qty)
            if lines:
                res[variant.id] = lines
        return {product_tmpl.id: res} if res else {}

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        res = super().product(
            product=product, category=category, search=search, **kwargs)
        res.qcontext['pricelist_per_qty'] = {}
        if not request.website.user_id:
            return res
        pricelist = res.qcontext.get('pricelist')
        if pricelist:
            pricelist_per_qty = self.get_pricelist_per_qty(
                product, pricelist)
            res.qcontext['pricelist_per_qty'] = pricelist_per_qty
        return res
