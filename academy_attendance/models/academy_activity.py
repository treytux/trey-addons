###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import calendar
import locale

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AcademyActivity(models.Model):
    _inherit = 'academy.activity'

    schedule = fields.Char(
        compute='_compute_schedule',
    )
    estimated_hours = fields.Float(
        compute='_compute_estimated_hours',
    )
    plan_attendance_line_ids = fields.One2many(
        comodel_name='academy.training.plan.attendance.line',
        inverse_name='activity_id',
        string='Attendance sheet',
    )

    @api.depends('plan_attendance_line_ids')
    def _compute_schedule(self):
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        for activity in self:
            schedules = []
            activity.schedule = False
            for attendance_line in activity.plan_attendance_line_ids:
                weekday_name = calendar.day_name[int(attendance_line.weekday)]
                weekday_initial = weekday_name[0:2].capitalize()
                start_time = attendance_line.float_to_time(
                    attendance_line.time_begin).strftime('%H:%M')
                end_time = attendance_line.float_to_time(
                    attendance_line.time_end).strftime('%H:%M')
                schedules.append("%s(%s - %s)" % (
                    weekday_initial, start_time, end_time))
            if schedules:
                activity.schedule = '-'.join(schedules)

    @api.depends('plan_attendance_line_ids')
    def _compute_estimated_hours(self):
        for activity in self:
            total_time = 0
            for attendance_sheet in activity.mapped(
                    'plan_attendance_line_ids.attendance_sheet_ids'):
                if attendance_sheet.date_start > attendance_sheet.date_end:
                    continue
                total_time += (
                    attendance_sheet.date_end
                    - attendance_sheet.date_start).seconds / 3600
            activity.estimated_hours = total_time

    def action_print_attendance_sheet(self):
        self.ensure_one()
        if not self.enrollment_ids:
            raise UserError(_('No enrollments found for this activity.'))
        return self.env.ref(
            'academy_attendance.academy_activity_attendance_sheet_create'
        ).report_action(self)
