###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo import fields, http
from odoo.http import request

try:
    from odoo.addons.portal.controllers.portal import CustomerPortal
except ImportError:
    CustomerPortal = object
try:
    from odoo.addons.purchase.controllers.portal import \
        CustomerPortal as PortalPurchase
except ImportError:
    PortalPurchase = object


class PortalPurchaseCustomerPortal(CustomerPortal):
    def _get_purchase_order_domain(self):
        partner_id = request.env.user.partner_id.commercial_partner_id.id
        return [
            ('message_partner_ids', 'child_of', partner_id),
            ('state', 'in', ['purchase', 'done']),
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

    @http.route(
        ['/my/upload_purchase_invoice/<int:purchase_id>'],
        type='http', auth='user', website=True)
    def portal_my_upload_purchase_invoice(
            self, purchase_id, csrf_token=None, **kw):
        domain = self._get_purchase_order_domain()
        domain += [('id', '=', purchase_id)]
        purchase_orders = request.env['purchase.order'].sudo().search(domain)
        if purchase_orders:
            purchase_orders[0].supplier_invoice_number = kw.get(
                'supplier_invoice_number')
            purchase_orders[0].supplier_invoice_date = fields.Date.from_string(
                kw.get('supplier_invoice_date'))
            purchase_orders[0].supplier_invoice_file = base64.b64encode(
                kw.get('supplier_invoice_file').read())
        return request.redirect(
            '/my/purchase/%s' % purchase_id)
