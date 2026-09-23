###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
from datetime import datetime

import xlwt
from odoo import _, fields, models


class ResPartnerExportFinancialRisk(models.TransientModel):
    _name = 'res.partner.export.financial.risk'
    _description = 'Wizard to export financial risk of partners to a file'

    file = fields.Binary(
        string='File',
        readonly=True,
        filename='filename',
    )
    filename = fields.Char(
        string='Filename',
    )

    def set_header_report_partner_financial_risk(self, sheet, title_format):
        sheet.write(0, 0, _('Name'), title_format)
        sheet.write(0, 1, _('VAT'), title_format)
        sheet.write(0, 2, _('Credit limit'), title_format)
        sheet.write(0, 3, _('Import invoices/balance unpaid'), title_format)
        sheet.write(0, 4, _('Import invoices/balance open'), title_format)
        sheet.write(0, 5, _('Import sale orders'), title_format)
        sheet.write(0, 6, _('Import draft invoices'), title_format)
        sheet.write(0, 7, _('Total risk'), title_format)

    def set_column_width(self, sheet):
        sheet.col(0).width = 7000
        sheet.col(1).width = 7000
        sheet.col(2).width = 4000
        sheet.col(3).width = 8000
        sheet.col(4).width = 7000
        sheet.col(5).width = 7000
        sheet.col(6).width = 7000

    def set_url_download(self):
        filename = 'partner_financial_risk_%s.xls' % (
            datetime.strftime(datetime.now(), '%y%m%d_%H%M'))
        url = ('web/content/?model=%s&id=%s&filename_field=filename&field=file'
               '&download=true&filename=%s')
        url = url % (self._name, self.id, filename)
        return {
            'url': url,
            'filename': filename,
        }

    def button_export_financial_risk(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        partners = self.env['res.partner'].browse(active_ids)
        wb = xlwt.Workbook()
        style_string = "font: bold on; borders: bottom dashed"
        title_format = xlwt.easyxf(style_string)
        ws = wb.add_sheet('Financial risk')
        self.set_header_report_partner_financial_risk(ws, title_format)
        self.set_column_width(ws)
        row = 1
        col = 0
        for partner in partners:
            ws.write(row, col, partner.name)
            ws.write(row, col + 1, partner.vat and partner.vat or ' ')
            ws.write(row, col + 2, partner.credit_limit)
            ws.write(row, col + 3, partner.risk_invoice_unpaid)
            ws.write(row, col + 4, partner.risk_invoice_open)
            ws.write(row, col + 5, partner.risk_sale_order)
            ws.write(row, col + 6, partner.risk_invoice_draft)
            ws.write(row, col + 7, partner.risk_total)
            row += 1
        fp = io.BytesIO()
        wb.save(fp)
        self.file = base64.encodestring(fp.getvalue())
        fp.close()
        res = self.set_url_download()
        self.filename = res['filename']
        return {
            'type': 'ir.actions.act_url',
            'url': res['url'],
            'target': 'new',
            'nodestroy': False,
        }
