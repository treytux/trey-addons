###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from collections import OrderedDict

from odoo import api, models


class ReportAccountReportInvoiceBase(models.AbstractModel):
    _inherit = 'report.account.report_invoice_base'

    def get_lines_sorted(self, invoice):
        lines_dict = {}
        for line in invoice.invoice_line_ids:
            attrs = line.product_id.attribute_value_ids.mapped(
                'attribute_id')
            key = '%s' % (line.product_id.website_default_code or 'z')
            for attr in attrs:
                filtered_val = line.product_id.attribute_value_ids.filtered(
                    lambda x: x.attribute_id.id == attr.id)
                key += '-%s' % str(filtered_val.sequence).zfill(4)
            key += '-%s' % str(line.id).zfill(4)
            lines_dict.setdefault(key, line)
        return OrderedDict(sorted(lines_dict.items()))

    def get_lines_grouped(self, invoice):
        if invoice.company_id.invoice_report_group_by:
            return super().get_lines_grouped(invoice)
        return [
            {'picking': False, 'line': line, 'quantity': line.quantity}
            for line in self.get_lines_sorted(invoice).values()
        ]

    @api.multi
    def _get_report_values(self, docids, data=None):
        res = super()._get_report_values(docids, data)
        res['get_lines_sorted'] = self.get_lines_sorted
        return res


class ReportAccountReportInvoice(ReportAccountReportInvoiceBase):
    _inherit = 'report.account.report_invoice'


class ReportAccountReportInvoiceWithPayments(ReportAccountReportInvoiceBase):
    _inherit = 'report.account.report_invoice_with_payments'
