###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import math

import pandas as pd
from odoo import _, fields, models
from odoo.exceptions import ValidationError


class PurchaseOrderLinesByRefXlsx(models.TransientModel):
    _name = 'purchase.order.lines_by_ref.xlsx'
    _description = 'Wizard to create purchase order lines by refs with xlsx'

    def _get_default_purchase_order(self):
        return self.env['purchase.order'].browse(self._context.get('active_id'))

    purchase_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase Order',
        default=_get_default_purchase_order,
        required=True,
        ondelete='cascade',
    )
    line_ids = fields.One2many(
        comodel_name='purchase.order.lines_by_ref.xlsx.message',
        inverse_name='wizard_id',
        string='Messages',
    )
    step = fields.Integer(
        string='Wizard steps',
    )
    xlsx_file = fields.Binary(
        string='XLSX file',
        help='XLSX file to add lines to purchase order',
    )

    def _reopen_view(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.ids[0],
            'res_model': self._name,
            'target': 'new',
            'context': {},
        }

    def _error(self, message, ref):
        self.ensure_one()
        self.line_ids.create({
            'wizard_id': self.id,
            'name': message,
            'ref': ref,
        })

    def action_back(self):
        self.step = 0
        return self._reopen_view()

    def _create_with_onchange(self, record, values):
        onchange_specs = {
            field_name: '1' for field_name, field in record._fields.items()
        }
        data = record._add_missing_default_values({})
        data.update(values)
        new = record.new(data)
        new._origin = record
        res = {
            'value': {},
            'warnings': set(),
        }
        for field in record._onchange_spec():
            if onchange_specs.get(field):
                new._onchange_eval(field, onchange_specs[field], res)
                new.update(data)
        cache = record._convert_to_write(new._cache)
        cache.update(values)
        return record.create(cache)

    def check_file_xlsx(self, sheet):
        if sheet.shape[0] == 0:
            raise ValidationError(_('No rows in file'))
        if sheet.shape[1] != 3:
            raise ValidationError(_('The file must have 3 columns'))
        return True

    def read_file_xlsx(self):
        try:
            buf = io.BytesIO()
            buf.write(base64.b64decode(self.xlsx_file))
            df = pd.read_excel(
                buf, engine='xlrd', encoding='utf-8',
                converters={
                    _('Product reference'): str,
                    _('Price unit'): float,
                    _('Product quantity'): int,
                })
        except Exception:
            raise ValidationError(_('Invalid file!'))
        return df

    def get_lines_info_from_xlsx(self, sheet):
        values = []
        for _index, row in sheet.iterrows():
            values.append({
                'product_ref': row[0],
                'price_unit': row[1],
                'product_qty': row[2],
            })
        return values

    def _reference_error(self, default_code):
        self._error(_('Ref not exists'), default_code)

    def _get_product_by_ref(self, default_code):
        products = self.env['product.product'].search([
            ('purchase_ok', '=', True),
            '|',
            ('default_code', '=', default_code),
            ('barcode', '=', default_code),
        ])
        if not products:
            products = self._reference_error(default_code)
        return products

    def get_supplierinfo_domain(self, default_code):
        return [
            ('product_code', '=', default_code),
            ('name', '=', self.purchase_id.partner_id.id),
        ]

    def search_product_supplierinfo(self, supplierinfos):
        products = self.env['product.product']
        for supplierinfo in supplierinfos:
            if supplierinfo.product_id:
                return supplierinfo.product_id
            elif supplierinfo.product_tmpl_id.product_variant_id:
                return supplierinfo.product_tmpl_id.product_variant_id
        return products

    def _get_product_by_supplier_code(self, default_code):
        products = self.env['product.product']
        product_supplier = self.env['product.supplierinfo'].search(
            self.get_supplierinfo_domain(default_code))
        if product_supplier:
            products = self.search_product_supplierinfo(product_supplier)
        else:
            products = self._get_product_by_ref(default_code)
        return products

    def prepare_purchase_line(self, line):
        def _float(value, default=None):
            try:
                return float(value)
            except Exception:
                return default

        products = self._get_product_by_supplier_code(line['product_ref'])
        if math.isnan(line['price_unit']):
            line['price_unit'] = 0.0
        data = {
            'order_id': self.purchase_id.id,
            'product_id': products[0].id if products else False,
            'price_unit': _float(line['price_unit']),
            'product_qty': _float(line['product_qty'], 1),
        }
        if not line['price_unit']:
            products_supplier = self.env['product.supplierinfo'].search(
                self.get_supplierinfo_domain(line['product_ref']))
            if products_supplier:
                if products_supplier[0].price == 0:
                    data['price_unit'] = (
                        products_supplier[0].product_id.standard_price or (
                            products_supplier[0].product_tmpl_id.standard_price)
                    )
                else:
                    data['price_unit'] = products_supplier[0].price
            else:
                supplierinfos = products[0].seller_ids.filtered(
                    lambda sp: sp.name == self.purchase_id.partner_id)
                if not supplierinfos or not supplierinfos[0].price:
                    data['price_unit'] = (
                        products[0].standard_price if products else 0)
                else:
                    data['price_unit'] = supplierinfos[0].price
        return line['product_ref'], data

    def action_simulate_import_lines_from_xlsx(self):
        self.ensure_one()
        self.line_ids.unlink()
        sheet = self.read_file_xlsx()
        self.check_file_xlsx(sheet)
        values = self.get_lines_info_from_xlsx(sheet)
        for line in values:
            default_code, data_line = self.prepare_purchase_line(line)
            if not data_line['order_id']:
                self._error(
                    _('Must be launch this wizard from purchase order'),
                    default_code)
                continue
            if not data_line['product_id']:
                continue
        self.step = 1
        return self._reopen_view()

    def action_import_lines_from_xlsx(self):
        line_obj = self.env['purchase.order.line']
        lines = self.env['purchase.order.line']
        sheet = self.read_file_xlsx()
        self.check_file_xlsx(sheet)
        values = self.get_lines_info_from_xlsx(sheet)
        for line in values:
            default_code, data_line = self.prepare_purchase_line(line)
            if default_code in self.line_ids.mapped('ref'):
                continue
            lines |= self._create_with_onchange(line_obj, data_line)

    def action_simulate_and_import_lines_from_xlsx(self):
        res = self.action_simulate_import_lines_from_xlsx()
        if not self.line_ids:
            self.action_import_lines_from_xlsx()
            return
        return res


class PurchaseOrderLinesByRefMessage(models.TransientModel):
    _name = 'purchase.order.lines_by_ref.xlsx.message'
    _description = 'Message for import purchase order line by refs with xlsx'
    _order = 'ref'

    wizard_id = fields.Many2one(
        comodel_name='purchase.order.lines_by_ref.xlsx',
        string='Wizard',
    )
    type = fields.Selection(
        selection=[
            ('error', 'Error'),
            ('warning', 'Warning'),
        ],
        string='Type',
        default='error',
    )
    name = fields.Char(
        string='Message',
        required=True,
    )
    ref = fields.Char(
        string='Reference',
        required=True,
    )
