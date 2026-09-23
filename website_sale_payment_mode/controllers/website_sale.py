###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    @http.route()
    def shop_payment_validate(self, sale_order_id=None, **post):
        SaleOrder = request.env['sale.order'].sudo()
        order = None
        if sale_order_id:
            sale_order_id = int(sale_order_id)
            order = SaleOrder.browse(sale_order_id).exists()
        else:
            session_order_id = request.session.get('sale_order_id')
            if session_order_id:
                order = SaleOrder.browse(session_order_id).exists()
            else:
                order = request.website.sale_get_order()
        if order and order.transaction_ids:
            transaction = order.transaction_ids[0]
            if transaction.provider_id:
                self._assign_payment_mode_to_order(order, transaction.provider_id)
        return super().shop_payment_validate(sale_order_id=sale_order_id, **post)

    def _assign_payment_mode_to_order(self, order, payment_provider):
        if payment_provider.payment_mode_id:
            payment_mode = payment_provider.payment_mode_id
        elif order.partner_id.customer_payment_mode_id:
            payment_mode = order.partner_id.customer_payment_mode_id
        else:
            return
        order.write({
            'payment_mode_id': payment_mode.id,
        })
