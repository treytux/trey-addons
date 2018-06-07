# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class AccountPickingList(models.TransientModel):
    _name = 'report.account_picking_list_report.account_picking_list'

    @api.multi
    def render_html(self, data=None):
        env = self.env
        template = 'stock.report_picking'
        doc = env['report']._get_report_from_name(template)
        selected_obj = env['account.invoice'].browse(self.ids)
        report = env['report'].browse(self.ids[0])
        return report.render(template, {
            'doc_ids': selected_obj.picking_ids.ids,
            'doc_model': doc.model,
            'docs': selected_obj.picking_ids})
