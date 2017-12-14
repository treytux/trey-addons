# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

import openerp.addons.website_sale.controllers.main as main
from openerp import http
from openerp.http import request
import logging

_log = logging.getLogger(__name__)


class WebsiteSale(main.website_sale):
    @http.route(['/shop/product/<model("product.template"):product>'],
                type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        r = super(WebsiteSale, self).product(product, category, search,
                                             **kwargs)
        cr, uid, context, pool = request.cr, request.uid, request.context, \
            request.registry
        # añadimos el listado de categorias
        category_obj = pool['product.public.category']
        category_ids = category_obj.search(cr, uid, [], context=context)
        categories = category_obj.browse(cr, uid, category_ids,
                                         context=context)
        categs = filter(lambda x: not x.parent_id, categories)
        r.qcontext['categories'] = categs

        return r

    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>'
        '/page/<int:page>'
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', **post):

        # ajustando productos por pagina
        # _log.info("PRODUCTOS POR PAGINA {}"
        #     .format(request.website.shop_products_per_page))

        return super(WebsiteSale, self).shop(page=page, category=category,
                                             search=search, **post)
