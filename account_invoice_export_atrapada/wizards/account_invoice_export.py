# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, _
import StringIO
import csv
import base64
from datetime import datetime


class AccountInvoiceExport(models.TransientModel):
    _name = 'wiz.account_invoice_export'
    _description = 'Account invoice export'

    @api.multi
    def _get_file_name(self):
        self.file_name = _('invoice_%s.csv') % fields.Datetime.now()

    name = fields.Char(
        string='Name')
    ffile = fields.Binary(
        string='File',
        filter='*.csv')
    file_name = fields.Char(
        string='File name',
        compute=_get_file_name)

    ttypes = {
        'out_refund': _('Refund Invoice'),
        'out_invoice': _('Invoice'),
        'in_invoice': _('Supplier Invoice'),
        'in_refund': _('Supplier Refund Invoice')}
    name_by_states = {
        'draft': _('Draft'),
        'proforma': _('Proform'),
        'proforma2': _('Proform'),
        'open': ttypes,
        'paid': ttypes}

    def format_date(self, date):
        return datetime.strptime(date, '%Y-%m-%d').date().strftime('%d/%m/%Y')

    def format_number(self, number):
        if isinstance(number, (bool, str)):
            return number
        try:
            return ('%.2f' % (number)).replace('.', ',')
        except Exception:
            return ('%.2f' % number).replace('.', ',')

    def get_invoice_name(self, invoice):
        if invoice.state not in self.name_by_states:
            return ''
        if isinstance(self.name_by_states[invoice.state], dict):
            return self.name_by_states[invoice.state][invoice.type]
        return self.name_by_states[invoice.state]

    def get_maturity(self, invoice):
        if (
                invoice.state not in ('open', 'paid') or not
                invoice.move_id.exists()):
            return ''
        move_lines = self.env['account.move.line'].search([
            ('move_id', '=', invoice.move_id.id),
            ('account_id.type', 'in', ['receivable', 'payable'])],
            order='date_maturity')
        if not move_lines.exists():
            return ''
        payment_dates = ''
        for move_line in move_lines:
            payment_dates += '%s %s: %s %s\n' % (
                self.format_date(move_line.date_maturity),
                _('Amount to pay: '), str(abs(move_line.amount_to_pay)),
                u'\u20AC')
        return payment_dates

    def encoded_rows(self, dictionary, doc):
        for row in sorted(dictionary):
            encoded_row = []
            for col in dictionary[row]:
                if isinstance(col, unicode):
                    encoded_row.append(col.encode('utf-8'))
                elif isinstance(col, float):
                    encoded_row.append(self.format_number(col))
                else:
                    encoded_row.append(col)
            doc.writerow(encoded_row)

    @api.multi
    def invoices_writer(self, invoices):
        ofile = StringIO.StringIO()
        doc = csv.writer(
            ofile, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
        for invoice in invoices:
            self.write_invoice(invoice, doc)
        content = base64.encodestring(ofile.getvalue())
        ofile.close()
        return content

    @api.multi
    def get_header_invoice(self, invoice, doc):
        header_dict = {
            1: [self.get_invoice_name(invoice), invoice.number or ''],
            2: [
                _('Date'), invoice.date_invoice and
                self.format_date(invoice.date_invoice) or ''],
            3: [],
            4: [_('Customer number'), invoice.partner_id.ref or ''],
            5: [_('Name'), invoice.partner_id.name],
            6: [
                _('Address'), '%s %s' % (
                    invoice.partner_id.street and
                    invoice.partner_id.street or '',
                    invoice.partner_id.zip or '')],
            7: [
                _('Location'), invoice.partner_id.city and
                invoice.partner_id.city or ''],
            8: [
                _('State'), invoice.partner_id.state_id and
                invoice.partner_id.state_id.name or ''],
            9: [
                _('Country'), invoice.partner_id.country_id and
                invoice.partner_id.country_id.name or ''],
            10: [
                _('VAT'), invoice.partner_id and invoice.partner_id.vat or ''],
            11: []}
        self.encoded_rows(header_dict, doc)
        current_row = max(header_dict, key=header_dict.get) + 1
        return current_row

    @api.multi
    def get_invoice_lines(self, invoice, table_dict, current_row):
        table_dict.update({
            current_row: [
                _('Reference'), _('Description'), _('Quantity'),
                _('Price unit'), _('Discount'), _('Price subtotal')]})
        current_row += 1
        row_by_tmpl = {}
        for line in invoice.invoice_line:
            product_tmpl_id = line.product_id.product_tmpl_id.id
            ref = (
                line.product_id and line.product_id.default_code and
                line.product_id.default_code or '')
            description = (
                line.product_id and '%s %s' % (
                    line.product_id.name_template,
                    line.product_id.description_sale and
                    line.product_id.description_sale or '') or line.name)
            row_vals = [
                ref, description, line.quantity, line.price_unit,
                line.discount, line.price_subtotal]
            if product_tmpl_id not in row_by_tmpl:
                row_by_tmpl[product_tmpl_id] = row_vals
                table_dict[current_row] = row_by_tmpl[product_tmpl_id]
                current_row += 1
            else:
                price_diff = (
                    line.price_unit != row_by_tmpl[product_tmpl_id][3])
                disc_diff = line.discount != row_by_tmpl[product_tmpl_id][4]
                if price_diff or disc_diff:
                    diff = line.price_unit if price_diff else line.discount
                    row_by_tmpl['%s-%s' % (product_tmpl_id, diff)] = row_vals
                    row_by_tmpl_aux = dict(row_by_tmpl)
                    for pt_id, pt_vals in row_by_tmpl_aux.iteritems():
                        table_dict[current_row] = row_by_tmpl['%s-%s' % (
                            product_tmpl_id, diff)]
                else:
                    row_by_tmpl[product_tmpl_id][2] += line.quantity
                    row_by_tmpl[product_tmpl_id][5] += line.price_subtotal
        current_row += 1
        table_dict[current_row] = ''
        current_row += 1
        return table_dict, current_row

    @api.multi
    def get_invoice_totals(self, invoice, table_dict, current_row):
        table_dict.update({
            current_row: [
                '', '', '', '', _('Untaxed amount'), invoice.amount_untaxed],
            current_row + 1: [
                '', '', '', '', _('Amount tax'), invoice.amount_tax],
            current_row + 2: [
                '', '', '', '', _('Amount total'), invoice.amount_total],
            current_row + 3: []})
        current_row += 4
        return table_dict, current_row

    @api.multi
    def get_invoice_taxes(self, invoice, table_dict, current_row):
        table_dict.update({
            current_row: [_('Name'), _('Base'), _('Amount')]})
        current_row += 1
        for tax_line in invoice.tax_line:
            table_dict.update({
                current_row: [tax_line.name, tax_line.base, tax_line.amount]})
            current_row += 1
        table_dict.update({current_row: []})
        current_row += 1
        return table_dict, current_row

    @api.multi
    def get_table_invoice(self, invoice, doc, current_row):
        table_dict = {}
        table_dict, current_row = self.get_invoice_lines(
            invoice, table_dict, current_row)
        table_dict, current_row = self.get_invoice_totals(
            invoice, table_dict, current_row)
        table_dict, current_row = self.get_invoice_taxes(
            invoice, table_dict, current_row)
        self.encoded_rows(table_dict, doc)
        return current_row

    @api.multi
    def get_footer_invoice(self, invoice, doc, current_row):
        footer_dict = {
            current_row: [
                _('Payment mode'), invoice.payment_mode_id and
                invoice.payment_mode_id.name or ''],
            current_row + 1: [
                _('Payment term'), invoice.payment_term and
                invoice.payment_term.name or ''],
            current_row + 2: [_('Maturity'), self.get_maturity(invoice)],
            current_row + 3: [
                _('Agents name'), invoice.agents_name and
                invoice.agents_name or ''],
            current_row + 4: [_('Total units'), invoice.total_qty],
            current_row + 5: [_('Comment'), invoice.comment or '']}
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
    def write_invoice(self, invoice, doc):
        current_row = self.get_header_invoice(invoice, doc)
        current_row = self.get_table_invoice(invoice, doc, current_row)
        current_row = self.get_footer_invoice(invoice, doc, current_row)
        separator_rows = 3
        current_row = self.put_separator(separator_rows, doc, current_row)

    @api.multi
    def button_accept(self):
        assert self.ids, _('IDs do not exist.')
        assert self.env.context['active_model'] == 'account.invoice', _(
            'Active model is not a account invoice!')
        active_ids = self.env.context.get('active_ids', [])
        invoices = self.env['account.invoice'].browse(active_ids)
        content = self.invoices_writer(invoices)
        self.write({'ffile': content})
        res = self.env['ir.model.data'].get_object_reference(
            'account_invoice_export_atrapada',
            'account_invoice_export_ok_wizard')
        res_id = res and res[1] or False
        return {
            'name': _('Account invoice export'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'wiz.account_invoice_export',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new'}
