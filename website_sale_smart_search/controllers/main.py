# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import openerp
from openerp import http
from openerp.http import request
from datetime import datetime, timedelta
import logging
_log = logging.getLogger(__name__)


DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


class WebSiteSaleAdvancedSearch(http.Controller):
    @http.route(['/smart-search/search'],
                type='json', auth='public', website=True)
    def search(self, search):
        def _get_results(search, products=None):
            context, env, website = (request.context, request.env,
                                     request.website)
            if not products:
                products = env['product.template'].sudo().search(
                    ['|', '|', '|', '|',
                     ('name', 'ilike', search),
                     ('searchable_text', 'ilike', search),
                     ('description', 'ilike', search),
                     ('description_sale', 'ilike', search),
                     ('product_variant_ids.default_code', 'ilike', search),
                     ('website_published', '=', True)],
                    limit=website.results_limit,
                    order='website_sequence desc').with_context(context)
            else:
                products = env['product.template'].sudo().search(
                    [('id', 'in', products.ids),
                     ('website_published', '=', True)],
                    limit=website.results_limit,
                    order='website_sequence desc').with_context(context)
            categories = {}
            for p in products:
                for c in p.public_categ_ids:
                    if c.id in categories.keys():
                        categories[c.id]['products'] += 1
                    else:
                        categories.update({
                            c.id: {'id': c.id, 'name': c.name, 'products': 1}})
            return products, categories

        def _get_pricelist():
            context, env = request.context, request.env
            partner = env.user.partner_id
            sale_order = context.get('sale_order')
            if sale_order:
                pricelist = sale_order.pricelist_id
            else:
                pricelist = partner.property_product_pricelist
            if not pricelist:
                _log.error(
                    'Fail to find pricelist for partner "%s" (id %s)',
                    partner.name, partner.id)
            return pricelist

        def _get_products_info(products, pricelist):
            return [{
                'id': p.id,
                'publish': ('on' if p.website_published else 'off'),
                'name': p.name,
                'description': (
                    p.description_sale if p.description_sale else ''),
                'price': p.price,
                'lst_price': p.lst_price,
                'currency': pricelist.currency_id.symbol}
                for p in products]

        def _get_banner(search):
            banner_obj = request.env['suggestion.banner']
            banners = banner_obj.search([('term_ids.name', 'ilike', search)])
            if banners:
                return {'id': banners[0].id, 'href': banners[0].href}
            banner_defaults = banner_obj.search([('default', '=', True)])
            if not banner_defaults:
                return None
            return {'id': banner_defaults[0].id,
                    'href': banner_defaults[0].href}

        def _format_results(search, products, pricelist, categories):
            return {
                'products': (_get_products_info(
                    products, pricelist) if products else []),
                'categories': categories.values(),
                'banner': _get_banner(search)}

        context, env = request.context, request.env
        cache_search = request.env['cache.search'].search(
            [('name', '=', search)], limit=1)
        if not context.get('pricelist'):
            pricelist = _get_pricelist()
            context['pricelist'] = int(pricelist)
        else:
            pricelist = env('product.pricelist').browse(
                context['pricelist'])
        if not cache_search:
            products, categories = _get_results(search)
            results = _format_results(search, products, pricelist, categories)
            env['cache.search'].create({
                'name': search,
                'searches': 1,
                'result_product_ids': [(6, 0, products.ids)],
                'last_cache_update': datetime.now().strftime(DATETIME_FORMAT)})
            return results
        create_date = datetime.strptime(
            cache_search['last_cache_update'],
            openerp.tools.misc.DEFAULT_SERVER_DATETIME_FORMAT)
        in_time = (datetime.now() - create_date) < timedelta(
            hours=request.website.expiry_time)
        if cache_search['custom_results'] or in_time:
            products, categories = _get_results(
                search, cache_search.result_product_ids)
            results = _format_results(search, products, pricelist, categories)
            cache_search.write({'searches': cache_search.searches + 1})
            return results
        products, categories = _get_results(search)
        results = _format_results(search, products, pricelist, categories)
        cache_search.write({
            'searches': cache_search.searches + 1,
            'result_product_ids': [(6, 0, products.ids)],
            'last_cache_update': datetime.now().strftime(DATETIME_FORMAT)})
        return results

    @http.route(
        ['/smart-search/hit'], type='json', auth='public', website=True)
    def hit(self, url, search):
        obj = request.env['cache.search'].search([('name', '=', search)])
        if obj:
            obj[0].write({'clicks': obj[0].clicks + 1})
