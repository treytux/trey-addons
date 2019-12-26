###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from openerp.http import request
import werkzeug
try:
    from odoo.addons.auth_signup.controllers.main import AuthSignupHome
except ImportError:
    AuthSignupHome = object


class AuthSignupHome(AuthSignupHome):

    @http.route()
    def web_auth_signup(self, *args, **kw):
        res = super(
            AuthSignupHome, self).web_auth_signup(*args, **kw)
        qcontext = self.get_auth_signup_qcontext()
        if 'error' not in qcontext and request.httprequest.method == 'POST':
            user_sudo = request.env['res.users'].sudo().search(
                [('login', '=', qcontext.get('login'))], limit=1)
            template = request.env.ref(
                'auth_signup.mail_template_user_signup_account_created',
                raise_if_not_found=False)
            if user_sudo and template:
                template.sudo().with_context(
                    lang=user_sudo.lang,
                    auth_login=werkzeug.url_encode(
                        {'auth_login': user_sudo.email}),
                ).send_mail(user_sudo.id, force_send=True)
        return res
