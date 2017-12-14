# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import http
from openerp.http import request
import logging

_log = logging.getLogger(__name__)


class WebsiteSaleProductComparison(http.Controller):

    @http.route(['/shop/product_comparison'], type='http', auth='public',
                methods=['GET'], website=True)
    def product_comparison_list(self):
        """
        Obtiene la lista de comparaciones para un usuario en el sitio web
        indicado
        """
        env = request.env
        pcl = env['product.comparison'].sudo().search([
            ('website_id', '=', request.website.id),
            ('user_id', '=', request.uid)
        ], limit=1)
        return request.website.render(
            'website_sale_product_comparison.layout',
            {'product_comparison': len(pcl) > 0 and pcl[0] or pcl})

    @http.route(['/shop/product_comparison/add'], type='http', auth='public',
                methods=['GET'], website=True)
    def comparison_set(self, product_tmpl_id):
        """
        Añade un producto a la lista de comparacion del usuario en el sitio web
        indicado
        """
        env = request.env
        cpl = env['product.comparison'].sudo().search([
            ('website_id', '=', request.website.id),
            ('user_id', '=', request.uid)
        ], limit=1)
        if not cpl:
            cpl = cpl.sudo().create({
                'website_id': request.website.id,
                'user_id': request.uid}
            )
        else:
            cpl = cpl[0]
        templates_received = [int(p) for p in product_tmpl_id.split(',')]
        total_templates = len(templates_received) + len(cpl.line_ids)
        if total_templates <= request.website.shop_products_per_comparison:
            exist_product_id = [l.product_tmpl_id.id for l in cpl.line_ids]
            for template_id in templates_received:
                if template_id not in exist_product_id:
                    env['product.comparison.line'].sudo().create({
                        'comparison_id': cpl.id,
                        'product_tmpl_id': template_id}
                    )
        else:
            _log.error('Maximo numero de articulos a comparar alcanzado')

    @http.route(['/shop/product_comparison/remove'], type='http',
                auth='public', methods=['POST'], website=True)
    def comparison_remove(self, line_id):
        """
        Elimina un producto de la lista de comparacion del usuario en el
        sitio web indicado
        """
        env = request.env
        try:
            line = env['product.comparison.line'].browse(int(line_id))
            if line and line.comparison_id.user_id.id == request.uid:
                line.unlink()
                env['product.comparison'].sudo().search([
                    ('website_id', '=', request.website.id),
                    ('user_id', '=', request.uid)], limit=1
                )
        except Exception as e:
            _log.error(
                'Remove comparison line, don\'t exist line id: %s , %s' % (
                    line_id, e)
            )

    @http.route(['/shop/product_comparison/empty'], type='http',
                auth='public', methods=['GET'], website=True)
    def comparison_empty(self, comparison_id):
        """
        Vacia la lista de comparacion del usuario en el sitio web indicado
        """
        env = request.env
        try:
            cpl = env['product.comparison'].browse(int(comparison_id))
            if cpl and cpl.user_id.id == request.uid:
                cpl.unlink()
        except Exception as e:
            _log.error(
                'Empty comparison, don\'t exist id: %s , %s' % (
                    comparison_id, e))
