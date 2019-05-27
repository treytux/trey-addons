###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, http
from odoo.http import request
from odoo.addons.web.controllers import main
from odoo.exceptions import AccessError


class Home(main.Home):
    @http.route()
    def web_login(self, redirect=None, **kw):
        if request.httprequest.method == 'POST':
            users = request.env['res.users'].sudo().search([
                ('login', '=', request.params['login'])])
            if len(users) > 1:
                raise AccessError(
                    _('More than one user found with login: %s') %
                    request.params['login'])
            user = users and users[0] or False
            if user and not user.allowed:
                return request.render(
                    'partner_blocking.blocked_user', {
                        'user': user,
                        'name': _('My user "%s" is blocked') % user.login,
                        'description': _(
                            'Can you please allow my user "%s" to login '
                            'into your system?') % user.login})
        return super(Home, self).web_login(redirect=redirect, **kw)
