###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import binascii
import io
import os
import tempfile

import openpyxl
import xlrd
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PurchaseOrderLinesByRefXls(models.TransientModel):
    _name = 'purchase.order.lines_by_ref.xls'
    _description = 'Wizard to create purchase order lines by refs with xls'

    purchase_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase Order',
        required=True,
        ondelete='cascade',
    )
    line_ids = fields.One2many(
        comodel_name='purchase.order.lines_by_ref.xls.message',
        inverse_name='wizard_id',
        string='Messages',
    )
    step = fields.Integer(
        string='Wizard steps',
    )
    xls_file = fields.Binary(
        string='XLS/XLSX file',
        help='XLS or XLSX file to add lines to purchase order',
    )
    xls_filename = fields.Char(
        string='Filename',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res['purchase_id'] = self.env.context.get(
            'order_id', self.env.context.get(
                'active_id', False))
        return res

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

    def check_file(self, sheet):
        if self._get_sheet_nrows(sheet) == 0:
            raise ValidationError(_('No rows in file'))
        if self._get_sheet_ncols(sheet) != 3:
            raise ValidationError(_('The file must have 3 columns'))
        cols_name = []
        for i in range(self._get_sheet_ncols(sheet)):
            cols_name.append(self._get_sheet_cell_value(sheet, 0, i))
        if cols_name[0] != _('Product reference') or (
                cols_name[1] != _('Price unit')) or (
                    cols_name[2] != _('Product quantity')):
            raise ValidationError('The columns are not in order')
        return True

    def read_file(self):
        filecontent = binascii.a2b_base64(self.xls_file)
        extension = os.path.splitext(self.xls_filename or '')[1].lower()
        if extension == '.xls':
            return self._read_file_xls(filecontent)
        if extension == '.xlsx':
            return self._read_file_xlsx(filecontent)
        raise ValidationError(_('Invalid file!'))

    def _read_file_xls(self, filecontent):
        fp = tempfile.NamedTemporaryFile(delete=True, suffix='.xls')
        fp.write(filecontent)
        fp.seek(0)
        workbook = xlrd.open_workbook(fp.name)
        return workbook.sheet_by_index(0)

    def _read_file_xlsx(self, filecontent):
        try:
            workbook = openpyxl.load_workbook(
                io.BytesIO(filecontent), read_only=True, data_only=True)
            return list(workbook.worksheets[0].iter_rows(values_only=True))
        except Exception:
            raise ValidationError(_('Invalid file!'))

    def get_lines_info_from_file(self, sheet):
        values = []
        for row in range(1, self._get_sheet_nrows(sheet)):
            if not self._get_sheet_cell_value(sheet, row, 0):
                continue
            values.append({
                'product_ref': self._get_sheet_reference_value(sheet, row, 0),
                'price_unit': self._get_sheet_text_value(sheet, row, 1),
                'product_qty': self._get_sheet_text_value(sheet, row, 2),
            })
        return values

    def _get_sheet_nrows(self, sheet):
        if hasattr(sheet, 'nrows'):
            return sheet.nrows
        return len(sheet)

    def _get_sheet_ncols(self, sheet):
        if hasattr(sheet, 'ncols'):
            return sheet.ncols
        return sum(
            1 for c in sheet[0] if c is not None and str(c).strip() != '')

    def _get_sheet_cell_value(self, sheet, row, col):
        if hasattr(sheet, 'cell_value'):
            return sheet.cell_value(row, col)
        if row >= len(sheet) or col >= len(sheet[row]):
            return ''
        value = sheet[row][col]
        return '' if value is None else value

    def _get_sheet_text_value(self, sheet, row, col):
        return str(self._get_sheet_cell_value(sheet, row, col)).strip()

    def _get_sheet_reference_value(self, sheet, row, col):
        value = self._get_sheet_cell_value(sheet, row, col)
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        return str(value).strip()

    def _reference_error(self, default_code):
        self._error(_('Ref not exists'), default_code)

    def _normalize_numeric_code(self, code):
        value = str(code or '').strip()
        if value.endswith('.0') and value[:-2].isdigit():
            return value[:-2]
        return value

    def _find_product_by_barcode_numeric_equivalence(self, default_code):
        normalized = self._normalize_numeric_code(default_code)
        if not normalized.isdigit():
            return self.env['product.product']
        normalized = normalized.lstrip('0') or '0'
        products = self.env['product.product'].search([
            ('purchase_ok', '=', True),
            ('barcode', '!=', False),
        ])
        return products.filtered(
            lambda p: str(p.barcode).strip().lstrip('0') == normalized)

    def _get_product_by_ref(self, default_code):
        default_code = self._normalize_numeric_code(default_code)
        products = self.env['product.product'].search([
            ('purchase_ok', '=', True),
            '|',
            ('default_code', '=', default_code),
            ('barcode', '=', default_code),
        ])
        if not products:
            products = self._find_product_by_barcode_numeric_equivalence(
                default_code)
        if not products:
            products = self._reference_error(default_code)
        return products

    def get_supplierinfo_domain(self, default_code):
        default_code = self._normalize_numeric_code(default_code)
        return [
            ('product_code', '=', default_code),
            ('partner_id', '=', self.purchase_id.partner_id.id),
        ]

    def get_supplierinfo_product_domain(self, products):
        return [
            ('partner_id', '=', self.purchase_id.partner_id.id),
            ('product_id', '=', products[0].id),
        ]

    def get_supplierinfo_product_tmpl_domain(self, products):
        return [
            ('partner_id', '=', self.purchase_id.partner_id.id),
            ('product_tmpl_id', '=', products[0].product_tmpl_id.id),
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
        data = {
            'order_id': self.purchase_id.id,
            'product_id': products[0].id if products else False,
            'price_unit': _float(line['price_unit']),
            'product_qty': _float(line['product_qty'], 1),
        }
        if not line['price_unit']:
            products_supplier = self.env['product.supplierinfo'].search(
                self.get_supplierinfo_domain(line['product_ref']))
            if not products_supplier and products:
                products_supplier = self.env['product.supplierinfo'].search(
                    self.get_supplierinfo_product_domain(products))
            if not products_supplier and products:
                products_supplier = self.env['product.supplierinfo'].search(
                    self.get_supplierinfo_product_tmpl_domain(products))
            if products_supplier:
                data['price_unit'] = products_supplier[0].price
        return line['product_ref'], data

    def action_simulate_import_lines_from_xls(self):
        self.ensure_one()
        self.line_ids.unlink()
        sheet = self.read_file()
        self.check_file(sheet)
        values = self.get_lines_info_from_file(sheet)
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

    def action_import_lines_from_xls(self):
        line_obj = self.env['purchase.order.line']
        lines = self.env['purchase.order.line']
        sheet = self.read_file()
        self.check_file(sheet)
        values = self.get_lines_info_from_file(sheet)
        for line in values:
            default_code, data_line = self.prepare_purchase_line(line)
            if default_code in self.line_ids.mapped('ref'):
                continue
            lines |= self._create_with_onchange(line_obj, data_line)

    def action_simulate_and_import_lines_from_xls(self):
        res = self.action_simulate_import_lines_from_xls()
        if not self.line_ids:
            self.action_import_lines_from_xls()
            return
        return res


class PurchaseOrderLinesByRefMessage(models.TransientModel):
    _name = 'purchase.order.lines_by_ref.xls.message'
    _description = 'Message for import purchase order line by refs with xls'
    _order = 'ref'

    wizard_id = fields.Many2one(
        comodel_name='purchase.order.lines_by_ref.xls',
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
