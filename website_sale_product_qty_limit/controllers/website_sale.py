###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers import main
from odoo.http import request


class WebsiteSale(main.WebsiteSale):
    def _check_qty_limit(self, order):
        for line in order.order_line:
            if (
                line.product_id
                and line.product_id.type == 'product'
                and line.product_id.qty_limit > 0
                and line.product_uom_qty > line.product_id.qty_limit
            ):
                line.product_uom_qty = line.product_id.qty_limit

    @http.route()
    def cart(self, **post):
        self._check_qty_limit(request.website.sale_get_order(force_create=1))
        return super(WebsiteSale, self).cart(**post)

    @http.route()
    def checkout(self, **post):
        self._check_qty_limit(request.website.sale_get_order(force_create=1))
        return super(WebsiteSale, self).checkout(**post)

    @http.route()
    def payment(self, **post):
        self._check_qty_limit(request.website.sale_get_order(force_create=1))
        return super(WebsiteSale, self).payment(**post)
