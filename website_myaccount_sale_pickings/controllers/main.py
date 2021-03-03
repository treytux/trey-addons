# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import werkzeug
from openerp import http
from openerp.exceptions import AccessError, MissingError
from openerp.http import request
from openerp.addons.website_myaccount_sale.controllers.main import (
    MyAccountSale)


class MyAccountSale(MyAccountSale):
    @http.route([
        '/my/order/pickings/<int:order_id>',
    ], type='http', auth='user', website=True)
    def order_pickings(self, order_id):
        saleorder = request.env['sale.order'].browse(order_id)
        if not saleorder.exists():
            raise werkzeug.exceptions.NotFound()
        try:
            pickings = request.env['stock.picking'].sudo().search([
                ('origin', '=', saleorder.name),
            ])
        except (AccessError, MissingError):
            return request.redirect('/my/orders')
        values = {
            'pickings': pickings,
            'order': saleorder,
        }
        return request.website.render(
            'website_myaccount_sale_pickings.myaccount_order_pickings', values)
