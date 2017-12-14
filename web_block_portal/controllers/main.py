# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

import werkzeug.utils
from openerp import http
from openerp.http import request
from openerp.addons.web.controllers import main


class Home(main.Home):
    login_redirect = '/'

    def _get_login_redirect(self):
        return self.login_redirect

    @http.route('/web', type='http', auth='none')
    def web_client(self, **post):
        env = request.env

        if request.session.uid:
            user = env['res.users'].browse(request.session.uid)
            if not user.has_group('base.group_user'):
                return werkzeug.utils.redirect(
                    post.get('redirect', self._get_login_redirect()))

        return super(Home, self).web_client(**post)
