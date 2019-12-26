###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    @http.route()
    def check_field_validations(self, values):
        res = super().check_field_validations(values=values)
        sale_order_id = request.session.get('sale_last_order_id')
        if not sale_order_id:
            return res
        order = request.env['sale.order'].sudo().browse(sale_order_id)
        if not order:
            return res
        if 'agent_customer' not in values:
            return res
        order.agent_customer = int(values['agent_customer'])
        return res

    @http.route()
    def payment_confirmation(self, **post):
        res = super().payment_confirmation(**post)
        sale_order_id = request.session.get('sale_last_order_id')
        if not sale_order_id:
            return res
        order = request.env['sale.order'].sudo().browse(sale_order_id)
        if not order or not order.agent_customer:
            return res
        request.env['mail.followers'].create({
            'res_model': 'sale.order',
            'res_id': order.id,
            'partner_id': order.agent_customer.id})
        return res
