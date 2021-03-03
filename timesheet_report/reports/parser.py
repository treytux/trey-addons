# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models


class TimesheetReport(models.TransientModel):
    _name = 'report.timesheet_report.report_timesheet'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        template = 'timesheet_report.report_timesheet'
        report = report_obj.browse(self.ids[0])
        return report.render(template, {
            'doc_ids': self.ids,
            'doc_model': 'hr.employee',
            'docs': data['employe_ids'],
            'data': data,
            'month_days': [day for day in range(1, data['month_days'] + 1)],
        })
