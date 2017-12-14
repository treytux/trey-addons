# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.addons.website_sale.controllers.main import website_sale


class WebsiteSaleSnippetController(website_sale):
    @http.route([
        '/website_sale_snippets/custom_list/render'
    ], type='http', auth='public', website=True)
    def render_custom_list(self, **post):
        env = request.env

        template = 'website_sale_snippets.custom_list_items'
        limit = post.get('limit', 0)
        limit = None if limit == 0 else int(limit)
        list_id = post.get('list_id', None)
        list_id = list_id if not list_id else int(list_id)
        image_size = post.get('image_size', 'default')

        response = self.shop()
        values = {}
        if response.qcontext:
            values = response.qcontext
            values['image_size'] = image_size
            ctx = request.context.copy()
            if not ctx.get('pricelist'):
                ctx['pricelist'] = (
                    values.get('pricelist')
                    if values.get('pricelist') else self.get_pricelist())
            domain = [('custom_list_id', '=', list_id)]
            order = 'sequence, name'
            custom_list_lines = env['custom.list.line'].with_context(
                ctx).sudo().search(domain, limit=limit, order=order)
            products = []
            if custom_list_lines:
                for l in custom_list_lines:
                    products.append(l.product_tmpl_id)
            values['products'] = products

        return request.website.render(template, values)
