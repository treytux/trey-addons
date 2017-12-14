# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http
from openerp.addons.website_sale.controllers.main import website_sale


class WebsiteSale(website_sale):
    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):
        res = super(WebsiteSale, self).payment()
        order = res.qcontext['order']
        taxes = {}
        for line in order.order_line:
            for tax in line.tax_id:
                t = tax.compute_all(
                    line.price_unit * (1 - (line.discount or 0.0) / 100.0),
                    line.product_uom_qty,
                    line.product_id,
                    line.order_id.partner_id)['taxes']
                if len(t) > 0 and t[0]['name'] not in taxes:
                    taxes[t[0]['name']] = 0
                taxes[t[0]['name']] += t[0]['amount']
        res.qcontext['taxes'] = taxes
        return res
