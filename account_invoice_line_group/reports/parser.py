###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ReportAccountReportInvoiceBase(models.AbstractModel):
    _inherit = 'report.account.report_invoice_base'

    @api.multi
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
                    lambda l: l.group_id == line.group_id)
                result |= to_add
                done |= to_add
        return result

    @api.multi
    def get_lines_grouped_by(self, invoice):
        if not any(invoice.mapped('invoice_line_ids.group_id')):
            return super().get_lines_grouped_by(invoice)
        return self.get_lines_grouped_by_group(invoice)


class ReportAccountReportInvoice(ReportAccountReportInvoiceBase):
    _inherit = 'report.account.report_invoice'


class ReportAccountReportInvoiceWithPayments(ReportAccountReportInvoiceBase):
    _inherit = 'report.account.report_invoice_with_payments'
