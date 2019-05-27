###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.http import request
from odoo.addons.website_sale_delivery.models import res_country


class WebSiteSaleCountries(res_country.ResCountry):

    def get_website_sale_countries(self, mode=None):
        return request.env['res.country'].search(
            [('website_published', '=', True)])
