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
        res['product_location'] = request.context.get('location_id')
        return res

    def _get_search_domain(
            self, search, category, attrib_values, search_in_description=True):
        domain = super()._get_search_domain(
            search, category, attrib_values,
            search_in_description=search_in_description)
        if 'location_id' in request.context:
            product_ids = request.env['stock.quant'].search([
                ('location_id', '=', request.context['location_id']),
            ])
            domain = expression.AND(
                [domain, [(
                    'id', 'in', product_ids.mapped('product_id').ids)]]
            )
        return domain

    def _get_product_location_domain(self, post):
        domain = [
            ('website_published', '=', True),
            ('child_ids', '=', False),
        ]
        if post.get('search'):
            domain += [('name', 'ilike', post.get('search'))]
        return domain

    @http.route(
        [
            '/shop',
            '/shop/page/<int:page>',
            '/shop/category/<model("product.public.category"):category>',
            '/shop/category/<model("product.public.category"):category'
            '>/page/<int:page>',
            '/shop/product-location',
        ],
        type='http', auth='public', website=True)
    def shop(
            self, page=0, category=None, search='', min_price=0.0,
            max_price=0.0, ppg=False, product_location=None, **post):
        res = super().shop(
            page=page, category=category, search=search, min_price=min_price,
            max_price=max_price, ppg=ppg, product_location=product_location,
            **post)
        res.qcontext['location'] = False
        if product_location:
            res.qcontext['location'] = request.env[
                'stock.location'].browse(int(product_location))
            context = dict(request.context)
            context.setdefault('location_id', int(product_location))
            request.update_context(**context)
        return res

    @http.route(
        ['/page/product-locations'], type='http', auth='public', website=True)
    def product_locations_page(self, **post):
        location_obj = request.env['stock.location']
        domain = self._get_product_location_domain(post)
        product_locations = location_obj.sudo().search(domain)
        keep = QueryURL('/page/product-locations', location_id=[])
        values = {
            'product_locations': product_locations,
            'keep': keep,
        }
        if post.get('search'):
            values.update({
                'search': post.get('search'),
            })
        return request.render(
            'website_sale_product_location.product_locations', values)
