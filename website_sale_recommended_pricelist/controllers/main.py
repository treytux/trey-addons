# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import openerp.addons.website_sale.controllers.main as main
from openerp import http
from openerp.http import request


class WebsiteSale(main.website_sale):

    def get_recommended_price(self, product_tmpl_ids):
        recommended_dic = {}
        user_obj = request.env['res.users']
        for product_tmpl in request.env['product.template'].sudo().browse(
                product_tmpl_ids):
            if request.uid != request.website.user_id.id:
                partner = user_obj.sudo().browse(
                    request.uid).partner_id.root_partner_id
                recommended_pricelist = partner.recommended_pricelist_id
                if not recommended_pricelist.exists():
                    recommended_dic[product_tmpl.id] = -1
                else:
                    recommended_price = recommended_pricelist.price_get(
                        product_tmpl.product_variant_ids[0].id, 1, partner)[
                            recommended_pricelist.id]
                    recommended_dic[product_tmpl.id] = recommended_price
        return recommended_dic

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        r = super(WebsiteSale, self).product(
            product, category, search, **kwargs)
        r.qcontext['recommended_price'] = self.get_recommended_price(
            product.ids)
        return r

    @http.route()
    def shop(self, page=0, category=None, search='', **post):
        r = super(WebsiteSale, self).shop(
            page=page, category=category, search=search, **post)
        r.qcontext['recommended_price'] = self.get_recommended_price(
            r.qcontext['products'].ids)
        return r

    @http.route()
    def cart(self, **post):
        r = super(WebsiteSale, self).cart(**post)
        order = r.qcontext['order']
        product_tmpl_ids = []
        if order:
            [[product_tmpl_ids.append(product.product_tmpl_id.id)
                for product in line.product_id]
                for line in order.order_line]
            r.qcontext['recommended_price'] = self.get_recommended_price(
                product_tmpl_ids)
        return r
