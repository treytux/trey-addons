###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ReportAccountReportInvoiceBase(models.AbstractModel):
    _inherit = 'report.account.report_invoice_base'

    def get_lines_grouped_by_group(self, invoice):
        result = self.env['account.invoice.line']
        done = self.env['account.invoice.line']
        for line in invoice.invoice_line_ids:
            if not line.group_id:
                result |= line
            else:
                if line in done:
                    continue
                to_add = invoice.invoice_line_ids.filtered(
                    lambda ln: ln.group_id == line.group_id)
                result |= to_add
                done |= to_add
        return result

    def get_lines_grouped(self, invoice):
        return self.get_lines_grouped_by_group(invoice)


class ReportAccountReportInvoice(ReportAccountReportInvoiceBase):
    _inherit = 'report.account.report_invoice'


class ReportAccountReportInvoiceWithPayments(ReportAccountReportInvoiceBase):
    _inherit = 'report.account.report_invoice_with_payments'
