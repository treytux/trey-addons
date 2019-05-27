###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleSearchTrim(WebsiteSale):
    @http.route()
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        return super().shop(
            page=page, category=category, search=search.strip(), ppg=ppg,
            **post)
