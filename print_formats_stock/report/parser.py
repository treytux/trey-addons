# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class StockPicking(models.TransientModel):
    _name = 'report.stock.report_picking'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        order_obj = self.env['stock.picking']
        report = report_obj._get_report_from_name('stock.report_picking')
        selected_orders = order_obj.browse(self.ids)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': selected_orders}
        report = report_obj.browse(self.ids[0])
        return report.render('stock.report_picking', docargs)
