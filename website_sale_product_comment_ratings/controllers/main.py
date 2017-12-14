# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import openerp.addons.website_sale.controllers.main as website_sale
from openerp.http import request, route


class WebsiteSale(website_sale.website_sale):

    @route()
    def product_comment(self, product_template_id, **post):
        ctx = request.context.copy()
        ctx['comment_ratings_rate'] = post.get('rating_selector', '0')
        request.context = ctx
        return super(WebsiteSale, self).product_comment(
            product_template_id, **post)

    @route()
    def product(self, product, category='', search='', **kwargs):
        res = super(WebsiteSale, self).product(
            product, category=category, search=search, **kwargs)
        has_rated = False
        if request.session.uid:
            for message in product.website_message_ids:
                if (message.message_rate and
                        message.create_uid.id == request.session.uid):
                    has_rated = True
        res.qcontext['has_rated'] = has_rated
        return res
