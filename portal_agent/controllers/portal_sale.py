###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request

try:
    from odoo.addons.portal_sale.controllers.portal_sale import (
        PortalSaleCustomerPortal)
except ImportError:
    PortalSaleCustomerPortal = object


class PortalSaleCustomerPortal(PortalSaleCustomerPortal):
    def _get_sale_quotation_domain(self):
        res = super()._get_sale_quotation_domain()
        partner = request.env.user.sudo().partner_id
        if not partner.agent:
            return res
        res = [
            '|',
            ('partner_id.agents', 'in', [partner.id]),
        ] + res
        return res

    def _get_sale_order_domain(self):
        res = super()._get_sale_order_domain()
        partner = request.env.user.sudo().partner_id
        if not partner.agent:
            return res
        res = [
            '|',
            ('partner_id.agents', 'in', [partner.id]),
        ] + res
        return res

    @http.route()
    def portal_order_page(
        self, order_id, report_type=None, access_token=None, message=False,
            download=False, **kw):
        res = super().portal_order_page(
            order_id=order_id, report_type=report_type,
            access_token=access_token, message=message, download=download, **kw)
        agent_customer_id = kw.get('agent_customer_id', False)
        if not agent_customer_id:
            return res
        agent_customer = request.env['res.partner'].browse(
            int(agent_customer_id))
        res.qcontext['agent_customer'] = (
            agent_customer and agent_customer.sudo() or False)
        return res
