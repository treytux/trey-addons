###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    @http.route()
    def shop(
            self, page=0, category=None, search='', min_price=0.0,
            max_price=0.0, ppg=False, product_category=None, **post):
        res = super().shop(
            page=page, category=category, search=search, min_price=min_price,
            max_price=max_price, ppg=ppg, product_category=product_category,
            **post)
        partner_id = request.env.user.partner_id.commercial_partner_id.id
        domain = [
            ('state', '=', 'draft'),
            ('is_abandoned_cart', '=', True),
            ('partner_id', 'child_of', [partner_id]),
        ]
        order = request.website.sale_get_order()
        if order:
            domain.append(('id', '!=', order.id))
        abandoned_carts = request.env['sale.order'].sudo().search(domain)
        res.qcontext['is_abandoned_carts'] = abandoned_carts and True or False
        return res
