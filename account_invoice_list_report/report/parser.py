# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from datetime import datetime
from openerp import models, api


class AccountInvoiceList(models.TransientModel):
    _name = 'report.account_invoice_list_report.account_invoice_list'

    @api.multi
    def render_html(self, data=None):
        env = self.env
        template = 'account_invoice_list_report.account_invoice_list'
        doc = env['report']._get_report_from_name(template)
        selected_obj = env['account.invoice'].browse(self.ids)
        report = env['report'].browse(self.ids[0])
        dates = [
            datetime.strptime(i.date_invoice, '%Y-%m-%d')
            for i in selected_obj if i.date_invoice]
        lang = env['res.lang'].search(
            [('code', '=', env.user.partner_id.lang)])
        date_begin = (
            dates and min(dates).strftime(lang[0].date_format) or '')
        date_end = (
            dates and max(dates).strftime(lang[0].date_format) or '')
        return report.render(template, {
            'doc_ids': self.ids,
            'doc_model': doc.model,
            'docs': selected_obj,
            'date_begin': date_begin,
            'date_end': date_end})
