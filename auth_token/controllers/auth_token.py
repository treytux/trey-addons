###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.web.controllers.main import set_cookie_and_redirect
from odoo.http import Response, request


class AuthToken(http.Controller):
    @http.route('/token/<string:token>', type='http', auth='none')
    def auth_token(self, token, **post):
        users = request.env['res.users'].sudo().search([('token', '=', token)])
        if len(users) != 1:
            return Response(status=500)
        website = request.env['website'].get_current_website()
        token_access = website.token_access
        if (token_access == 'internal_users' and users.share) or (
                token_access == 'external_users' and not users.share):
            return Response(status=500)
        request.session.authenticate(
            http.request.session.db,
            login=users[0].login,
            password=users[0].token,
            uid=users[0].id,
        )
        return set_cookie_and_redirect('/my')
