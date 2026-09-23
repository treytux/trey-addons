###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, time, timedelta

import dateutil
from dateutil.relativedelta import relativedelta
from dateutil.rrule import DAILY, MONTHLY, YEARLY, rrule
from odoo import _, exceptions, fields, models
from pytz import UTC, timezone


class AcademyTrainingPlanAttendanceLine(models.Model):
    _name = 'academy.training.plan.attendance.line'
    _description = 'Training plan attendance sheet line'

    activity_id = fields.Many2one(
        comodel_name='academy.activity',
        string='Activity',
        required=True,
    )
    training_plan_hr_holiday_ids = fields.Many2many(
        related='activity_id.training_plan_id.hr_holiday_ids',
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
        comodel_name='hr.employee',
        string='Teacher',
        domain=[('is_activity_selectable', '=', True)],
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
            ('0', 'Monday'),
            ('1', 'Tuesday'),
            ('2', 'Wednesday'),
            ('3', 'Thursday'),
            ('4', 'Friday'),
            ('5', 'Saturday'),
            ('6', 'Sunday'),
        ],
        string='Weekday',
        default='0',
        required=True,
    )
    attendance_sheet_ids = fields.One2many(
        comodel_name='academy.attendance.sheet',
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
            '0': dateutil.rrule.MO,
            '1': dateutil.rrule.TU,
            '2': dateutil.rrule.WE,
            '3': dateutil.rrule.TH,
            '4': dateutil.rrule.FR,
            '5': dateutil.rrule.SA,
            '6': dateutil.rrule.SU,
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
            dtstart=self.activity_id.start_date,
            until=self.activity_id.end_date,
            byweekday=self._get_weekday()[self.weekday],
            interval=interval,
            bysetpos=1)

    def generate_attendances(self):

        def _get_attendance_sheet_data(line, start_datetime, end_datetime):
            return {
                'activity_id': line.activity_id.id,
                'attencance_sheet_line_id': line.id,
                'user_id': line.activity_id.user_id.id,
                'teacher_id': line.teacher_id.id,
                'date': start_datetime.astimezone(
                    timezone(self.env.user.tz or 'Europe/Madrid')).date(),
                'date_start': start_datetime,
                'date_end': end_datetime,
            }

        if (not self.activity_id.start_date
                or not self.activity_id.end_date):
            raise exceptions.ValidationError(_(
                'Activity dates are required'))
        self.activity_id._compute_schedule()
        att_sheet_obj = self.env['academy.attendance.sheet']
        holidays_public_ids = self.training_plan_hr_holiday_ids
        user_tz = timezone(self.env.user.tz or 'Europe/Madrid')
        for att_line in self:
            if att_line.attendance_sheet_ids:
                raise exceptions.ValidationError(_(
                    'Attendance sheets already generated'))
            if att_line.period == 'special':
                start_date = datetime.combine(
                    att_line.activity_id.start_date,
                    self.float_to_time(att_line.time_begin))
                end_date = datetime.combine(
                    att_line.activity_id.start_date,
                    att_line.float_to_time(att_line.time_end))
                start_datetime = user_tz.localize(
                    start_date, is_dst=None).astimezone(UTC).replace(
                        tzinfo=None)
                end_datetime = user_tz.localize(
                    end_date, is_dst=None).astimezone(UTC).replace(tzinfo=None)
                att_sheet_obj.create(_get_attendance_sheet_data(
                    att_line, start_datetime, end_datetime))
                continue
            dates_start = att_line._get_attendance_dates()
            for date in dates_start:
                start_date = datetime.combine(
                    date.date(), att_line.float_to_time(att_line.time_begin))
                end_date = datetime.combine(
                    date.date(), att_line.float_to_time(att_line.time_end))
                start_datetime = user_tz.localize(
                    start_date, is_dst=None).astimezone(UTC).replace(
                        tzinfo=None)
                end_datetime = user_tz.localize(
                    end_date, is_dst=None).astimezone(UTC).replace(tzinfo=None)
                if holidays_public_ids:
                    if holidays_public_ids.is_public_holiday(
                            start_datetime.astimezone(user_tz).date()):
                        continue
                att_sheet_obj.create(_get_attendance_sheet_data(
                    att_line, start_datetime, end_datetime))
            if not att_line.attendance_sheet_ids:
                raise exceptions.ValidationError(_(
                    'No attendance sheet generated, check dates'))
