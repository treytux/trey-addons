# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _
from cStringIO import StringIO
from datetime import datetime
import base64
import unicodecsv


class AccountPickingExport(models.TransientModel):
    _name = 'wiz.stock_picking_export'
    _description = 'Stock picking export'

    @api.multi
    def _get_file_name(self):
        self.file_name = _('picking_%s.csv') % fields.Datetime.now()

    name = fields.Char(
        string='Name')
    ffile = fields.Binary(
        string='File',
        filter='*.csv')
    file_name = fields.Char(
        string='File name',
        compute=_get_file_name)

    def format_date(self, date):
        return datetime.strptime(
            date, '%Y-%m-%d %H:%M:%S').date().strftime('%d/%m/%Y')

    def format_number(self, number):
        if isinstance(number, (bool, str)):
            number = 0.
        return str('%.2f' % number).replace('.', ',')

    def encoded_rows(self, dictionary, doc):
        for row in sorted(dictionary):
            encoded_row = []
            for col in dictionary[row]:
                if isinstance(col, unicode):
                    encoded_row.append(col)
                elif isinstance(col, float):
                    encoded_row.append(self.format_number(col))
                else:
                    encoded_row.append(col)
            doc.writerow(encoded_row)

    @api.multi
    def picking_writer(self, picking):
        ofile = StringIO()
        doc = unicodecsv.writer(ofile, encoding='utf-8')
        for picking in picking:
            self.write_picking(picking, doc)
        content = base64.encodestring(ofile.getvalue())
        ofile.close()
        return content

    @api.multi
    def get_header_picking(self, picking, doc):
        header_dict = {
            1: [
                _('Stock Picking'), picking.name or ''],
            2: [
                _('Date'), picking.date and
                self.format_date(picking.date) or ''],
            3: [],
            4: [_('Customer number'), picking.partner_id.ref or ''],
            5: [_('Name'), picking.partner_id.name],
            6: [
                _('Address'), '%s %s' % (
                    picking.partner_id.street and
                    picking.partner_id.street or '',
                    picking.partner_id.zip or '')],
            7: [
                _('Location'), picking.partner_id.city or ''],
            8: [
                _('State'), picking.partner_id.state_id and
                picking.partner_id.state_id.name or ''],
            9: [
                _('Country'), picking.partner_id.country_id and
                picking.partner_id.country_id.name or ''],
            10: [
                _('Phone'), picking.partner_id.phone or ''],
            11: [
                _('Fax'), picking.partner_id.fax or ''],
            12: [
                _('Email'), picking.partner_id.email or ''],
            13: []}
        self.encoded_rows(header_dict, doc)
        current_row = max(header_dict, key=header_dict.get) + 1
        return current_row

    @api.multi
    def get_picking_lines(self, picking, table_dict, current_row):
        table_dict.update({
            current_row: [
                _('Reference'), _('Description'), _('Size'),
                _('Variant'), _('Quantity')]})
        current_row += 1
        row_by_tmpl = {}
        for line in picking.move_lines:
            product_tmpl_id = line.product_id
            ref = line.product_id and line.product_id.name_template or ''
            description = (
                line.product_id and '%s %s' % (
                    line.product_id.name_template,
                    line.product_id.description_sale and
                    line.product_id.description_sale or '') or line.name)
            size = (line.product_id.attribute_value_ids and
                    line.product_id.attribute_value_ids[0].name) or ''
            variant = (line.product_id.attribute_value_ids and
                       line.product_id.attribute_value_ids[1].name) or ''
            row_vals = [
                ref, description, size, variant, line.product_uom_qty]
            if product_tmpl_id not in row_by_tmpl:
                row_by_tmpl[product_tmpl_id] = row_vals
                table_dict[current_row] = row_by_tmpl[product_tmpl_id]
                current_row += 1
        current_row += 1
        table_dict[current_row] = ''
        current_row += 1
        return table_dict, current_row

    @api.multi
    def get_table_picking(self, picking, doc, current_row):
        table_dict = {}
        table_dict, current_row = self.get_picking_lines(
            picking, table_dict, current_row)
        self.encoded_rows(table_dict, doc)
        return current_row

    @api.multi
    def put_separator(self, separator_rows, doc, current_row):
        separator_dict = {}
        for sep in range(0, separator_rows):
            separator_dict.update({current_row: []})
            current_row += 1
        self.encoded_rows(separator_dict, doc)
        return current_row

    @api.multi
    def write_picking(self, picking, doc):
        current_row = self.get_header_picking(picking, doc)
        current_row = self.get_table_picking(picking, doc, current_row)
        separator_rows = 3
        current_row = self.put_separator(separator_rows, doc, current_row)

    @api.multi
    def button_accept(self):
        assert self.ids, _('IDs do not exist.')
        assert self.env.context['active_model'] == 'stock.picking', _(
            'Active model is not a stock picking!')
        active_ids = self.env.context.get('active_ids', [])
        picking = self.env['stock.picking'].browse(active_ids)
        content = self.picking_writer(picking)
        self.write({'ffile': content})
        res = self.env['ir.model.data'].get_object_reference(
            'stock_picking_export',
            'stock_picking_export_ok_wizard')
        res_id = res and res[1] or False
        return {
            'name': _('Stock picking export'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'wiz.stock_picking_export',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new'}
