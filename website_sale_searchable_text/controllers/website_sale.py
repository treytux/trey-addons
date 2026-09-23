###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.osv import expression


class WebsiteSale(WebsiteSale):
    def _add_search_subdomains_hook(self, search):
        domain = super()._add_search_subdomains_hook(search)
        extra = [('searchable_text', 'ilike', search)]
        if domain:
            return expression.OR([domain, extra])
        return extra
