# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.http import request
import openerp.addons.website_sale.controllers.main as main


class WebsiteSale(main.website_sale):
    def checkout_form_validate(self, data):
        error = super(WebsiteSale, self).checkout_form_validate(data)
        env = request.env

        if 'vat' in data and env.user.vat != data['vat'] and data['vat'] != '':
            exists = env.user.search([('vat', '=', data['vat'])])
            if exists:
                error['vat'] = 'error'

        return error
