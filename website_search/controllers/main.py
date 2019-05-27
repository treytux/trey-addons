##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website


class WebsiteSearch(Website):

    def _get_search_domain(self, search):
        domain = []
        if search:
            for srch in search.split(' '):
                domain += [
                    '|',
                    ('name', 'ilike', srch),
                    ('arch_db', 'ilike', srch)]
        return domain

    def _get_search_results(self, search):
        pages = request.env['website.page'].search(
            self._get_search_domain(search))
        return {'pages': pages.filtered(lambda x: x.is_visible)}

    @http.route(
        ['/search', '/search/page/<int:page>'],
        type='http', auth='public', website=True)
    def search_results(self, page=1, sorting='date', search='', **post):
        values = self._get_search_results(search)
        values['search'] = search
        return request.render('website_search.search_results', values)
