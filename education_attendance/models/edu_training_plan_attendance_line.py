###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, time, timedelta

import dateutil
from dateutil.relativedelta import relativedelta
from dateutil.rrule import DAILY, MONTHLY, YEARLY, rrule
from odoo import _, exceptions, fields, models
from pytz import timezone


class EduTrainingPlanAttendanceLine(models.Model):
    _name = 'edu.training.plan.attendance.line'
    _description = 'Training plan attendance sheet line'

    training_plan_line_id = fields.Many2one(
        comodel_name='edu.training.plan.line',
        string='Training plan line',
        required=True,
    )
    training_plan_hr_holiday_id = fields.Many2one(
        related='training_plan_line_id.training_plan_id.hr_holiday_id',
        comodel_name='hr.holidays.public',
        string='Public Holidays',
    )
    time_begin = fields.Float(
        string='Begin hour',
        required=True,
    )
    time_end = fields.Float(
        string='End hour',
        required=True,
    )
    teacher_id = fields.Many2one(
        comodel_name='res.partner',
        string='Teacher',
        required=True,
    )
    period = fields.Selection(
        selection=[
            ('weekly', 'Weekly'),
            ('biweekly', 'Biweekly'),
            ('monthly', 'Monthly'),
            ('bimonthly', 'Bimonthly'),
            ('quaterly', 'Quaterly'),
            ('biannual', 'Biannual'),
            ('yearly', 'Yearly'),
            ('special', 'Special'),
        ],
        string='Periodicity',
        default='weekly',
        required=True,
    )
    weekday = fields.Selection(
        selection=[
            ('monday', 'Monday'),
            ('tuesday', 'Tuesday'),
            ('wednesday', 'Wednesday'),
            ('thursday', 'Thursday'),
            ('friday', 'Friday'),
            ('saturday', 'Saturday'),
            ('sunday', 'Sunday'),
        ],
        string='Weekday',
        default='monday',
        required=True,
    )
    attendance_sheet_ids = fields.One2many(
        comodel_name='edu.attendance.sheet',
        inverse_name='attencance_sheet_line_id',
        string='Attendance sheets',
    )

    def float_to_time(self, float_time):
        minutes = int(float_time * 60)
        hours, minutes = divmod(minutes, 60)
        return time(hours, minutes)

    def get_dst_time(self, datetime_a, datetime_b):
        tz = timezone(self.env.user.tz or 'UTC')
        dstime = datetime_a.astimezone(tz).dst().seconds
        dstime_relative = datetime_b.astimezone(tz).dst().seconds
        if dstime < dstime_relative:
            datetime_b = datetime_b + relativedelta(
                seconds=dstime_relative)
        if dstime > dstime_relative:
            datetime_b = datetime_b - relativedelta(seconds=dstime)
        return datetime_b

    def _get_first_day(self, start_date, end_date):
        difference = start_date - start_date
        for i in range(difference.days + 1):
            date = start_date + timedelta(days=i)
            if date.weekday() == 0:
                return date

    def _get_weekday(self):
        return {
            'monday': dateutil.rrule.MO,
            'tuesday': dateutil.rrule.TU,
            'wednesday': dateutil.rrule.WE,
            'thursday': dateutil.rrule.TH,
            'friday': dateutil.rrule.FR,
            'saturday': dateutil.rrule.SA,
            'sunday': dateutil.rrule.SU
        }

    def _get_attendance_dates(self):
        interval = 1
        if self.period == 'weekly':
            frequency = DAILY
        elif self.period == 'biweekly':
            frequency = DAILY
            interval = 2
        elif self.period == 'monthly':
            frequency = MONTHLY
        elif self.period == 'bimonthly':
            frequency = MONTHLY
            interval = 2
        elif self.period == 'quaterly':
            frequency = MONTHLY
            interval = 3
        elif self.period == 'yearly':
            frequency = YEARLY
        elif self.period == 'biannual':
            frequency = YEARLY
            interval = 2
        return rrule(
            frequency,
            dtstart=self.training_plan_line_id.start_date,
            until=self.training_plan_line_id.end_date,
            byweekday=self._get_weekday()[self.weekday],
            interval=interval,
            bysetpos=1)

    def generate_attendances(self):

        def _get_attendance_sheet_data(line, start_datetime, end_datetime):
            return {
                'name': line.training_plan_line_id.name,
                'training_plan_line_id': line.training_plan_line_id.id,
                'attencance_sheet_line_id': line.id,
                'user_id': line.training_plan_line_id.user_id.id,
                'teacher_id': line.teacher_id.id,
                'date': start_datetime.date(),
                'date_start': self.get_dst_time(datetime.now(), start_datetime),
                'date_end': self.get_dst_time(datetime.now(), end_datetime),
            }

        if (not self.training_plan_line_id.start_date
                or not self.training_plan_line_id.end_date):
            raise exceptions.ValidationError(_(
                'Training plan line dates are required'))
        self.training_plan_line_id._compute_schedule()
        att_sheet_obj = self.env['edu.attendance.sheet']
        holidays_public_id = self.training_plan_hr_holiday_id
        offset = int(self.env.user.tz_offset[:3])
        for att_line in self:
            if att_line.attendance_sheet_ids:
                raise exceptions.ValidationError(_(
                    'Attendance sheets already generated'))
            if att_line.period == 'special':
                start_date = (datetime.combine(
                    att_line.training_plan_line_id.start_date,
                    self.float_to_time(att_line.time_begin))
                    - timedelta(hours=int(offset)))
                end_datetime = (datetime.combine(
                    att_line.training_plan_line_id.start_date,
                    att_line.float_to_time(att_line.time_end))
                    - timedelta(hours=int(offset)))
                att_sheet_obj.create(_get_attendance_sheet_data(
                    att_line, start_date, end_datetime))
                continue
            dates_start = att_line._get_attendance_dates()
            if not dates_start:
                raise exceptions.ValidationError(_(
                    'Could not create attendances'))
            for date in dates_start:
                start_datetime = datetime.combine(
                    date.date(),
                    att_line.float_to_time(att_line.time_begin)
                ) - timedelta(hours=int(offset))
                end_datetime = datetime.combine(
                    date.date(),
                    att_line.float_to_time(att_line.time_end)
                ) - timedelta(hours=int(offset))
                if holidays_public_id:
                    if holidays_public_id.is_public_holiday(
                            start_datetime.date()):
                        continue
                att_sheet_obj.create(_get_attendance_sheet_data(
                    att_line, start_datetime, end_datetime))
