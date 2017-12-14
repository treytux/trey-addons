# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

import openerp.addons.website_sale.controllers.main
from openerp import http


class ContactUs(openerp.addons.website_crm.controllers.main.contactus):
    @http.route(['/crm/contactus'], type='http', auth="public", website=True)
    def contactus(self, **kwargs):
        pass
        # r = super(ContactUs, self).contactus(**kwargs)
        # return self.get_contactus_response(values, kwargs)
