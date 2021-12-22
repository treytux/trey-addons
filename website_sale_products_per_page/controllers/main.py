###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    @http.route()
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        res = super().shop(
            page=page, category=category, search=search, ppg=ppg, **post)
        res.qcontext['ppg'] = ppg
        website = request.env['website'].get_current_website()
        ppg_config = website.ppg_values
        res.qcontext['ppg_values'] = ppg_config and [
            int(value) for value in
            ppg_config.split(',') if value.isdigit()
        ] or []
        return res
