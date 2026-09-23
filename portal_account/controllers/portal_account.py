###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.http import request

try:
    from odoo.addons.portal.controllers.portal import CustomerPortal
except ImportError:
    CustomerPortal = object
try:
    from odoo.addons.account.controllers.portal import PortalAccount
except ImportError:
    PortalAccount = object


class PortalAccountCustomerPortal(CustomerPortal):
    def _get_account_invoice_domain(self):
        partner_id = request.env.user.sudo().partner_id.commercial_partner_id.id
        return [
            ('message_partner_ids', 'child_of', [partner_id]),
            ('state', '=', 'posted'),
        ]


class PortalAccountPortalAccount(PortalAccount):
    def _prepare_portal_layout_values(self):
        res = super()._prepare_portal_layout_values()
        website = request.env['website'].get_current_website()
        domain = self._get_account_invoice_domain()
        res['invoice_count'] = request.env['account.move'].search_count(
            domain)
        res['invoice_open_paid'] = request.env['account.move'].search(
            domain, order='date desc, id desc', limit=website.limit_account)
        return res
