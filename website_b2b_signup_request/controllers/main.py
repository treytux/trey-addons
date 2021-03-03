###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, http
from odoo.http import request


class SingUp(http.Controller):
    def get_contact_fields(self):
        return [
            'contact_name',
            'description',
            'email_from',
            'name',
            'partner_name',
            'phone',
            'vat',
        ]

    @http.route(
        ['/web/signup-request'], type='http', auth='public', website=True)
    def signup_b2b(self, **kwargs):
        values = {f: kwargs.get(f) for f in self.get_contact_fields()}
        kwargs['name'] = _('Signup Request')
        values.update(kwargs=kwargs.items())
        return request.render(
            'website_b2b_signup_request.signup_form', values)
