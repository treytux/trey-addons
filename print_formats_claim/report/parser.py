# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class StockPicking(models.TransientModel):
    _name = 'report.print_formats_claim.report_crm_claim'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        claim_obj = self.env['crm.claim']
        report = report_obj._get_report_from_name(
            'print_formats_claim.report_crm_claim')
        claims = claim_obj.browse(self.ids)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': claims}
        report = report_obj.browse(self.ids[0])
        return report.render('print_formats_claim.report_crm_claim', docargs)
