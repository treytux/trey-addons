###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json
import logging
import os
from datetime import datetime

from odoo import http
from odoo.http import request
from odoo.tools import config

_logger = logging.getLogger(__name__)


class SaleOrderImportJson(http.Controller):

    def _save_json_error(self, json_data, error, operation_type='import'):
        try:
            data_dir = config.filestore(request.env.cr.dbname)
            error_dir = os.path.join(
                data_dir, 'sale_order_import_json_error')
            if not os.path.exists(error_dir):
                os.makedirs(error_dir)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            filename = os.path.join(
                error_dir, '{}_{}.json'.format(operation_type, timestamp))
            with open(filename, 'w') as f:
                json.dump({
                    'data': json_data,
                    'error': str(error),
                    'timestamp': timestamp,
                }, f, indent=2)
            _logger.error(
                'JSON import error saved to %s: %s', filename, error)
        except Exception as e:
            _logger.error('Failed to save error JSON: %s', e)

    @http.route(
        ['/sale_order/import'],
        type='json', auth='user')
    def sale_order_import_json(self, **kw):
        json_data = None
        try:
            json_data = json.loads(request.httprequest.data)
            result = request.env['sale.order'].sudo(
                user=request.env.user).with_context(
                    login_user=request.env.user).json_import(json_data)
            res = {
                'result': result,
            }
            return json.dumps(res)
        except Exception as e:
            if json_data:
                self._save_json_error(json_data, e, 'import')
            raise

    @http.route(
        ['/sale_order/create_invoice'],
        type='json', auth='user')
    def create_invoice_json(self, **kw):
        json_data = None
        try:
            json_data = json.loads(request.httprequest.data)
            result = request.env['sale.order'].sudo(
                user=request.env.user).with_context(
                    login_user=request.env.user).json_import_create_invoice(
                        json_data)
            res = {
                'result': result,
            }
            return json.dumps(res)
        except Exception as e:
            if json_data:
                self._save_json_error(json_data, e, 'create_invoice')
            raise
