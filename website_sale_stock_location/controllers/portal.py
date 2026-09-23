###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class PortalAccessCustomerPortal(CustomerPortal):
    def get_portal_access(self):
        website = request.website
        return website.get_portal_access(request.env.user)

    @http.route()
    def home(self, **kw):
        if self.get_portal_access():
            return super().home(**kw)
        else:
            return request.redirect('/404')

    @http.route()
    def account(self, redirect=None, **post):
        if self.get_portal_access():
            return super().account(redirect=redirect, **post)
        else:
            return request.redirect('/404')

    @http.route()
    def security(self, **post):
        if self.get_portal_access():
            return super().security(**post)
        else:
            return request.redirect('/404')
