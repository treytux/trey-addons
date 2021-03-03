###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from io import BytesIO
import base64
import itertools
import unicodecsv
try:
    import xlsxwriter
except ImportError:
    import logging
    _log = logging.getLogger(__name__)
    _log.debug('Can not import xlsxwriter`.')


class ProductQuantExport(models.TransientModel):
    _name = 'product.quant.export'
    _description = 'Product Quant Export'

    data = fields.Binary(
        string='Generated File',
        filter='*.csv',
    )
    name = fields.Char(
        string='File name',
        compute='_get_file_name',
    )
    format_file = fields.Selection(
        selection=[
            ('csv', 'CSV'),
            ('xls', 'Excel')],
        string='Format type',
        default='xls',
    )
    product_ids = fields.Many2many(
        comodel_name='product.product',
        domain=[('type', '=', 'product')],
        string='Products',
        help='Select a product',
    )
    category_ids = fields.Many2many(
        comodel_name='product.category',
        string='Categories',
        help='Search for all categories and its children',
    )
    location_ids = fields.Many2many(
        comodel_name='stock.location',
        domain=[('usage', 'in', ['internal', 'transit'])],
        required=True,
        string='Locations',
        help='Search for all locations and its children',
    )
    show_zeros = fields.Boolean(
        string='Show products without stock',
    )

    @api.model
    def default_get(self, fields):
        values = super().default_get(fields)
        values['location_ids'] = self.env['stock.warehouse'].search([]).mapped(
            'lot_stock_id.id')
        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids', [])
        if active_model == 'product.product':
            values.update({
                'product_ids': [(6, 0, active_ids)],
            })
        if active_model == 'product.template':
            active_ids = self.env['product.product'].search(
                [('product_tmpl_id', 'in', active_ids)]).ids
            values.update({
                'product_ids': [(6, 0, active_ids)],
            })
        return values

    @api.multi
    def _get_file_name(self):
        self.name = _('product_quant_%s.%s') % (
            fields.Datetime.now(), self.format_file)

    @api.model
    def get_stock_quant_header(self):
        return [
            _('Product'),
            _('Code'),
            _('Category'),
            _('Uom'),
        ]

    @api.model
    def get_stock_quant_lines(self, products, locations):
        recs = []
        for product in products:
            if product.type != 'product':
                continue
            data_dict = {
                _('Product'): product.name,
                _('Code'): product.default_code,
                _('Category'): product.categ_id.name,
                _('Uom'): product.uom_id.name,
            }
            for location in locations:
                quant_groups = self.env['stock.quant'].read_group(
                    [('location_id', 'child_of', [location.id]),
                     ('product_id', '=', product.id)],
                    ['quantity', 'product_id'],
                    ['product_id'])
                mapping = dict(
                    [(quant_group['product_id'][0],
                      quant_group['quantity'])
                     for quant_group in quant_groups])
                if not self.show_zeros and not mapping.get(product.id, 0.0):
                    continue
                data_dict[location.display_name] = mapping.get(product.id, 0.0)
            recs.append(data_dict)
        return recs

    @api.model
    def get_lines(self):
        def parse_val(val):
            if val is None or val is False:
                return ''
            return val

        products = self.get_products()
        header = self.get_stock_quant_header()
        lines = self.get_stock_quant_lines(products, self.location_ids)
        if not lines:
            raise UserError(_('There is no records with selection data.'))
        keys = list(set(
            itertools.chain.from_iterable([c.keys() for c in lines])))
        keys = [k for k in keys if k not in header]
        keys.sort()
        [keys.insert(index, k) for index, k in enumerate(header, 0)]
        return [keys] + [[parse_val(ln.get(k)) for k in keys] for ln in lines]

    @api.model
    def generate_xls(self, lines):
        with BytesIO() as ofile:
            workbook = xlsxwriter.Workbook(ofile, {})
            worksheet = workbook.add_worksheet(_('Quant by Location'))
            for row, line in enumerate(lines):
                for col, data in enumerate(line):
                    worksheet.write(row, col, data)
            workbook.close()
            ofile.seek(0)
            content = base64.encodestring(ofile.read())
        return content

    @api.model
    def generate_csv(self, lines):
        with BytesIO() as ofile:
            keys = lines.pop(0)
            doc = unicodecsv.DictWriter(
                ofile, encoding='utf-8', fieldnames=keys)
            doc.writeheader()
            for line in lines:
                doc.writerow({k: line[index] for index, k in enumerate(keys)})
            content = base64.encodestring(ofile.getvalue())
        return content

    @api.model
    def get_products(self):
        products_allowed = []
        if self.category_ids:
            products_allowed = self.env['product.template'].search(
                [('categ_id', 'child_of', self.category_ids.ids)])
        if self.product_ids:
            if products_allowed:
                return self.product_ids.filtered(
                    lambda x: x.product_tmpl_id.id in products_allowed.ids)
            else:
                return self.product_ids
        return self.env['product.product'].search([])

    @api.multi
    def button_accept(self):
        lines = self.get_lines()
        generate = getattr(self, 'generate_%s' % self.format_file)
        self.write({'data': generate(lines)})
        res = self.env['ir.model.data'].get_object_reference(
            'sale_stock_quant_available_xls',
            'product_quant_export_ok_form')
        return {
            'name': _('Product Quant Export'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res and res[1] or False],
            'res_model': 'product.quant.export',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new'}
