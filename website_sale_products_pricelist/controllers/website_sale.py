# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import openerp.addons.website_sale.controllers.main as main
from openerp.addons.web.http import request
from openerp import http, fields, exceptions, _


class WebsiteSale(main.website_sale):
    def get_promo(self, product_tmpl, pricelist):
        res = {}
        for pp in product_tmpl.product_variant_ids:
            text = pp.sudo().get_price_by_qty(pricelist.id)
            if not text:
                continue
            res[pp.id] = text
        return {product_tmpl.id: res}

    def get_promo_qtys(self, product_tmpl, pricelist):
        res = {}
        for pp in product_tmpl.product_variant_ids:
            text = self.has_promo(pp, pricelist.id)
            if not text:
                continue
            res[pp.id] = text
        return {product_tmpl.id: res}

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        res = super(WebsiteSale, self).product(
            product, category, search, **kwargs)
        res.qcontext['pricelist_per_qty'] = {}
        if not http.request.website.user_id:
            return res
        res.qcontext['pricelist_per_qty'] = self.get_promo(
            product, res.qcontext['pricelist'])
        return res

    # @http.route()
    # def shop(self, page=0, category=None, search='', **post):
    #     res = super(WebsiteSale, self).shop(
    #         page=page, category=category, search=search, **post)
    #     if not http.request.website.user_id:
    #         return res
        # product_pricelist_qty = {}
        # for product_tmpl in res.qcontext['products']:
        #     product_pricelist_qty.update(
        #         self.get_promo_qtys(product_tmpl, res.qcontext['pricelist']))
        # res.qcontext['product_pricelist_qty'] = product_pricelist_qty
    #     return res

    def has_promo(self, product, pricelist_id, partner_id=None):
        pricelist = request.env['product.pricelist'].browse(pricelist_id)
        has_qtys = self.pricelist_minimal_qtys(pricelist, product)
        return has_qtys and has_qtys or False

    def pricelist_minimal_qtys(self, pricelist, product):
        def _get_pricelist_version(pricelist):
            date = fields.Datetime.now()
            for v in pricelist.version_id:
                if all([((v.date_start is False) or (v.date_start <= date)),
                        ((v.date_end is False) or (v.date_end >= date))]):
                    return v
            raise exceptions.Warning(
                _('No active version for pricelist %s') % pricelist.name)

        def _check_item(item, product):
            def check_is_parent_categ(item_categ, product_categ):
                if not item_categ or not product_categ:
                    return False
                if item_categ.id == product_categ.id:
                    return True
                if not product_categ.parent_id:
                    return False
                else:
                    return check_is_parent_categ(
                        item_categ, product_categ.parent_id)
            return any([
                check_is_parent_categ(item.categ_id, product.categ_id),
                item.product_tmpl_id.id == product.product_tmpl_id.id,
                item.product_id.id == product.id])
        res = []
        version = _get_pricelist_version(pricelist)
        for item in version.items_id:
            if item.base == -1:
                res += self.pricelist_minimal_qtys(
                    item.base_pricelist_id, product)
            if item.min_quantity != 0 and _check_item(item, product):
                res.append(item.min_quantity)
        return sorted(list(set(res)))

    # @http.route(['/shop/product_prices'], type='json', auth='public',
    #             methods=['post'], website=True)
    # def get_product_prices_per_qty(self, product_id, qtys):
    #     res = []
    #     user_id = request.env['res.users'].browse(request.env.context['uid'])
    #     partner_id = user_id.partner_id
    #     pricelist = partner_id.sudo().property_product_pricelist
    #     product_id = request.env['product.product'].browse(product_id)
    #     prices = set()
    #     symbol = pricelist.currency_id.symbol
    #     for qty in qtys:
    #         item = pricelist.price_rule_get_multi(
    #             products_by_qty_by_partner=[(product_id, qty, partner_id)])
    #         price = item[product_id.id][pricelist.id][0]
    #         price = pricelist.currency_id.round(price)
    #         if price in prices or not price > 0:
    #             continue
    #         prices.add(price)
    #         res.append('%su-%s%s/u' % (qty, price, symbol))
    #     return [res[0]] if (len(qtys) > 1 and len(prices) == 1) else res
