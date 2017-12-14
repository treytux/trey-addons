# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
import openerp.addons.website_sale.controllers.main as main
from openerp import http
from openerp.http import request
import logging

_log = logging.getLogger(__name__)


class WebsiteSale(main.website_sale):

    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/'
        '<int:page>'
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', **post):
        result = super(WebsiteSale, self).shop(
            page=page, category=category, search=search, **post)

        wl = request.env['wishlist'].sudo().search([
            ('website_id', '=', request.website.id),
            ('user_id', '=', request.uid)
        ], limit=1)
        result.qcontext['wishlist_products'] = [l.product_tmpl_id.id
                                                for l in wl.line_ids]
        return result

    @http.route(['/shop/product/<model("product.template"):product>'],
                type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        result = super(WebsiteSale, self).product(
            product, category=category, search=search, **kwargs)
        wl = request.env['wishlist'].sudo().search([
            ('website_id', '=', request.website.id),
            ('user_id', '=', request.uid)
        ], limit=1)
        tmpl_products = [l.product_tmpl_id.id for l in wl.line_ids]
        result.qcontext['in_wishlist'] = bool(product.id in tmpl_products)
        return result


class WebsiteSaleWishlist(http.Controller):

    @http.route(['/shop/wishlist'], type='http', auth='public',
                methods=['GET'], website=True)
    def wishlist_list(self):
        """
        Obtiene la lista de deseos para un usuario en el sitio web indicado
        """
        env = request.env
        wl = env['wishlist'].sudo().search([
            ('website_id', '=', request.website.id),
            ('user_id', '=', request.uid)
        ], limit=1)
        return request.website.render(
            'website_sale_wishlist.layout',
            {'wishlist': len(wl) > 0 and wl[0] or wl})

    @http.route(['/shop/wishlist/add'], type='json', auth='public',
                methods=['POST'], website=True)
    def wishlist_set(self, product_tmpl_id):
        """
        Añade un producto a la lista de deseos del usuario en el sitio web
        indicado
        """
        env = request.env
        wl = env['wishlist'].sudo().search([
            ('website_id', '=', request.website.id),
            ('user_id', '=', request.uid)
        ], limit=1)
        if not wl:
            wl = wl.sudo().create({
                'website_id': request.website.id,
                'user_id': request.uid,
            })
        else:
            wl = wl[0]

        exist_product_id = [l.product_tmpl_id.id for l in wl.line_ids]
        for product_id in [int(p) for p in product_tmpl_id.split(',')]:
            if product_id not in exist_product_id:
                env['wishlist.line'].sudo().create({
                    'wishlist_id': wl.id,
                    'product_tmpl_id': product_id
                })

        return {
            'user_id': request.uid,
            'website_id': request.website.id,
            'product_tmpl_id': product_tmpl_id
        }

    @http.route(['/shop/wishlist/remove'], type='json', auth='public',
                methods=['POST'], website=True)
    def wishlist_remove(self, line_id):
        """
        Elimina un producto de la lista de deseos del usuario en el sitio web
        indicado
        """
        response = {}
        env = request.env
        try:
            line = env['wishlist.line'].browse(int(line_id))
            if line and line.wishlist_id.user_id.id == request.uid \
               and line.wishlist_id.website_id.id == request.website.id:
                response['line_id'] = line_id
                response['product_tmpl_id'] = line.product_tmpl_id.id
                if line.wishlist_id.line_ids == 1:
                    response['empty'] = True
                line.unlink()
        except Exception as e:
            _log.error(
                'Remove wishlist line, don\'t exist line id: %s , %s' % (
                    line_id, e))
            response['error'] = ('Remove wishlist line, don\'t exist '
                                 'line id: %s , %s' % (line_id, e))
            response['empty'] = False

        return response

    @http.route(['/shop/wishlist/empty'], type='json', auth='public',
                methods=['POST'], website=True)
    def wishlist_empty(self):
        """
        Vacia la lista de deseos del usuario en el sitio web indicado
        """
        env = request.env
        wl = env['wishlist'].sudo().search([
            ('website_id', '=', request.website.id),
            ('user_id', '=', request.uid)
        ], limit=1)
        if wl:
            wl.unlink()
            return {'response': True}
        return {'response': False}

    @http.route(['/shop/wishlist/to_cart'], type='json',
                auth='public', methods=['POST'], website=True)
    def wishlist_to_cart(self):
        env = request.env
        wl = env['wishlist'].sudo().search([
            ('website_id', '=', request.website.id),
            ('user_id', '=', request.uid)
        ], limit=1)

        lines_added = []
        for line in wl.line_ids:
            if len(line.product_tmpl_id.product_variant_ids) == 1:
                request.website.sale_get_order(force_create=1)._cart_update(
                    product_id=line.product_tmpl_id.product_variant_ids[0].id,
                    add_qty=1)
                lines_added.append(line.id)
                line.unlink()

        return {
            'lines_added': lines_added,
            'empty': lines_added == len(wl.line_ids) and True or False
        }
