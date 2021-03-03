###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.auth_signup.controllers.main import AuthSignupHome


class AuthSignupHomeFixes(AuthSignupHome):
    def get_auth_signup_qcontext(self):
        result = super(AuthSignupHomeFixes, self).get_auth_signup_qcontext()
        if 'login' in result:
            result['login'] = result['login'].replace(' ', '')
        return result
