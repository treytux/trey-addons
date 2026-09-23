###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json

from odoo import http
from odoo.addons.website_sale_stock.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteSale(WebsiteSale):
    @http.route(
        ['/product/stock/available/<string:id>'], type='http',
        auth="public", website=True)
    def product_public_stock(self, id, **kw):
        values = {}
        try:
            id = int(id)
        except Exception:
            values['Error'] = 'ID must be Integer'
            return json.dumps(values)
        product = request.env['product.product'].sudo().browse(id)
        if not product.exists():
            values['Error'] = 'ID not found'
            return json.dumps(values)
        if product.inventory_availability == 'never':
            values['qty_available'] = 9999
        elif product.inventory_availability == 'always':
            values['qty_available'] = product.qty_available
        elif product.inventory_availability == 'threshold':
            if product.qty_available < product.available_threshold:
                values['qty_available'] = product.qty_available
            else:
                values['qty_available'] = 9999
        elif product.inventory_availability == 'custom':
            values['qty_available'] = product.qty_available
            values['custom_message'] = product.custom_message
        return json.dumps(values)
