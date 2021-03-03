###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    @http.route()
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        website = request.env['website'].get_current_website()
        ppg_config = website.ppg_values
        values = []
        if ppg_config is not False:
            values = [
                int(number) for number in
                ppg_config.split(',') if number.isdigit()
            ]
        ppg_value = request.params.get('ppg')
        res = super().shop(page=page, category=category, search=search,
                           ppg=ppg_value, **post)
        attrib_list = request.httprequest.args.getlist('attrib')
        res.qcontext['ppg_values'] = values
        order = post.get('order')
        keep = QueryURL('/shop', category=category and int(category),
                        search=search, attrib=attrib_list,
                        order=order, ppg=ppg_value)
        res.qcontext['keep'] = keep
        return res
