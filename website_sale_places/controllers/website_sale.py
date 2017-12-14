# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.http import request
import openerp.addons.website_sale.controllers.main as main


class WebSiteSale(main.website_sale):
    def checkout_values(self, data=None):
        res = super(WebSiteSale, self).checkout_values(data=data)

        if 'countries' and 'states' in res:
            env = request.env
            countries = env['res.country'].search(
                [('website_published', '=', True)])
            res['countries'] = countries
            states = env['res.country.state'].search(
                [('country_id', 'in', countries.ids)])
            res['states'] = states

        return res
