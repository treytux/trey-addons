###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):

    @http.route()
    def check_field_validations(self, values):
        order = request.website.sale_get_order(force_create=1)
        order['note'] = 'note' in values and values['note'] or ''
        return super(WebsiteSale, self).check_field_validations(values)
