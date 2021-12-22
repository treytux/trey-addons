###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, http
from odoo.addons.http_routing.models.ir_http import slugify
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    @http.route()
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        res = super().shop(
            page=page, category=category, search=search, ppg=ppg, **post)
        if search:
            website = request.env['website'].get_current_website()
            term_length = website.search_history_term_length
            store = website.search_history_store
            search_history = request.env['search.history'].search([
                ('name', '=', search)], limit=1)
            count = res.qcontext['search_count']
            if (
                    not search_history
                    and ((count == 0 and store == 'empty') or store == 'all')):
                products_found = True if count > 0 else False
                sanitized = slugify(search) and [
                    word for word in
                    slugify(search).split('-') if len(word) >= term_length
                ] or []
                sanitized.sort()
                sanitized_search = " ".join(sanitized)
                request.env['search.history'].create({
                    'name': search,
                    'sanitized_search': sanitized_search,
                    'last_update': fields.Date.today(),
                    'products_found': products_found,
                    'searches_count': 1,
                })
            elif search_history:
                search_history.last_date = fields.Date.today()
                search_history.searches_count += 1
                search_history.products_found = True if count > 0 else False
        return res
