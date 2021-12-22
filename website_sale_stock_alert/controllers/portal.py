###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class CustomerPortal(CustomerPortal):
    def _get_stock_alerts_domain(self, notified):
        partner_id = request.env.user.sudo().partner_id
        domain = [('partner_id', '=', partner_id.id)]
        if not notified:
            domain += [('notified', '=', False)]
        return domain

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        website = request.env['website'].get_current_website()
        stock_alerts_count = request.env['product.stock.alert'].search_count(
            self._get_stock_alerts_domain(True))
        last_stock_alerts = request.env['product.stock.alert'].search(
            self._get_stock_alerts_domain(False),
            order='create_date desc, id desc',
            limit=website.limit_stock_alert,
        )
        values.update({
            'stock_alerts_count': stock_alerts_count,
            'last_stock_alerts': last_stock_alerts,
        })
        return values

    @http.route(['/my/alerts'], type='http', auth='user', website=True)
    def portal_my_stock_alert(self):
        values = {}
        stock_alerts = request.env['product.stock.alert'].search(
            self._get_stock_alerts_domain(True))
        values.update({
            'page_name': 'alerts',
            'stock_alerts': stock_alerts,
        })
        return request.render(
            'website_sale_stock_alert.portal_my_stock_alerts', values)
