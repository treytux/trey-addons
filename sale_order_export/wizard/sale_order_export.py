# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _
from cStringIO import StringIO
from datetime import datetime
import base64
import unicodecsv


class AccountorderExport(models.TransientModel):
    _name = 'wiz.sale_order_export'
    _description = 'Sale order export'

    @api.multi
    def _get_file_name(self):
        self.file_name = _('sale_order_%s.csv') % fields.Datetime.now()

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
    def order_writer(self, order):
        ofile = StringIO()
        doc = unicodecsv.writer(ofile, encoding='utf-8')
        for order in order:
            self.write_order(order, doc)
        content = base64.encodestring(ofile.getvalue())
        ofile.close()
        return content

    @api.multi
    def get_header_order(self, order, doc):
        header_dict = {
            1: [
                _('Sale order'), order.name or ''],
            2: [
                _('Date'), order.date_order and
                self.format_date(order.date_order) or ''],
            3: [],
            4: [_('Customer number'), order.partner_id.ref or ''],
            5: [_('Name'), order.partner_id.name],
            6: [
                _('Address'), '%s %s' % (
                    order.partner_id.street and
                    order.partner_id.street or '',
                    order.partner_id.zip or '')],
            7: [
                _('Location'), order.partner_id.city or ''],
            8: [
                _('State'), order.partner_id.state_id and
                order.partner_id.state_id.name or ''],
            9: [
                _('Country'), order.partner_id.country_id and
                order.partner_id.country_id.name or ''],
            10: [
                _('Phone'), order.partner_id.phone or ''],
            11: [
                _('Fax'), order.partner_id.fax or ''],
            12: [
                _('Email'), order.partner_id.email or ''],
            13: []}
        self.encoded_rows(header_dict, doc)
        current_row = max(header_dict, key=header_dict.get) + 1
        return current_row

    @api.multi
    def get_order_lines(self, order, table_dict, current_row):
        table_dict.update({
            current_row: [
                _('Reference'), _('Description'), _('Variant'),
                _('Size'), _('Price Unit'), _('Quantity'), _('Total')]})
        current_row += 1
        row_by_tmpl = {}
        for line in order.order_line:
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
                ref, description, size, variant,
                line.price_unit, line.product_uom_qty, line.price_subtotal]
            if product_tmpl_id not in row_by_tmpl:
                row_by_tmpl[product_tmpl_id] = row_vals
                table_dict[current_row] = row_by_tmpl[product_tmpl_id]
                current_row += 1
        current_row += 1
        table_dict[current_row] = ''
        current_row += 1
        return table_dict, current_row

    @api.multi
    def get_order_totals(self, order, table_dict, current_row):
        table_dict.update({
            current_row: [
                '', '', '', '', '', _('Untaxed amount'),
                order.amount_untaxed],
            current_row + 1: [
                '', '', '', '', '', _('Amount tax'), order.amount_tax],
            current_row + 2: [
                '', '', '', '', '', _('Amount total'), order.amount_total],
            current_row + 3: []})
        current_row += 4
        return table_dict, current_row

    @api.multi
    def get_order_taxes(self, order, table_dict, current_row):
        table_dict.update({
            current_row: [_('Name'), _('Base'), _('Amount')]})
        current_row += 1
        for tax_line in order.tax_line:
            table_dict.update({
                current_row: [tax_line.name, tax_line.base, tax_line.amount]})
            current_row += 1
        table_dict.update({current_row: []})
        current_row += 1
        return table_dict, current_row

    @api.multi
    def get_table_order(self, order, doc, current_row):
        table_dict = {}
        table_dict, current_row = self.get_order_lines(
            order, table_dict, current_row)
        table_dict, current_row = self.get_order_totals(
            order, table_dict, current_row)
        self.encoded_rows(table_dict, doc)
        return current_row

    @api.multi
    def get_footer_order(self, order, doc, current_row):
        footer_dict = {
            current_row: [
                _('Payment mode'), order.payment_mode_id and
                order.payment_mode_id.name or ''],
            current_row + 1: [
                _('Payment term'), order.payment_term and
                order.payment_term.name or ''],
            current_row + 2: [_('Maturity'), order.date_max_shipping],
            current_row + 3: [
                _('Agents name'), order.agents_name and
                order.agents_name or ''],
            current_row + 4: [_('Total units'), order.total_qty]}
        self.encoded_rows(footer_dict, doc)
        current_row = max(footer_dict, key=footer_dict.get) + 1
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
    def write_order(self, order, doc):
        current_row = self.get_header_order(order, doc)
        current_row = self.get_table_order(order, doc, current_row)
        current_row = self.get_footer_order(order, doc, current_row)
        separator_rows = 3
        current_row = self.put_separator(separator_rows, doc, current_row)

    @api.multi
    def button_accept(self):
        assert self.ids, _('IDs do not exist.')
        assert self.env.context['active_model'] == 'sale.order', _(
            'Active model is not a sale order!')
        active_ids = self.env.context.get('active_ids', [])
        order = self.env['sale.order'].browse(active_ids)
        content = self.order_writer(order)
        self.write({'ffile': content})
        res = self.env['ir.model.data'].get_object_reference(
            'sale_order_export',
            'sale_order_export_ok_wizard')
        res_id = res and res[1] or False
        return {
            'name': _('Sale order export'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'wiz.sale_order_export',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new'}
