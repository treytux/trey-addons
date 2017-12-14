# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class SaleReport(models.TransientModel):
    _name = 'report.sale.report_saleorder'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        order_obj = self.env['sale.order']
        report = report_obj._get_report_from_name('sale.report_saleorder')
        selected_orders = order_obj.browse(self.ids)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': selected_orders}
        report = report_obj.browse(self.ids[0])
        return report.render('sale.report_saleorder', docargs)
