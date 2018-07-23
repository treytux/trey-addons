# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from functools import partial
from openerp.addons.website_sale.controllers.main import website_sale
from openerp import http
from openerp.http import request


class WebsiteSale(website_sale):
    def get_discount_price(self, product_id, partner_id):
        env = request.env
        context = request.context
        item_obj = env['product.pricelist.item']
        uom = False
        qty = 1
        price = {}
        if product_id:
            if not context.get('pricelist'):
                pricelist = self.get_pricelist().id
                context['pricelist'] = pricelist
            else:
                pricelist = env['product.pricelist'].browse(
                    context['pricelist']).id
            item_id = item_obj.sudo().get_best_pricelist_item(
                pricelist, product_id=product_id, qty=qty,
                partner_id=partner_id)
            if item_id:
                item = item_obj.browse(item_id)
                price_unit = item.sudo().price_get(
                    product_id, qty, partner_id, uom)[0]
                price = {
                    'lst_price': price_unit,
                    'discount': item.discount,
                    'price': price_unit * (1 - (item.discount / 100)),
                }
        return price

    @http.route()
    def shop(self, page=0, category=None, search='', **post):
        res = super(WebsiteSale, self).shop(
            page=page, category=category, search=search, **post)
        res.qcontext['get_discount_price'] = partial(self.get_discount_price)
        return res

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        res = super(WebsiteSale, self).product(
            product=product, category=category, search=search, **kwargs)
        env = request.env
        user = False
        if request.uid != request.website.user_id.id:
            user = env['res.users'].browse(request.uid)
        discount_price = user and self.get_discount_price(
            product.product_variant_ids[0].id, user.partner_id.id) or {
            'lst_price': product.lst_price, 'discount': 0,
            'price': product.price}
        res.qcontext['discount_price'] = discount_price
        return res

    @http.route()
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        res = super(WebsiteSale, self).cart_update(
            product_id=product_id, add_qty=add_qty, set_qty=set_qty, **kw)
        request.website.sale_get_order(force_create=1).recalculate_prices()
        return res

    @http.route()
    def cart_update_json(
            self, product_id, line_id, add_qty=None, set_qty=None,
            display=True):
        res = super(WebsiteSale, self).cart_update_json(
            product_id=product_id, line_id=line_id, add_qty=add_qty,
            set_qty=set_qty, display=display)
        request.website.sale_get_order(force_create=1).recalculate_prices()
        return res

    @http.route()
    def get_unit_price(
            self, product_ids, add_qty, use_order_pricelist=False, **kw):
        '''
        Se sobrescribe la función y omite la llamada al super para evitar el
        siguiente warning que para la ejecución de la página

        WARNING base_datos openerp.models: Comparing apples and oranges:
        res.partner(4669,) == 1354 (/server/openerp/models.py:5601)

        Esto lo provoca la comparación de la línea 312 en el fichero
        '/server/addons/product/pricelist.py':

        if (not partner) or (seller_id.name.id != partner):

        ya que el valor de 'partner' unas veces es un 'id' y otras un objeto

        El error se podría corregir modificando la línea 375 del fichero
        '/server/addons/product/pricelist.py':

        res_multi = self.price_rule_get_multi(cr, uid, ids,
        products_by_qty_by_partner=[(product, qty, partner)], context=context)

        por

        res_multi = self.price_rule_get_multi(cr, uid, ids,
        products_by_qty_by_partner=[(product, qty, partner and
        isinstance(partner, int) or partner.id)], context=context)

        y la línea 994 del fichero
        '/server/addons/website_sale/controllers/main.py'

        prices = pool['product.pricelist'].price_rule_get_multi(cr, uid,
        [pricelist_id], [(product, add_qty, partner) for
        product in products], context=context)

        por

        prices = pool['product.pricelist'].price_rule_get_multi(cr, uid,
        [pricelist_id], [(product, add_qty, partner and isinstance(partner,
        int) or partner.id)) for product in products], context=context)

        una vez corregidas estas líneas se podria hacer la llamada al super
        de la función para mantener la herencia de forma correcta aunque los
        datos devueltos sean otros
        '''
        env = request.env
        user = False
        if request.uid != request.website.user_id.id:
            user = env['res.users'].browse(request.uid)
        return {product_id: self.get_discount_price(
            product_id, user.partner_id.id)['price']
            for product_id in product_ids}
