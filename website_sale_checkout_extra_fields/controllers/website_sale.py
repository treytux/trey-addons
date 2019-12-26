###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    @http.route(
        ['/shop/cart/validation'], type='json', auth='public',
        methods=['POST'], website=True, csrf=False)
    def check_field_validations(self, values):
        return {'error': []}
