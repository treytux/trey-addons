###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request


class WebsiteSaleObservations(http.Controller):

    @http.route(
        ['/shop/cart/set_web_order_observations'],
        type='json', auth='public', methods=['POST'], website=True)
    def set_web_order_observations(self, observations=None, **kw):
        order = request.website.sale_get_order()
        if not order or order.state != 'draft':
            return {'observations': False}
        order.web_order_observations = (observations or '').strip() or False
        return {'observations': order.web_order_observations or False}
