###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    @http.route(
        ['/shop/enable-maintenance'], type='http', auth='public', website=True)
    def enable_maintenance(self):
        order = request.website.sale_get_order()
        order.enable_maintenance()
        return request.redirect('/shop/cart')

    @http.route(
        ['/shop/disable-maintenance'], type='http', auth='public', website=True)
    def disable_maintenance(self):
        order = request.website.sale_get_order()
        order.disable_maintenance()
        return request.redirect('/shop/cart')

    @http.route()
    def cart(self, access_token=None, revive='', **post):
        request.env.context = dict(
            request.env.context,
            force_update_maintenance_line=True)
        return super().cart(access_token=access_token, revive=revive, **post)
