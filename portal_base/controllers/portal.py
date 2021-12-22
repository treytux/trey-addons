###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request

try:
    from odoo.addons.portal.controllers.portal import CustomerPortal
except ImportError:
    CustomerPortal = object


class EditDetailsCustomerPortal(CustomerPortal):
    def _prepare_portal_layout_values(self):
        res = super()._prepare_portal_layout_values()
        res['edit_portal_details'] = request.env[
            'ir.config_parameter'].sudo().get_param(
                'portal_base.edit_portal_details')
        return res

    @http.route(['/my/conditions'], type='http', auth='user', website=True)
    def portal_my_account_conditions(self):
        values = {}
        values.update({
            'page_name': 'conditions',
            'partner': request.env.user.sudo().partner_id,
        })
        return request.render('portal_base.portal_my_conditions', values)
