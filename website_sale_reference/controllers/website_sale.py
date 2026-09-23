###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request


class WebsiteSaleReference(http.Controller):

    @http.route(
        ['/shop/cart/set_client_order_ref'], type='json', auth='public',
        methods=['POST'], website=True)
    def set_client_order_ref(self, client_order_ref=None, **kw):
        order = request.website.sale_get_order()
        if not order or order.state != 'draft':
            return {'client_order_ref': False}
        order.client_order_ref = (client_order_ref or '').strip() or False
        return {'client_order_ref': order.client_order_ref or False}
