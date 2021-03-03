###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    @http.route(
        ['/shop/stock_alert'], type='json', auth='public',
        methods=['POST'], website=True, csrf=False)
    def stock_alert(self, product_id, **post):
        alert = request.env['product.stock.alert'].sudo().search([
            ('partner_id', '=', request.env.user.partner_id.id),
            ('product_id', '=', product_id)], limit=1)
        if alert.exists():
            return json.dumps(True)
        product = request.env['product.product'].browse(product_id)
        if not product.exists():
            return json.dumps(False)
        alert = request.env['product.stock.alert'].sudo().create({
            'partner_id': request.env.user.partner_id.id,
            'product_id': product_id})
        template = request.env.ref(
            'website_sale_stock_alert.product_stock_alert_new_email')
        template.sudo().with_context(
            lang=request.env.user.lang).send_mail(alert.id)
        return json.dumps(True)
