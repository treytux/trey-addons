###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class EduTrainingPlanLine(models.Model):
    _inherit = 'edu.training.plan.line'

    schedule = fields.Char(
        compute='_compute_schedule',
    )
    estimated_hours = fields.Float(
        compute='_compute_estimated_hours',
    )
    plan_attendance_line_ids = fields.One2many(
        comodel_name='edu.training.plan.attendance.line',
        inverse_name='training_plan_line_id',
        string='Attendance sheet',
    )

    @api.depends('plan_attendance_line_ids')
    def _compute_schedule(self):
        for plan_line in self:
            schedules = []
            for attendance_line in plan_line.plan_attendance_line_ids:
                weekday_initial = attendance_line.weekday[0].capitalize()
                start_time = attendance_line.float_to_time(
                    attendance_line.time_begin)
                end_time = attendance_line.float_to_time(
                    attendance_line.time_end)
                schedules.append("%s(%s - %s)" % (
                    weekday_initial, start_time, end_time))
            if schedules:
                plan_line.schedule = '-'.join(schedules)

    @api.depends('plan_attendance_line_ids')
    def _compute_estimated_hours(self):
        for plan_line in self:
            total_time = 0
            for attendance_sheet in plan_line.mapped(
                    'plan_attendance_line_ids.attendance_sheet_ids'):
                if attendance_sheet.date_start > attendance_sheet.date_end:
                    continue
                total_time += (
                    attendance_sheet.date_end
                    - attendance_sheet.date_start).seconds / 3600
            plan_line.estimated_hours = total_time
