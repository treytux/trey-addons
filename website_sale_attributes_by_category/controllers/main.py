###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request
from werkzeug.exceptions import NotFound


class WebsiteSale(WebsiteSale):
    def _keep_category_attributes(self, category):
        if not category:
            return False
        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [
            [int(x) for x in v.split('-')] for v in attrib_list if v]
        category_attributes = [
            True for v in attrib_values
            if v[0] in category.attribute_ids.ids]
        return len(category_attributes) > 0 and all(category_attributes)

    def _get_search_domain(self, search, category, attrib_values):
        return super()._get_search_domain(
            search,
            category,
            self._keep_category_attributes(category) and attrib_values or None,
        )

    def _unkeep_category_attributes(self, res):
        res.qcontext['attrib_values'] = []
        res.qcontext['attrib_set'] = []
        return res

    @http.route()
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        res = super().shop(
            page=page, category=category, search=search, ppg=ppg, **post)
        if request.httprequest.environ['PATH_INFO'] == '/shop':
            return self._unkeep_category_attributes(res)
        if not category:
            return self._unkeep_category_attributes(res)
        res.qcontext['attributes'] = []
        res.qcontext['keep'] = QueryURL(
            '/shop', category=category and int(category), search=search)
        env = request.env
        current_category = env['product.public.category'].search([
            ('id', '=', int(category))], limit=1)
        if (
                not current_category
                or not current_category.can_access_from_current_website()):
            raise NotFound()
        product_attributes = env['product.attribute'].with_context(
            request.context)
        res.qcontext['attributes'] = product_attributes.sudo().browse(
            current_category.attribute_ids.ids)
        if not self._keep_category_attributes(current_category):
            res = self._unkeep_category_attributes(res)
        return res

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        res = super().product(
            product, category=category, search=search, **kwargs)
        if not category:
            return res
        current_category = request.env['product.public.category'].browse(
            int(category)).exists()
        res.qcontext['keep'] = QueryURL(
            '/shop',
            category=current_category and current_category.id,
            search=search,
        )
        return res
