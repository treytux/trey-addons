# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import openerp.addons.website_sale.controllers.main as main


class WebsiteSale(main.website_sale):
    def __init__(self, *args, **kwargs):
        super(WebsiteSale, self).__init__(*args, **kwargs)
        if 'vat' in self.optional_billing_fields:
            index = self.optional_billing_fields.index('vat')
            del self.optional_billing_fields[index]
        if 'vat' not in self.mandatory_billing_fields:
            self.mandatory_billing_fields.append('vat')
