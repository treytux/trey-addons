###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request

try:
    from odoo.addons.portal.controllers.portal import CustomerPortal
except ImportError:
    CustomerPortal = object
try:
    from odoo.addons.sale.controllers.portal import (
        CustomerPortal as PortalSale)
except ImportError:
    PortalSale = object


class PortalSaleCustomerPortal(CustomerPortal):
    def _get_sale_quotation_domain(self):
        partner_id = request.env.user.sudo().partner_id.commercial_partner_id.id
        return [
            ('message_partner_ids', 'child_of', [partner_id]),
            ('state', 'in', ['sent'])
        ]

    def _get_sale_order_domain(self):
        partner_id = request.env.user.sudo().partner_id.commercial_partner_id.id
        return [
            ('message_partner_ids', 'child_of', [partner_id]),
            ('state', 'in', ['sale', 'done'])
        ]

    def _get_archive_groups(
        self, model, domain=None, fields=None, groupby='create_date',
            order='create_date desc'):
        if model == 'sale.order':
            domain_request = request.context.get('domain_request', False)
            if domain_request == 'portal_my_quotes':
                domain += self._get_sale_quotation_domain()
            elif domain_request == 'portal_my_orders':
                domain += self._get_sale_order_domain()
        return super()._get_archive_groups(
            model, domain=domain, fields=fields, groupby=groupby,
            order=order)


class PortalSalePortalSale(PortalSale):
    def _prepare_portal_layout_values(self):
        res = super()._prepare_portal_layout_values()
        website = request.env['website'].get_current_website()
        limit = website.limit_orders_quotations
        order_ids = request.env['sale.order'].search(
            self._get_sale_order_domain(),
            order='date_order desc, id desc')
        res['order_count'] = len(order_ids)
        res['orders_sale_done'] = order_ids[:limit]
        quotation_ids = request.env['sale.order'].search(
            self._get_sale_quotation_domain(),
            order='date_order desc, id desc')
        res['quotation_count'] = len(quotation_ids)
        res['quotation_sent'] = quotation_ids[:limit]
        return res

    @http.route()
    def portal_my_quotes(
            self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        context = request.context.copy()
        context['domain_request'] = 'portal_my_quotes'
        request.context = context
        return super().portal_my_quotes(
            page=page, date_begin=date_begin, date_end=date_end, sortby=sortby,
            **kw)

    @http.route()
    def portal_my_orders(
            self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        context = request.context.copy()
        context['domain_request'] = 'portal_my_orders'
        request.context = context
        return super().portal_my_orders(
            page=page, date_begin=date_begin, date_end=date_end, sortby=sortby,
            **kw)
