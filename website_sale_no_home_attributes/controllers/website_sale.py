###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    @http.route()
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        if (
            request.httprequest.environ['PATH_INFO'] == '/shop'
                and post.get('attrib')):
            return request.redirect('/shop')
        res = super().shop(
            page=page, category=category, search=search, ppg=ppg, **post)
        if not category:
            res.qcontext['attrib_values'] = []
            res.qcontext['attrib_set'] = []
            res.qcontext['attributes'] = []
        return res
