# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class StockPicking(models.TransientModel):
    _name = 'report.print_formats_voucher.report_account_voucher'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        voucher_obj = self.env['account.voucher']
        report = report_obj._get_report_from_name(
            'print_formats_voucher.report_account_voucher')
        selected_vouchers = voucher_obj.browse(self.ids)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': selected_vouchers}
        report = report_obj.browse(self.ids[0])
        return report.render(
            'print_formats_voucher.report_account_voucher', docargs)
