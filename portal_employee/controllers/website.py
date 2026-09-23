###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website.controllers.main import Website
from odoo.http import request


class WebsiteEmployee(Website):
    @http.route()
    def web_login(self, redirect=None, *args, **kw):
        response = super().web_login(redirect=redirect, *args, **kw)
        if (
            not redirect and request.params['login_success']
                and request.env.user.employee_portal_block_backoffice):
            return http.redirect_with_hash('/employee')
        return response
