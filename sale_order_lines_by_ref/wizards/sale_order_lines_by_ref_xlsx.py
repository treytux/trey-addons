###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import math

import pandas as pd
import xlsxwriter
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import code_translations


class SaleOrderLinesByRefXlsx(models.TransientModel):
    _name = 'sale.order.lines_by_ref.xlsx'
    _description = 'Import sale order line by refs with xlsx'

    sale_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade',
    )
    line_ids = fields.One2many(
        comodel_name='sale.order.lines_by_ref.xlsx.message',
        inverse_name='wizard_id',
        string='Messages',
    )
    step = fields.Integer(
        string='Wizard steps',
    )
    xlsx_file = fields.Binary(
        string='XLSX file',
        help='XLSX file to add lines to sale order',
    )
    fallback_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Fallback product',
        domain=[('sale_ok', '=', True)],
        help='If a product reference is not found, use this product and keep '
             'the imported reference as the sale order line description.',
    )

    def _template_sheet_name(self):
        return _('Import Template')

    def _template_instruction_sheet_name(self):
        return _('Instructions')

    def _template_filename(self):
        return _('Product Import Template') + '.xlsx'

    def _template_instructions(self):
        return [
            _('Fill in the data starting from Row 2.'),
            _('For \'Product reference\', use the Internal Reference or '
              'External ID.'),
            _('Leave \'Price unit\' empty to use the default price.'),
        ]

    def action_provide_template_xlsx(self):
        headers = [label for _, label in self._xlsx_columns()]
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet(self._template_sheet_name())
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center',
            'font_color': '#000000',
            'border': 1,
            'font_size': 11,
        })
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        worksheet.freeze_panes(1, 0)
        for col, header in enumerate(headers):
            width = max(len(header) + 4, 14)
            worksheet.set_column(col, col, min(width, 40))
        instruction_sheet = workbook.add_worksheet(
            self._template_instruction_sheet_name())
        for row, line in enumerate(self._template_instructions()):
            instruction_sheet.write(row, 0, line)
        workbook.close()
        output.seek(0)
        xlsx_data = output.read()
        attachment = self.env['ir.attachment'].create({
            'name': self._template_filename(),
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
            'datas': base64.b64encode(xlsx_data),
            'mimetype': 'application/vnd.openxmlformats'
                        '-officedocument.spreadsheetml.sheet',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'new',
        }

    def _xlsx_columns(self):
        return [
            ('product_ref', _('Product reference')),
            ('price_unit', _('Price unit')),
            ('product_uom_qty', _('Product quantity')),
        ]

    def _xlsx_column_sources(self):
        return [
            ('product_ref', 'Product reference'),
            ('price_unit', 'Price unit'),
            ('product_uom_qty', 'Product quantity'),
        ]

    def _header_map(self):
        header_map = {}
        installed_langs = self.env['res.lang'].get_installed()
        lang_codes = {code for code, _name in installed_langs}
        if self.env.context.get('lang'):
            lang_codes.add(self.env.context['lang'])
        module_name = 'sale_order_lines_by_ref'
        for key, source in self._xlsx_column_sources():
            header_map[self._normalize_header(source)] = key
            for lang_code in lang_codes:
                label = code_translations.get_python_translations(
                    module_name, lang_code).get(source, source)
                header_map[self._normalize_header(label)] = key
        return header_map

    def _normalize_header(self, value):
        return str(value).strip().casefold()

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res_ids = self.env.context.get('order_id')
        res['sale_id'] = res_ids
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
        data = record._add_missing_default_values({})
        data.update(values)
        new = record.new(data)
        for _name, methods in record._onchange_methods.items():
            for method in methods:
                method(new)
        cache = new._convert_to_write(new._cache)
        cache.update(values)
        return record.create(cache)

    def check_file_xlsx(self, sheet):
        if sheet.shape[0] == 0:
            raise ValidationError(_('No rows in file'))
        if sheet.shape[1] != 3:
            raise ValidationError(_('The file must have 3 columns'))
        header_map = self._header_map()
        normalized_columns = [self._normalize_header(c) for c in sheet.columns]
        mapped_columns = {
            header_map.get(column) for column in normalized_columns}
        expected_columns = {key for key, _label in self._xlsx_columns()}
        if None in mapped_columns or mapped_columns != expected_columns:
            raise ValidationError(
                _('Invalid column names. Expected: %s') %
                ', '.join(label for _, label in self._xlsx_columns())
            )
        return True

    def read_file_xlsx(self):
        try:
            buf = io.BytesIO()
            buf.write(base64.b64decode(self.xlsx_file))
            buf.seek(0)
            df = pd.read_excel(buf)
        except Exception:
            raise ValidationError(_('Invalid file!'))
        return df

    def get_lines_info_from_xlsx(self, sheet):
        rename_map = {}
        header_map = self._header_map()
        for col in sheet.columns:
            normalized = self._normalize_header(col)
            if normalized in header_map:
                rename_map[col] = header_map[normalized]
        sheet = sheet.rename(columns=rename_map)
        values = []
        for _row_index, row in sheet.iterrows():
            values.append({
                'product_ref': row['product_ref'],
                'price_unit': row['price_unit'],
                'product_uom_qty': row['product_uom_qty'],
            })
        return values

    def _reference_error(self, default_code):
        self._error(_('Ref not exists'), default_code)

    def _reference_warning(self, default_code):
        self._warning(
            _('Ref not exists. The fallback product will be used.'),
            default_code)

    def _warning(self, message, ref):
        self.ensure_one()
        self.line_ids.create({
            'type': 'warning',
            'wizard_id': self.id,
            'name': message,
            'ref': ref,
        })

    def _get_product_by_ref(self, default_code):
        products = self.env['product.product'].search([
            ('sale_ok', '=', True),
            '|',
            ('default_code', '=', default_code),
            ('barcode', '=', default_code),
        ])
        return products, False

    def get_customerinfo_domain(self, default_code):
        domain = [('product_code', '=', default_code)]
        if self.sale_id.partner_id == self.sale_id.partner_shipping_id:
            domain.append(('partner_id', '=', self.sale_id.partner_id.id))
        else:
            domain.append('|')
            domain.append(('partner_id', '=', self.sale_id.partner_id.id))
            domain.append((
                'partner_id', '=', self.sale_id.partner_shipping_id.id))
        return domain

    def search_product_customerinfo(self, customerinfos):
        products = self.env['product.product']
        for customerinfo in customerinfos:
            if customerinfo.product_id:
                return customerinfo.product_id, customerinfo.price
            elif customerinfo.product_tmpl_id.product_variant_id:
                return (
                    customerinfo.product_tmpl_id.product_variant_id,
                    customerinfo.price)
        return products

    def _get_product_by_customer_code(self, default_code):
        products = self.env['product.product']
        price = 0
        product_customer = self.env['product.customerinfo'].search(
            self.get_customerinfo_domain(default_code))
        if product_customer:
            if self.sale_id.partner_id == self.sale_id.partner_shipping_id:
                products, price = self.search_product_customerinfo(
                    product_customer)
                if price == 0:
                    price = False
            else:
                customerinfo_filtered = product_customer.filtered(
                    lambda c: c.partner_id == self.sale_id.partner_shipping_id)
                if customerinfo_filtered:
                    products, price = self.search_product_customerinfo(
                        product_customer.filtered(
                            lambda c: c.partner_id == (
                                self.sale_id.partner_shipping_id)))
                    if price == 0:
                        price = False
                if not products or not customerinfo_filtered:
                    products, price = self.search_product_customerinfo(
                        product_customer.filtered(
                            lambda c: c.partner_id == self.sale_id.partner_id))
                    if price == 0:
                        price = False
        else:
            products, price = self._get_product_by_ref(default_code)
        return products, price

    def _float(self, value, default=None):
        try:
            return float(value)
        except Exception:
            return default

    def _prepare_fallback_sale_line(self, line):
        data = {
            'order_id': self.sale_id.id,
            'product_id': self.fallback_product_id.id,
            'product_uom_qty': self._float(line['product_uom_qty'], 1),
            'name': line['product_ref'],
        }
        price_unit = self._float(line['price_unit'])
        if price_unit is not None:
            data['price_unit'] = price_unit
        return line['product_ref'], data, True

    def prepare_sale_line(self, line):
        modules = self.env['ir.module.module'].sudo().search([
            ('name', '=', 'product_supplierinfo_for_customer_sale'),
            ('state', '=', 'installed'),
        ])
        fix_price = False
        if math.isnan(line['price_unit']):
            line['price_unit'] = 0.0
            fix_price = True
        data = {
            'order_id': self.sale_id.id,
            'product_uom_qty': self._float(line['product_uom_qty'], 1)
        }
        if not modules:
            products, price = self._get_product_by_ref(line['product_ref'])
        else:
            products, price = self._get_product_by_customer_code(
                line['product_ref'])
        if not products and self.fallback_product_id:
            return self._prepare_fallback_sale_line(line)
        data.update({
            'product_id': products[0].id if products else False,
            'price_unit': self._float(line['price_unit']) or price,
        })
        if price is False and (math.isnan(line['price_unit']) or fix_price):
            del data['price_unit']
        return line['product_ref'], data, False

    def action_simulate_import_lines_from_xlsx(self):
        self.ensure_one()
        self.line_ids.unlink()
        sheet = self.read_file_xlsx()
        self.check_file_xlsx(sheet)
        values = self.get_lines_info_from_xlsx(sheet)
        for line in values:
            default_code, data_line, used_fallback = self.prepare_sale_line(
                line)
            if not data_line['order_id']:
                self._error(
                    _('This wizard must be launched from sale order'),
                    default_code)
                continue
            if used_fallback:
                self._reference_warning(default_code)
                continue
            if not data_line['product_id']:
                self._reference_error(default_code)
                continue
        self.step = 1
        return self._reopen_view()

    def action_import_lines_from_xlsx(self):
        line_obj = self.env['sale.order.line']
        lines = self.env['sale.order.line']
        sheet = self.read_file_xlsx()
        self.check_file_xlsx(sheet)
        values = self.get_lines_info_from_xlsx(sheet)
        error_refs = self.line_ids.filtered(
            lambda line: line.type == 'error').mapped('ref')
        for line in values:
            default_code, data_line, _used_fallback = (
                self.prepare_sale_line(line))
            if default_code in error_refs:
                continue
            lines |= self._create_with_onchange(line_obj, data_line)

    def action_simulate_and_import_lines_from_xlsx(self):
        res = self.action_simulate_import_lines_from_xlsx()
        if not self.line_ids.filtered(lambda line: line.type == 'error'):
            self.action_import_lines_from_xlsx()
            return
        return res


class SaleOrderLinesByRefMessage(models.TransientModel):
    _name = 'sale.order.lines_by_ref.xlsx.message'
    _description = 'Message for import sale order line by refs with xlsx'
    _order = 'ref'

    wizard_id = fields.Many2one(
        comodel_name='sale.order.lines_by_ref.xlsx',
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
