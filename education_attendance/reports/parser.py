###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class EducationAttendanceEduAttendanceSheet(models.TransientModel):
    _name = 'report.education_attendance.edu_attendance_sheet'
    _description = 'Edu attendance sheet'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['edu.attendance.sheet'].browse(docids)
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name(
            'education_attendance.edu_attendance_sheet')
        return {
            'data': data,
            'docs': docs,
            'doc_model': report.model,
        }
