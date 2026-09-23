###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import math

import pandas as pd
from odoo import _, fields, models
from odoo.exceptions import ValidationError


class SaleOrderLinesByRefXlsx(models.TransientModel):
    _name = 'sale.order.lines_by_ref.xlsx'
    _description = 'Import sale order line by refs with xlsx'

    def _get_default_sale_order(self):
        return self.env['sale.order'].browse(self._context.get('active_id'))

    sale_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        default=_get_default_sale_order,
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

    def _prepare_sale_line(self, ref):
        def _float(value, default=None):
            try:
                return float(value)
            except Exception:
                return default

        get_param = self.env['ir.config_parameter'].sudo().get_param
        vals = ref.split(get_param('sale_order_lines_by_ref.glue', '/'))
        default_code = vals.pop(0)
        products = self.env['product.product'].search([
            ('sale_ok', '=', True),
            '|',
            ('default_code', '=', default_code),
            ('barcode', '=', default_code),
        ])
        data = {
            'order_id': self.sale_id.id,
            'product_id': products[0].id if products else False,
            'product_uom_qty': 1,
        }
        if vals:
            data['product_uom_qty'] = _float(vals.pop(0), 1)
        if vals:
            price_unit = _float(vals.pop(0))
            if price_unit:
                data['price_unit'] = price_unit
        return default_code, data

    def action_back(self):
        self.step = 0
        return self._reopen_view()

    def _create_with_onchange(self, record, values):
        onchange_specs = {
            field_name: '1' for field_name, field in record._fields.items()
        }
        data = self._add_missing_default_values({})
        data.update(values)
        new = record.new(data)
        new._origin = record
        res = {'value': {}, 'warnings': set()}
        for field in record._onchange_spec():
            if onchange_specs.get(field):
                new._onchange_eval(field, onchange_specs[field], res)
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
                'product_uom_qty': row[2],
            })
        return values

    def _reference_error(self, default_code):
        self._error(_('Ref not exists'), default_code)

    def _get_product_by_ref(self, default_code):
        products = self.env['product.product'].search([
            ('sale_ok', '=', True),
            '|',
            ('default_code', '=', default_code),
            ('barcode', '=', default_code),
        ])
        if not products:
            products = self._reference_error(default_code)
            return products, 0
        return products, False

    def get_customerinfo_domain(self, default_code):
        domain = [('product_code', '=', default_code)]
        if self.sale_id.partner_id == self.sale_id.partner_shipping_id:
            domain.append(('name', '=', self.sale_id.partner_id.id))
        else:
            domain.append('|')
            domain.append(('name', '=', self.sale_id.partner_id.id))
            domain.append(('name', '=', self.sale_id.partner_shipping_id.id))
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
        return products, False

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
                    lambda c: c.name == self.sale_id.partner_shipping_id)
                if customerinfo_filtered:
                    products, price = self.search_product_customerinfo(
                        product_customer.filtered(
                            lambda c: c.name == (
                                self.sale_id.partner_shipping_id)))
                    if price == 0:
                        price = False
                if not products or not customerinfo_filtered:
                    products, price = self.search_product_customerinfo(
                        product_customer.filtered(
                            lambda c: c.name == self.sale_id.partner_id))
                    if price == 0:
                        price = False
        if not products:
            products, price = self._get_product_by_ref(default_code)
        return products, price

    def prepare_sale_line(self, line):
        def _float(value, default=None):
            try:
                return float(value)
            except Exception:
                return default

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
            'product_uom_qty': _float(line['product_uom_qty'], 1)
        }
        if not modules:
            products, price = self._get_product_by_ref(line['product_ref'])
            data['product_id'] = products[0].id if products else False
        else:
            products, price = self._get_product_by_customer_code(
                line['product_ref'])
        data.update({
            'product_id': products[0].id if products else False,
            'price_unit': _float(line['price_unit']) or price,
        })
        if price is False and (math.isnan(line['price_unit']) or fix_price):
            del data['price_unit']
        return line['product_ref'], data

    def action_simulate_import_lines_from_xlsx(self):
        self.ensure_one()
        self.line_ids.unlink()
        sheet = self.read_file_xlsx()
        self.check_file_xlsx(sheet)
        values = self.get_lines_info_from_xlsx(sheet)
        for line in values:
            default_code, data_line = self.prepare_sale_line(line)
            if not data_line['order_id']:
                self._error(
                    _('Must be launch this wizard from sale order'),
                    default_code)
                continue
            if not data_line['product_id']:
                continue
        self.step = 1
        return self._reopen_view()

    def action_import_lines_from_xlsx(self):
        line_obj = self.env['sale.order.line']
        lines = self.env['sale.order.line']
        sheet = self.read_file_xlsx()
        self.check_file_xlsx(sheet)
        values = self.get_lines_info_from_xlsx(sheet)
        for line in values:
            default_code, data_line = self.prepare_sale_line(line)
            if (default_code in self.line_ids.mapped('ref')
                    or not data_line.get('product_id')):
                continue
            lines |= self._create_with_onchange(line_obj, data_line)

    def action_simulate_and_import_lines_from_xlsx(self):
        res = self.action_simulate_import_lines_from_xlsx()
        if not self.line_ids:
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
