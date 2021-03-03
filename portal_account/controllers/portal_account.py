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
            ('state', 'in', ['open', 'in_payment', 'paid']),
        ]

    def _get_archive_groups(
        self, model, domain=None, fields=None, groupby='create_date',
            order='create_date desc'):
        if model == 'account.invoice':
            domain += self._get_account_invoice_domain()
        return super()._get_archive_groups(
            model, domain=domain, fields=fields, groupby=groupby,
            order=order)


class PortalAccountPortalAccount(PortalAccount):
    def _get_invoice_domain(self):
        partner_id = request.env.user.sudo().partner_id
        commercial_partner_id = partner_id.commercial_partner_id.id
        return [
            ('partner_id', '=', commercial_partner_id),
            ('state', 'in', ['open', 'paid']),
        ]

    def _prepare_portal_layout_values(self):
        res = super()._prepare_portal_layout_values()
        website = request.env['website'].get_current_website()
        res['invoice_count'] = request.env['account.invoice'].search_count(
            self._get_account_invoice_domain())
        res['invoice_open_paid'] = request.env['account.invoice'].search(
            self._get_invoice_domain(),
            order='date desc, id desc', limit=website.limit_account)
        return res
