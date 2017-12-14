# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class EducationAttendanceEduAttendanceSheet(models.TransientModel):
    _name = 'report.education_attendance.edu_attendance_sheet'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        attendance_sheet_obj = self.env['edu.attendance.sheet']
        report = report_obj._get_report_from_name(
            'education_attendance.edu_attendance_sheet')
        attendance_sheets = attendance_sheet_obj.browse(self.ids)

        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': attendance_sheets}

        report = report_obj.browse(self.ids[0])
        return report.render(
            'education_attendance.edu_attendance_sheet', docargs)
