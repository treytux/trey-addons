# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api
from functools import partial


class PrintIntrastatReport(models.TransientModel):
    _name = 'report.intrastat_report.print_intrastat_report'

    @api.multi
    def get_amount_total(self, intrastats):
        return sum([i.amount_company_currency for i in intrastats])

    @api.multi
    def get_supply_units_total(self, intrastats):
        return sum([i.supply_units for i in intrastats])

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name(
            'intrastat_report.print_intrastat_report')
        selected_intrastat_reps = self.env['intrastat.report'].browse(self.ids)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': selected_intrastat_reps,
            'get_amount_total': partial(self.get_amount_total),
            'get_supply_units_total': partial(self.get_supply_units_total)}
        report = report_obj.browse(self.ids[0])
        return report.render(
            'intrastat_report.print_intrastat_report', docargs)
