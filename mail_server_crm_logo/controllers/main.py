###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo import http
from odoo.http import request


class MailServerCrmLogoController(http.Controller):

    @http.route(
        '/team_logo/<int:team_id>',
        type='http', auth='public', methods=['GET'], sitemap=False)
    def team_logo(self, team_id, **kwargs):
        team = request.env['crm.team'].sudo().browse(team_id)
        if not team.exists() or not team.logo:
            return request.not_found()
        image_bin = base64.b64decode(team.logo)
        return request.make_response(
            image_bin,
            headers=[
                ('Content-Type', 'image/png'),
                ('Cache-Control', 'public, max-age=86400')
            ]
        )
