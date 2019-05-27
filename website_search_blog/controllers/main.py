###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.http import request
from odoo.addons.website_search.controllers.main import WebsiteSearch


class WebsiteBlogSearch(WebsiteSearch):

    def _get_blog_search_domain(self, search):
        domain = []
        if search:
            for srch in search.split(' '):
                domain += [
                    '|', ('name', 'ilike', srch),
                    ('content', 'ilike', srch),
                    ('website_published', '=', True)]
        return domain

    def _get_search_results(self, search):
        res = super(WebsiteBlogSearch, self)._get_search_results(search=search)
        res['posts'] = request.env['blog.post'].search(
            self._get_blog_search_domain(search))
        return res
