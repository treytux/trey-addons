###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    def _update_website_sale_acquirer_return(self, order, acquirer_id):
        if not order:
            return {}
        currency = order.currency_id
        return {
            'status': order.delivery_rating_success,
            'error_message': order.delivery_message,
            'acquirer_id': acquirer_id,
            'new_amount_delivery': self._format_amount(
                order.delivery_price, currency),
            'new_amount_untaxed': self._format_amount(
                order.amount_untaxed, currency),
            'new_amount_tax': self._format_amount(
                order.amount_tax, currency),
            'new_amount_total': self._format_amount(
                order.amount_total, currency),
        }

    def _update_website_sale_acquirer(self, **post):
        acquirer_id = (
            'acquirer_id' in post and int(post['acquirer_id']) or False)
        order = request.website.sale_get_order()
        if order and acquirer_id:
            acquirer = request.env['payment.acquirer'].browse(acquirer_id)
            order.general_discount = acquirer and acquirer.discount or 0
            order.onchange_general_discount()
        return self._update_website_sale_acquirer_return(order, acquirer_id)

    @http.route(
        ['/shop/update_acquirer'], type='json', auth='public',
        methods=['POST'], website=True, csrf=False)
    def update_eshop_acquirer(self, **post):
        results = {}
        if hasattr(self, '_update_website_sale_acquirer'):
            results.update(self._update_website_sale_acquirer(**post))
        return results
