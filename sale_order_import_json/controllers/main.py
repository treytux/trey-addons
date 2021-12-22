###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json

from odoo import http
from odoo.http import request


class SaleOrderImportJson(http.Controller):
    @http.route(
        ['/sale_order/import'],
        type='json', auth='user')
    def sale_order_import_json(self, **kw):
        info = json.loads(request.httprequest.data)
        result = request.env['sale.order'].sudo().json_import(info)
        res = {
            'result': result,
        }
        return json.dumps(res)
