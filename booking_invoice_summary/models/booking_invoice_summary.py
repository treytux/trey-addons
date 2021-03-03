# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import base64
import StringIO
from openerp import models, fields, api, _
import logging
_log = logging.getLogger(__name__)

try:
    import xlsxwriter
except ImportError:
    _log.debug(_(
        'Module xlsxwriter not installed in server, please install with: '
        'sudo pip install xlsxwriter'))


class BookingInvoiceSummary(models.Model):
    _name = 'booking.invoice.summary'
    _description = 'Booking Invoice Summary'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(
        string='Name',
        required=True,
        default='/'
    )
    date_from = fields.Date(
        string='Date From',
        required=True,
    )
    date_to = fields.Date(
        string='Date To',
        required=True,
    )
    note = fields.Text(
        string='Note',
    )
    state = fields.Selection(
        string='State',
        selection=[
            ('draft', 'Draft'),
            ('calculated', 'Calculated'),
            ('send', 'Send'),
            ('done', 'Done'),
        ],
        required=True,
        default='draft',
        track_visibility='onchange',
    )
    lines = fields.One2many(
        comodel_name='booking.invoice.summary.line',
        inverse_name='summary_id',
        string='Lines',
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user,
    )

    @api.one
    def action_calculate(self):
        if self.state not in ('draft', 'calculated'):
            return False
        if self.lines:
            self.lines.unlink()
        partners = self.env['res.partner'].search([('customer', '=', True)])
        for partner in partners:
            invoices = self.env['account.invoice'].search([
                ('type', 'in', ('out_invoice', 'out_refund')),
                ('state', '=', 'open'), ('booking_id', '!=', None),
                ('date_invoice', '>=', self.date_from),
                ('date_invoice', '<=', self.date_to),
                ('partner_id', '=', partner.id)], order='date_invoice desc')
            if invoices:
                self.env['booking.invoice.summary.line'].create({
                    'summary_id': self.id,
                    'partner_id': partner.id,
                    'invoice_ids': [(6, 0, invoices.ids)]
                })
        if self.lines:
            self.state = 'calculated'

    @api.one
    def action_create_xls(self):
        for line in self.lines:
            output = StringIO.StringIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet(_('Bookings'))
            bold = workbook.add_format({'bold': True})
            worksheet.write('A1', _('Invoice'), bold)
            worksheet.write('B1', _('Date'), bold)
            worksheet.write('C1', _('Booking'), bold)
            worksheet.write('D1', _('Date From'), bold)
            worksheet.write('E1', _('Date To'), bold)
            worksheet.write('F1', _('Holder'), bold)
            worksheet.write('G1', _('Amount'), bold)
            worksheet.write('H1', _('Taxes'), bold)
            worksheet.write('I1', _('Total'), bold)
            row = 1
            col = 0
            bold = workbook.add_format({'bold': True})
            for invoice in line.invoice_ids:
                worksheet.write_string(row, col, invoice.number)
                worksheet.write_string(row, col + 1, invoice.date_invoice)
                worksheet.write_string(row, col + 2, invoice.booking_id.name)
                worksheet.write_string(
                    row, col + 3, invoice.booking_id.booking_line.date_init)
                worksheet.write_string(
                    row, col + 4, invoice.booking_id.booking_line.date_end)
                worksheet.write_string(
                    row, col + 5, invoice.booking_id.holder_id.name)
                if invoice.type == 'out_invoice':
                    worksheet.write_number(
                        row, col + 6, invoice.amount_untaxed)
                    worksheet.write_number(row, col + 7, invoice.amount_tax)
                    worksheet.write_number(row, col + 8, invoice.amount_total)
                else:
                    worksheet.write_number(
                        row, col+6, -invoice.amount_untaxed)
                    worksheet.write_number(row, col + 7, -invoice.amount_tax)
                    worksheet.write_number(row, col + 8, -invoice.amount_total)
                row += 1
            worksheet.write_number(row, col + 6, invoice.amount_untaxed, bold)
            worksheet.write_number(row, col + 7, invoice.amount_tax, bold)
            worksheet.write_number(row, col + 8, invoice.amount_total, bold)
            workbook.close()
            content = base64.encodestring(output.getvalue())
            filename = '%s-%s-%s.xlsx' % (
                line.partner_id.name, self.date_from, self.date_to)
            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'booking.invoice.summary.line'),
                ('res_id', '=', line.id)])
            attachments.unlink()
            self.env['ir.attachment'].create({
                'res_model': 'booking.invoice.summary.line',
                'res_id': line.id,
                'datas_fname': filename,
                'datas': content,
                'name': filename,
            })
            self.env.cr.commit()
        self.state = 'send'

    @api.multi
    def action_send_summary_email(self):
        self.ensure_one()
        if self.state != 'calculated' or not self.lines:
            return False
        lines = self.mapped('lines').filtered(
            lambda l: l.is_send_email is True)
        for line in lines:
            line.action_send_email_background()
        self.state = 'done'
