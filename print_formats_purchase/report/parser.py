# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class PurchaseReport(models.TransientModel):
    _name = 'report.purchase.report_purchaseorder'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        order_obj = self.env['purchase.order']
        report = report_obj._get_report_from_name(
            'purchase.report_purchaseorder')
        selected_orders = order_obj.browse(self.ids)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': selected_orders}
        report = report_obj.browse(self.ids[0])
        return report.render('purchase.report_purchaseorder', docargs)
