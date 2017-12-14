# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http
import openerp.addons.website_sale.controllers.main as main
from openerp.addons.web.http import request


class WebsiteSale(main.website_sale):
    @http.route(['/shop/empty-cart'], type='json', auth='public',
                methods=['post'], website=True)
    def empty_cart(self):
        request.website.sale_reset()
        return {}
