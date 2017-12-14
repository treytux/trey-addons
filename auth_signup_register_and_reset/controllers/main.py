# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import openerp.addons.auth_signup.controllers.main as main
from openerp import http
from openerp.http import request
from openerp.tools.translate import _


class AuthSignupHome(main.AuthSignupHome):
    @http.route('/web/reset_password', type='http', auth='public',
                website=True)
    def web_auth_reset_password(self, *args, **kw):
        env = request.env
        if 'login' in kw:
            users = env['res.users'].sudo().search([(
                'login', '=', kw['login'])])
            if not users.exists():
                partners = env['res.partner'].sudo().search([(
                    'email', '=', kw['login'])])
                if partners.exists():
                    config_param = env['ir.config_parameter']
                    template_user_id = config_param.get_param(
                        'auth_signup.template_user_id')
                    template_user = env['res.users'].browse(
                        int(template_user_id))
                    template_user.sudo().copy({
                        'active': True,
                        'login': kw['login'],
                        'partner_id': partners[0].id})
                    qcontext = self.get_auth_signup_qcontext()
                    qcontext['message'] = _("An email has been sent with "
                                            "credentials to reset your "
                                            "password")
                    return request.render('auth_signup.reset_password',
                                          qcontext)
        return super(AuthSignupHome, self).web_auth_reset_password(args=args,
                                                                   kw=kw)
