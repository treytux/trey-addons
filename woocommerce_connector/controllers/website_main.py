###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http

try:
    from odoo.addons.website.controllers.main import WebsiteBinary
except ImportError:
    WebsiteBinary = object


class WebsiteBinaryExtended(WebsiteBinary):

    @http.route([
        '/website/image/<model>/<id>/<field>/<filename>',
    ], type='http', auth='public', website=False, multilang=False)
    def content_image(self, id=None, max_width=0, max_height=0, **kw):
        return super().content_image(
            id=id, max_width=max_width, max_height=max_height, **kw)
