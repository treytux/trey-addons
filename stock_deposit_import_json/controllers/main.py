###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json

from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request


class StockDepositImportJson(http.Controller):
    def create_with_onchange(self, record, values):
        onchange_specs = {
            field_name: '1' for field_name, field in record._fields.items()
        }
        new = record.new(values)
        new._origin = None
        res = {'value': {}, 'warnings': set()}
        for field in record._onchange_spec():
            if onchange_specs.get(field):
                new._onchange_eval(field, onchange_specs[field], res)
        cache = record._convert_to_write(new._cache)
        cache.update(values)
        return record.create(cache)

    def get_partner(self, data):
        partners = request.env['res.partner'].search([
            ('name', '=', data),
            ('type', '=', 'delivery')])
        if not partners:
            raise ValidationError(
                _('Partner with name "%s" not found' % (data)))
        if len(partners) > 1:
            raise ValidationError(
                _('Multiple partners with same name "%s"' % (data)))
        return partners

    def get_product(self, data):
        products = request.env['product.product'].search([
            ('default_code', '=', data),
        ])
        if not products:
            raise ValidationError(
                _('Product with code %s not exist' % data))
        if len(products) > 1:
            raise ValidationError(
                _('Many products with same code %s' % data))
        return products

    def stock_deposit_json_import(self, data):
        stock_deposit = request.env['stock.deposit']
        stock_deposit_line = request.env['stock.deposit.line']
        partner_id = self.get_partner(data['shipping_partner_name'])
        values = {
            'name': data['name'],
            'create_invoice': data['create_invoice'],
            'partner_id': partner_id.id,
            'price_option': data['price_option'],
        }
        deposit = self.create_with_onchange(stock_deposit, values)
        for line in data['line_ids']:
            product = self.get_product(line['default_code'])
            data = {
                'deposit_id': deposit.id,
                'ttype': line['ttype'],
                'product_id': product.id,
                'qty': line['qty'],
                'force_inventory': line['force_inventory'],
            }
            self.create_with_onchange(stock_deposit_line, data)
        deposit.action_confirm()
        return deposit.id

    @http.route(
        ['/stock_deposit/import'],
        type='json', auth='user')
    def stock_deposit_import_json(self, **kw):
        info = json.loads(request.httprequest.data)
        result = self.stock_deposit_json_import(info)
        res = {
            'result': result,
        }
        return res
