###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request
try:
    from odoo.addons.website.controllers.main import Website
except ImportError:
    Website = object
try:
    from odoo.addons.auth_signup.controllers.main import AuthSignupHome
except ImportError:
    AuthSignupHome = object


class WebsiteValidation(Website):
    @http.route()
    def web_login(self, redirect=None, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        all_data = all([
            qcontext.get('login'), qcontext.get('name'),
            qcontext.get('password'), qcontext.get('signup_enabled')])
        if (not all_data or
                request.httprequest.environ['PATH_INFO'] != '/web/signup'):
            return super(WebsiteValidation, self).web_login(
                redirect=redirect, *args, **kw)
        user = request.env['res.users'].sudo().search(
            [('login', '=', qcontext.get('login'))], limit=1)
        if not user:
            return super(WebsiteValidation, self).web_login(
                redirect=redirect, *args, **kw)
        user.partner_id.allowed = False
        request.session.logout(keep_db=True)
        template = request.env.ref(
            'auth_signup_validation.activation_request_email')
        template = template.sudo().with_context(
            lang=user.lang).send_mail(user.id)
        response = request.render(
            'auth_signup_validation.welcome', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response


class AuthSignupHomeValidation(AuthSignupHome):
    def _signup_with_values(self, token, values):
        db, login, password = request.env['res.users'].sudo().signup(
            values, token)
        request.env.cr.commit()
