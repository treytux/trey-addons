###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.http import request, route
from odoo.addons.portal.controllers import portal


class PortalCustomerCountries(portal.CustomerPortal):

    @route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        res = super(
            PortalCustomerCountries, self).account(redirect=redirect, **post)
        res.qcontext['countries'] = request.env['res.country'].search(
            [('website_published', '=', True)])
        return res
