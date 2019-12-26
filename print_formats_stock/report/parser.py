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
        template = 'stock.report_picking'
        doc = report_obj._get_report_from_name(template)
        report = report_obj.browse(self.ids[0])
        return report.render(template, {
            'doc_ids': self.ids,
            'doc_model': doc.model,
            'docs': self.env['stock.picking'].browse(self.ids),
        })
