# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http
from openerp.http import request
try:
    from openerp.addons.website_myaccount_sale.controllers.main import (
        MyAccountSale)
except ImportError:
    MyAccountSale = object


class MyAccountSaleDuplicate(MyAccountSale):
    @http.route([
        '/my/orders/duplicate/<int:order_id>',
    ], type='http', auth='user', website=True)
    def duplicate_order(self, order_id):
        saleorder = self._prepare_saleorders(saleorder_id=order_id, limit=1)
        if saleorder:
            order_created_id = saleorder.sudo().copy()
            request.session['sale_order_id'] = order_created_id.id
            return request.redirect('/shop/cart')
        return request.redirect('/my/orders')
