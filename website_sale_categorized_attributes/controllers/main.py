# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import http
from openerp.http import request
import openerp.addons.website_sale.controllers.main as main


class WebSiteSale(main.website_sale):
    @http.route()
    def shop(self, page=0, category=None, search='', **post):
        res = super(WebSiteSale, self).shop(
            page=page, category=category, search=search, **post)
        env = request.env
        context = request.context
        if category:
            prod_category = env['product.attribute'].with_context(context)
            attributes = prod_category.sudo().browse(
                category.attribute_ids.ids)
        else:
            attributes = []
        res.qcontext['attributes'] = attributes
        return res
