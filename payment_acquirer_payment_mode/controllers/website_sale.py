###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    @http.route()
    def payment_validate(self, transaction_id=None, sale_order_id=None, **post):
        if sale_order_id is None:
            order = request.website.sale_get_order()
        else:
            order = request.env['sale.order'].sudo().search(
                [('id', '=', sale_order_id)])
            assert order.id == request.session.get('sale_last_order_id')
        if order.transaction_ids and order.transaction_ids[0].acquirer_id:
            acquirer = order.transaction_ids[0].acquirer_id
            customer_payment_mode = order.partner_id.customer_payment_mode_id
            if acquirer.payment_mode_id:
                order.write({
                    'payment_mode_id': acquirer.payment_mode_id.id,
                })
            elif customer_payment_mode:
                order.write({
                    'payment_mode_id': customer_payment_mode.id,
                })
        return super().payment_validate(
            transaction_id=transaction_id, sale_order_id=sale_order_id, **post)
