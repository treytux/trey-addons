###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models
from odoo.tools.misc import format_date


class ReportInvoiceList(models.AbstractModel):
    _name = 'report.print_formats_invoice_list.account_move_list'
    _description = 'Report Invoice List'

    def _get_report_values(self, docids, data=None):
        docs = self.env['account.move'].browse(docids).exists()
        invoice_dates = [
            invoice_date for invoice_date in docs.mapped('invoice_date')
            if invoice_date
        ]
        company = docs[:1].company_id or self.env.company
        company_lang = (
            company.partner_id.lang or self.env.company.partner_id.lang)
        lang = self.env.user.lang or company_lang
        if invoice_dates:
            date_begin = format_date(
                self.env, min(invoice_dates), lang_code=lang)
            date_end = format_date(
                self.env, max(invoice_dates), lang_code=lang)
        else:
            date_begin = ''
            date_end = ''
        return {
            'doc_ids': docs.ids,
            'doc_model': 'account.move',
            'docs': docs,
            'date_begin': date_begin,
            'date_end': date_end,
            'report_lang': lang,
        }
