# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _
import StringIO
import csv
import base64


class ProductExportStockByLocation(models.TransientModel):
    _name = 'wiz.product_export_stock_by_location'
    _description = 'Product export stock by location'

    @api.multi
    def _get_file_name(self):
        self.file_name = _('product_stock_%s.csv') % fields.Datetime.now()

    name = fields.Char(
        string='Name')
    ffile = fields.Binary(
        string='File',
        filter='*.csv')
    file_name = fields.Char(
        string='File name',
        compute=_get_file_name)
    is_internal = fields.Boolean(
        string='Only internal locations',
        default=True,
        help="If it is checked, it will only consider the company's internal "
             "locations.")

    def format_number(self, number):
        if isinstance(number, (bool, str)):
            return number
        try:
            return ('%.2f' % (number)).replace('.', ',')
        except Exception:
            return ('%.2f' % number).replace('.', ',')

    def encoded_rows(self, value_list, doc):
        encoded_row = []
        for col in value_list:
            if isinstance(col, unicode):
                encoded_row.append(col.encode('utf-8'))
            elif isinstance(col, float):
                encoded_row.append(self.format_number(col))
            else:
                encoded_row.append(col)
        doc.writerow(encoded_row)

    def add_row(self, table_dict, current_row, value_list):
        table_dict.update({current_row: value_list})
        current_row += 1
        return table_dict, current_row

    def write_file(self, table_dict):
        ofile = StringIO.StringIO()
        a = csv.writer(
            ofile, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
        for k, v in table_dict.iteritems():
            self.encoded_rows(v, a)
        content = ofile.getvalue()
        return base64.encodestring(content)

    @api.multi
    def button_accept(self):
        assert self.ids, _('IDs do not exist.')
        location_obj = self.env['stock.location']
        table_dict = {}
        current_row = 0
        table_dict, current_row = self.add_row(
            table_dict, current_row, ['', _('Product'), _('Quantity On Hand')])
        domain = self.is_internal and [('usage', '=', 'internal')] or []
        locations = location_obj.search(domain)
        for location in locations:
            child_locations = location_obj.search([
                ('location_id', 'child_of', location.id)])
            child_locations_ids = ', '.join([
                str(i) for i in child_locations.ids])
            table_dict, current_row = self.add_row(
                table_dict, current_row,
                ['%s %s' % (_('LOCATION'), location.complete_name)])
            self.env.cr.execute('''
                SELECT pp.default_code, pp.name_template, sum(q.qty)
                FROM stock_quant AS q
                LEFT JOIN product_product AS pp ON pp.id = q.product_id
                WHERE q.location_id IN (%s)
                GROUP BY pp.name_template, pp.default_code
                ORDER BY pp.name_template, pp.default_code''' % (
                child_locations_ids))
            for row in self.env.cr.fetchall():
                if row[2] > 0.0:
                    table_dict, current_row = self.add_row(
                        table_dict, current_row,
                        [_(''), '%s%s' % (row[0] and ('[%s] ' % row[0]) or '',
                         row[1]), row[2]])
        content = self.write_file(table_dict)
        self.write({'ffile': content})
        res = self.env['ir.model.data'].get_object_reference(
            'product_export_stock_by_location',
            'wiz_product_export_stock_by_location_ok')
        res_id = res and res[1] or False
        return {
            'name': _('Product stock exporter'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'wiz.product_export_stock_by_location',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new'}
