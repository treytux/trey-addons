###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, timedelta

from odoo import models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _send_student_attendance_email(self):
        today = datetime.now().date()
        first_day_last_month = (
            today.replace(day=1) - timedelta(days=1)).replace(day=1)
        last_day_last_month = (today.replace(day=1) - timedelta(days=1))
        template = self.env.ref('education_attendance.student_attendance_email')
        students = self.env['res.partner'].search([
            ('is_student', '=', True),
            ('tutor_ids', '!=', False),
        ])
        for student in students:
            absences = self.env['edu.attendance.sheet.line'].search([
                ('student_id', '=', student.id),
                ('date', '>=', first_day_last_month),
                ('date', '<=', last_day_last_month),
                ('attendance_sheet_id.state', 'not in', ['draft', 'cancelled']),
                ('present', '=', False),
            ])
            if not absences:
                continue
            template_ctx = {
                'student': student,
                'absences': absences,
                'date': first_day_last_month,
            }
            for tutor in student.tutor_ids:
                template.with_context(template_ctx).send_mail(tutor.id)
