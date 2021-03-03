###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website


class Website(Website):

    @http.route([
        '/profile/<int:user_id>',
    ], type='http', auth='none', website=True)
    def location(self, user_id, **post):
        users_ids = request.env['res.config.settings'].sudo().search(
            [], order='id desc', limit=1).website_public_users.ids
        if not request.session.uid or user_id in users_ids:
            request.session['context'] = dict(
                request.session['context'], set_profile=user_id)
        return request.redirect(request.httprequest.referrer)
