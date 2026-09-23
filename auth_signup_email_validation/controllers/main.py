###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from email_validator import EmailSyntaxError, validate_email
from odoo import _
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.exceptions import ValidationError


class AuthSignupHome(AuthSignupHome):

    def _prepare_signup_values(self, qcontext):
        values = super()._prepare_signup_values(qcontext)
        if qcontext.get('token'):
            return values
        login = (values.get('login') or '').strip()
        try:
            normalized_login = validate_email(
                login, check_deliverability=False).normalized.lower()
        except EmailSyntaxError as error:
            raise ValidationError(_('Invalid email address')) from error
        values['login'] = normalized_login
        qcontext['login'] = normalized_login
        return values
