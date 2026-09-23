###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request


class BmcatController(http.Controller):

    @http.route('/bmcat/<string:token>/download',
                type='http', auth='public', methods=['GET'])
    def bmcat_download(self, token):
        catalog = request.env['product.catalog'].sudo().search([
            ('bmcat_token', '=', token),
        ], limit=1)
        if not catalog:
            return request.not_found()
        xml_content = catalog._bmcat_get_or_generate()
        if not xml_content:
            return request.not_found()
        filename = catalog.bmcat_filename or 'catalog.xml'
        headers = [
            ('Content-Type', 'application/xml; charset=utf-8'),
            ('Content-Disposition', 'attachment; filename="%s"' % filename),
            ('Content-Length', str(len(xml_content))),
        ]
        return request.make_response(xml_content, headers=headers)
