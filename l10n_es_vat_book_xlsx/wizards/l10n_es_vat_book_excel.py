# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import base64
import StringIO
from openerp import models, api, fields, exceptions, _
import logging
_log = logging.getLogger(__name__)
try:
    import xlsxwriter
except ImportError:
    _log.debug(_(
        'Module xlsxwriter not installed in server, please install with: '
        'sudo pip install xlsxwriter'))


class L10nEsVatBookExcel(models.TransientModel):
    _name = 'l10n.es.vat.book.excel'
    _description = 'Spain Vat Book to Excel'

    file_data = fields.Binary(
        string='Excel File',
    )
    file_name = fields.Char(
        string='File Name',
    )
    out_invoices = fields.Boolean(
        string='Customer Invoices',
    )
    out_refunds = fields.Boolean(
        string='Customer Refunds',
    )
    in_invoices = fields.Boolean(
        string='Supplier Invoices',
    )
    in_refunds = fields.Boolean(
        string='Supplier Refunds',
    )
    state = fields.Selection(
        string='State',
        selection=[
            ('draft', 'Draft'),
            ('done', 'Done'),
        ],
        default='draft',
    )

    @api.one
    def action_step_done(self):
        def generate_header(sheets=None):
            bold = workbook.add_format({'bold': True})
            headers = {
                'customer': {
                    'A1': _('Invoice'),
                    'B1': _('Date'),
                    'C1': _('Company'),
                    'D1': _('VAT'),
                    'E1': _('Base'),
                    'F1': _('Type'),
                    'G1': _('Quote'),
                    'H1': _('Tax Name'),
                },
                'supplier': {
                    'A1': _('Internal Invoice'),
                    'B1': _('Date'),
                    'C1': _('Supplier Invoice'),
                    'D1': _('Company'),
                    'E1': _('VAT'),
                    'F1': _('Base'),
                    'G1': _('Type'),
                    'H1': _('Quote'),
                    'I1': _('Tax Name'),
                },
            }
            if sheets['out_invoices']:
                for key, value in headers['customer'].items():
                    sheets['out_invoices'].write(key, value, bold)
            if sheets['out_refunds']:
                for key, value in headers['customer'].items():
                    sheets['out_refunds'].write(key, value, bold)
            if sheets['in_invoices']:
                for key, value in headers['supplier'].items():
                    sheets['in_invoices'].write(key, value, bold)
            if sheets['in_refunds']:
                for key, value in headers['supplier'].items():
                    sheets['in_refunds'].write(key, value, bold)
            _log.info('Generate Excel Header')

        def generate_lines(sheet, lines=None, partner_type='customer',
                           invoice_type='out_invoices'):
            num_format = workbook.add_format({'num_format': '#,##0.00'})
            date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
            row = 1
            col = 0
            for line in lines:
                if invoice_type == 'out_invoices':
                    taxes = line.tax_line_issued_ids
                if invoice_type == 'out_refunds':
                    taxes = line.tax_lines_rectification_issued_ids
                if invoice_type == 'in_invoices':
                    taxes = line.tax_lines_received_ids
                if invoice_type == 'in_refunds':
                    taxes = line.tax_lines_rectification_received_ids
                for tax in taxes:
                    sheet.write_string(row, col, line.invoice_id.number)
                    inv_date = fields.Date.from_string(
                        line.invoice_id.date_invoice)
                    sheet.write_datetime(row, col + 1, inv_date, date_format)
                    if partner_type == 'supplier':
                        sheet.write_string(
                            row, col + 2, (line.invoice_id.reference or
                                           line.invoice_id.number or ''))
                        sheet.write_string(row, col + 3, line.partner_id.name)
                        sheet.write_string(row, col + 4, line.vat_number or '')
                        sheet.write_number(
                            row, col + 5, tax.amount_without_tax, num_format)
                        sheet.write_number(
                            row, col + 6, tax.tax_percent * 100, num_format)
                        sheet.write_number(
                            row, col + 7, tax.tax_amount, num_format)
                        sheet.write_string(row, col + 8, tax.name)
                        row += 1
                    else:
                        sheet.write_string(row, col + 2, line.partner_id.name)
                        sheet.write_string(row, col + 3, line.vat_number or '')
                        sheet.write_number(
                            row, col + 4, tax.amount_without_tax,
                            num_format)
                        sheet.write_number(
                            row, col + 5, tax.tax_percent * 100,
                            num_format)
                        sheet.write_number(
                            row, col + 6, tax.tax_amount, num_format)
                        sheet.write_string(row, col + 7, tax.name)
                        row += 1

        if not (self.out_invoices or self.out_refunds or self.in_invoices or
                self.in_refunds):
            raise exceptions.Warning(_(
                'Please check some of the options to generate the Excel'))
        vat_book = self.env['l10n.es.vat.book'].browse(
            self.env.context['active_id'])
        output = StringIO.StringIO()
        workbook = xlsxwriter.Workbook(output)
        worksheets = {
            'out_invoices': workbook.add_worksheet(_(
                'Customer Invoices')) if self.out_invoices else None,
            'out_refunds': workbook.add_worksheet(_(
                'Customer Refunds')) if self.out_refunds else None,
            'in_invoices': workbook.add_worksheet(_(
                'Supplier Invoices')) if self.in_invoices else None,
            'in_refunds': workbook.add_worksheet(_(
                'Supplier Refunds')) if self.in_refunds else None,
        }
        generate_header(worksheets)
        if worksheets['out_invoices']:
            generate_lines(
                worksheets['out_invoices'], vat_book.issued_invoice_ids,
                'customer', 'out_invoices')
        if worksheets['out_refunds']:
            generate_lines(
                worksheets['out_refunds'],
                vat_book.rectification_issued_invoice_ids, 'customer',
                'out_refunds')
        if worksheets['in_invoices']:
            generate_lines(
                worksheets['in_invoices'], vat_book.received_invoice_ids,
                'supplier', 'in_invoices')
        if worksheets['in_refunds']:
            generate_lines(
                worksheets['in_refunds'],
                vat_book.rectification_received_invoice_ids, 'supplier',
                'in_refunds')
        workbook.close()
        content = base64.encodestring(output.getvalue())
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'l10n.es.vat.book'),
            ('res_id', '=', vat_book.id)])
        attachments.unlink()
        self.env['ir.attachment'].create({
            'res_model': 'l10n.es.vat.book',
            'res_id': vat_book.id,
            'datas_fname': '%s.xlsx' % vat_book.name or 'vat_book',
            'datas': content,
            'name': '%s.xlsx' % vat_book.name or 'vat_book',
        })
        self.state = 'done'
