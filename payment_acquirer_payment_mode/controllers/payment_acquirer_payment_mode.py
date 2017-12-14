# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import openerp.addons.website_sale.controllers.main as main
from openerp import http
from openerp.http import request

import logging
_log = logging.getLogger(__name__)


class WebsiteSale(main.website_sale):
    @http.route(
        '/shop/payment/validate',
        type='http',
        auth="public",
        website=True)
    def payment_validate(
            self,
            transaction_id=None,
            sale_order_id=None,
            **post):
        context = request.context
        env = request.env
        if sale_order_id is None:
            order = request.website.sale_get_order(context=context)
        else:
            order = env['sale.order'].sudo().search(
                [('id', '=', sale_order_id)])
            assert order.id == request.session.get('sale_last_order_id')
        if order.payment_acquirer_id and \
           order.payment_acquirer_id.payment_mode_id:

            order_data = {
                'payment_mode_id': order.payment_acquirer_id.payment_mode_id.id
            }
            order.write(order_data)
        return super(WebsiteSale, self).payment_validate(
            transaction_id=transaction_id,
            sale_order_id=sale_order_id,
            **post)
