###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):

    @http.route()
    def check_field_validations(self, values):
        order = request.website.sale_get_order(force_create=1)
        order['note'] = 'note' in values and values['note'] or ''
        return super(WebsiteSale, self).check_field_validations(values)
