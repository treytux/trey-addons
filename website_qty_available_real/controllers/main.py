###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.website_sale.controllers import main  # type:ignore
from odoo.http import request, route


class WebsiteSale(main.WebsiteSale):

    def _get_search_domain(self, search, category, attrib_values):
        domain = super()._get_search_domain(
            search=search, category=category, attrib_values=attrib_values)
        if not request.session.get('filter_stock'):
            return domain
        template_obj = request.env['product.template'].sudo()
        product_tmpl_stock_ids = (
            template_obj._search_qty_available_real_website('>', 0))
        domain += [('id', 'in', product_tmpl_stock_ids)]
        return domain

    @route()
    def shop(self, page=1, category=None, search='', ppg=False, **post):
        if request.httprequest.method == 'POST':
            request.session['filter_stock'] = 'filter_stock' in post or False
        return super(WebsiteSale, self).shop(
            page=page, category=category, search=search, ppg=ppg, **post)
