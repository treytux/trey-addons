# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.addons.website_sale.controllers.main import website_sale
from openerp.http import request


class WebsiteSale(website_sale):
    def checkout_values(self, data=None):
        res = super(WebsiteSale, self).checkout_values(data=data)
        res['checkout']['picking_policy'] = data and data.get(
            'picking_policy', None) or None
        return res

    def checkout_form_save(self, checkout):
        res = super(WebsiteSale, self).checkout_form_save(checkout=checkout)
        picking_policy = checkout.get('picking_policy')
        if picking_policy:
            order = request.website.sale_get_order()
            order.picking_policy = picking_policy
        return res
