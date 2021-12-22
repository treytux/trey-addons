###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.http import request

try:
    from odoo.addons.portal.controllers.portal import CustomerPortal
except ImportError:
    CustomerPortal = object
try:
    from odoo.addons.purchase.controllers.portal import (
        CustomerPortal as PortalPurchase)
except ImportError:
    PortalPurchase = object


class PortalPurchaseCustomerPortal(CustomerPortal):
    def _get_purchase_order_domain(self):
        partner_id = request.env.user.partner_id.commercial_partner_id.id
        return [
            ('message_partner_ids', 'child_of', partner_id),
            ('state', 'in', ['purchase', 'done'])
        ]

    def _get_archive_groups(
        self, model, domain=None, fields=None, groupby='create_date',
            order='create_date desc'):
        if model == 'purchase.order':
            domain += self._get_purchase_order_domain()
        return super()._get_archive_groups(
            model, domain=domain, fields=fields, groupby=groupby,
            order=order)


class PortalPurchasePortalPurchase(PortalPurchase):
    def _prepare_portal_layout_values(self):
        res = super()._prepare_portal_layout_values()
        res['purchase_count'] = request.env['purchase.order'].search_count(
            self._get_purchase_order_domain())
        return res
