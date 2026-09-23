###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo import fields, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

try:
    from odoo.addons.purchase.controllers.portal import CustomerPortal
except ImportError:
    PortalPurchase = object


class PortalPurchaseCustomerPortal(CustomerPortal):
    @http.route(
        ['/my/upload_purchase_invoice/<int:purchase_id>'],
        type='http', auth='user', website=True)
    def portal_my_upload_purchase_invoice(
            self, purchase_id, access_token=None, **kw):
        try:
            purchase_order = self._document_check_access(
                'purchase.order', purchase_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect(
                '/my/purchase/%s' % purchase_id)
        if purchase_order:
            purchase_order.supplier_invoice_number = kw.get(
                'supplier_invoice_number')
            purchase_order.supplier_invoice_date = fields.Date.from_string(
                kw.get('supplier_invoice_date'))
            purchase_order.supplier_invoice_file = base64.b64encode(
                kw.get('supplier_invoice_file').read())
        return request.redirect(
            '/my/purchase/%s' % purchase_id)
