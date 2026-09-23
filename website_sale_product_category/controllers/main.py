###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import QueryURL, WebsiteSale
from odoo.http import request
from odoo.osv import expression


class WebsiteSale(WebsiteSale):
    def _get_search_options(
            self, category=None, attrib_values=None, pricelist=None,
            min_price=0.0, max_price=0.0, conversion_rate=1, **post):
        res = super()._get_search_options(
            category=category, attrib_values=attrib_values,
            pricelist=pricelist, min_price=min_price, max_price=max_price,
            conversion_rate=conversion_rate, **post)
        res['product_category'] = request.context.get('categ_id')
        return res

    def _get_search_domain(
            self, search, category, attrib_values, search_in_description=True):
        domain = super()._get_search_domain(
            search, category, attrib_values,
            search_in_description=search_in_description)
        if 'categ_id' in request.context:
            domain = expression.AND(
                [domain, [('categ_id', '=', request.context['categ_id'])]]
            )
        return domain

    def _get_product_category_domain(self, post):
        domain = []
        if post.get('search'):
            domain += [('name', 'ilike', post.get('search'))]
        return domain

    @http.route()
    def shop(
            self, page=0, category=None, search='', min_price=0.0,
            max_price=0.0, ppg=False, product_category=None, **post):
        if product_category:
            context = dict(request.context)
            context.setdefault('categ_id', int(product_category))
            request.update_context(**context)
        return super().shop(
            page=page, category=category, search=search, min_price=min_price,
            max_price=max_price, ppg=ppg, product_category=product_category,
            **post)

    @http.route(
        ['/page/product-categories'], type='http', auth='public', website=True)
    def product_categories_page(self, **post):
        category_obj = request.env['product.public.category']
        domain = self._get_product_category_domain(post)
        product_categories = category_obj.sudo().search(domain)
        keep = QueryURL('/page/product-categories', categ_id=[])
        values = {
            'product_categories': product_categories,
            'keep': keep,
        }
        if post.get('search'):
            values.update({
                'search': post.get('search'),
            })
        return request.render(
            'website_sale_product_category.product_categories', values)
