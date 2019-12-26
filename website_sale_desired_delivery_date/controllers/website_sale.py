###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http, _
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request
import datetime


class WebsiteSale(WebsiteSale):

    @http.route()
    def check_field_validations(self, values):
        res = super(WebsiteSale, self).check_field_validations(values)
        if 'commitment_date' not in values or not values['commitment_date']:
            return res
        order = request.website.sale_get_order(force_create=1)
        post_commitment_date = values['commitment_date']
        if post_commitment_date < datetime.datetime.now().strftime("%Y-%m-%d"):
            res['error'].append(
                _('Desired date must be later than current one.'))
            return res
        if post_commitment_date < order.expected_date.strftime("%Y-%m-%d"):
            res['error'].append(
                _('Desired date must be later than expected '
                  'date \'%s\'.') % (
                    order.expected_date.strftime('%d/%m/%Y')))
            return res
        order['commitment_date'] = post_commitment_date
        return res
