###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    @http.route(
        ['/shop/cart/note'], type='json', auth='public',
        methods=['POST'], website=True, csrf=False)
    def note(self, note, **post):
        order = request.website.sale_get_order()
        order.note = note
        return True
