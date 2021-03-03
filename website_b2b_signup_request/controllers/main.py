# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import _, http
from openerp.http import request


class SignUp(http.Controller):

    def get_contact_fields(self):
        return [
            'company',
            'contact_name',
            'description',
            'email_from',
            'name',
            'partner_name',
            'phone',
            'vat',
        ]

    @http.route(['/page/signup'], type='http', auth='public', website=True)
    def signup_b2b(self, **kwargs):
        values = {f: kwargs.get(f) for f in self.get_contact_fields()}
        kwargs['name'] = _('Sign up request')
        values.update(kwargs=kwargs.items())
        return request.website.render(
            'website_b2b_signup_request.signup_form', values)
