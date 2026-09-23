###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, timedelta

from odoo.addons.academy.tests.test_base import TestBase


class TestAttendanceSheet(TestBase):

    def setUp(self):
        super().setUp()
        today = datetime.now().date()
        self.last_month = (today.replace(day=1) - timedelta(days=1))
        self.attendance_sheet_01 = self.env[
            'academy.attendance.sheet'].create({
                'date': self.last_month,
                'teacher_id': self.teacher_01.id,
                'substitution': False,
                'filters': 'all',
                'activity_id': self.activity_01.id,
            })
        current_year = datetime.now().year
        first_day_of_year = datetime(current_year, 1, 1)
        days_to_first_tuesday = (1 - first_day_of_year.weekday() + 7) % 7
        first_tuesday_of_year = (
            first_day_of_year + timedelta(days=days_to_first_tuesday))
        self.hr_holidays_public = self.env['hr.holidays.public'].create({
            'year': current_year,
            'line_ids': [(0, 0, {
                'date': first_tuesday_of_year.strftime('%Y-%m-%d'),
                'name': 'First Tuesday of Year Holiday Test',
            })],
        })

    def test_attendance_sheet(self):
        enrollment_01 = self.env['academy.enrollment'].create({
            'start_date': datetime.now().replace(day=1, month=2),
            'end_date': datetime.now().replace(day=1, month=11),
            'training_plan_id': self.training_plan_01.id,
            'activity_id': self.activity_01.id,
            'student_id': self.student_01.id,
            'tutor_ids': [(6, 0, [self.father_01.id, self.mother_01.id])],
            'comments': 'Lorem ipsum',
        })
        enrollment_01._onchange_student_id()
        self.attendance_sheet_01.to_ready()
        self.assertEqual(len(self.attendance_sheet_01.attendance_line_ids), 0)
        enrollment_01.state = 'active'
        self.attendance_sheet_01.to_cancelled()
        self.attendance_sheet_01.to_draft()
        self.attendance_sheet_01.to_ready()
        self.assertEqual(len(self.attendance_sheet_01.attendance_line_ids), 1)
        self.attendance_sheet_01.to_cancelled()
        self.attendance_sheet_01.to_draft()
        self.attendance_sheet_01.filters = 'manual'
        self.attendance_sheet_01.to_ready()
        self.assertEqual(len(self.attendance_sheet_01.attendance_line_ids), 0)

    def test_activity_schedule(self):
        self.training_plan_01.hr_holiday_ids = self.hr_holidays_public.ids
        self.activity_01.write({
            'start_date': datetime.now().replace(day=1, month=1),
            'end_date': datetime.now().replace(day=15, month=7),
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'weekly',
                'weekday': '1',
            })],
        })
        self.assertEqual(self.activity_01.schedule, 'Tu(10:00 - 11:00)')
        self.activity_01.write({
            'start_date': datetime.now().replace(day=1, month=1),
            'end_date': datetime.now().replace(day=15, month=7),
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 11.,
                'time_end': 12.,
                'period': 'weekly',
                'weekday': '2',
            })],
        })
        self.assertEqual(
            self.activity_01.schedule, 'Tu(10:00 - 11:00)-We(11:00 - 12:00)')

    def test_attendance_sheet_generator_weekly_with_holiday(self):
        self.training_plan_01.hr_holiday_ids = self.hr_holidays_public.ids
        self.activity_01.write({
            'start_date': datetime.now().replace(day=1, month=1),
            'end_date': datetime.now().replace(day=15, month=7),
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'weekly',
                'weekday': '1',
            })],
        })
        plan_attendance_line = self.activity_01.plan_attendance_line_ids[0]
        plan_attendance_line.generate_attendances()
        self.assertEqual(len(plan_attendance_line.attendance_sheet_ids), 27)
        for attendance_sheet in plan_attendance_line.attendance_sheet_ids:
            self.assertEqual(attendance_sheet.date_start.weekday(), 1)
            self.assertEqual(attendance_sheet.date_end.weekday(), 1)
            self.assertTrue(attendance_sheet.date_start.date()
                            >= self.activity_01.start_date)
            self.assertTrue(attendance_sheet.date_start.date()
                            <= self.activity_01.end_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            >= self.activity_01.start_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            <= self.activity_01.end_date)

    def test_attendance_sheet_generator_biweekly_with_holiday(self):
        self.training_plan_01.hr_holiday_ids = self.hr_holidays_public.ids
        self.activity_01.write({
            'start_date': datetime.now().replace(day=1, month=1),
            'end_date': datetime.now().replace(day=15, month=7),
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'biweekly',
                'weekday': '1',
            })],
        })
        plan_attendance_line = self.activity_01.plan_attendance_line_ids[0]
        plan_attendance_line.generate_attendances()
        sessions_count = (
            self.hr_holidays_public.line_ids.date
            in plan_attendance_line.attendance_sheet_ids.mapped('date_start')
            and 13 or 14)
        self.assertEqual(
            len(plan_attendance_line.attendance_sheet_ids), sessions_count)
        for attendance_sheet in plan_attendance_line.attendance_sheet_ids:
            self.assertEqual(attendance_sheet.date_start.weekday(), 1)
            self.assertEqual(attendance_sheet.date_end.weekday(), 1)
            self.assertTrue(attendance_sheet.date_start.date()
                            > self.activity_01.start_date)
            self.assertTrue(attendance_sheet.date_start.date()
                            < self.activity_01.end_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            > self.activity_01.start_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            < self.activity_01.end_date)

    def test_attendance_sheet_generator_monthly_with_holiday(self):
        self.training_plan_01.hr_holiday_ids = self.hr_holidays_public.ids
        self.activity_01.write({
            'start_date': datetime.now().replace(day=1, month=1),
            'end_date': datetime.now().replace(day=15, month=7),
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'monthly',
                'weekday': '1',
            })],
        })
        plan_attendance_line = self.activity_01.plan_attendance_line_ids[0]
        plan_attendance_line.generate_attendances()
        self.assertEqual(len(plan_attendance_line.attendance_sheet_ids), 6)
        for attendance_sheet in plan_attendance_line.attendance_sheet_ids:
            self.assertEqual(attendance_sheet.date_start.weekday(), 1)
            self.assertEqual(attendance_sheet.date_end.weekday(), 1)
            self.assertTrue(attendance_sheet.date_start.date()
                            > self.activity_01.start_date)
            self.assertTrue(attendance_sheet.date_start.date()
                            < self.activity_01.end_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            > self.activity_01.start_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            < self.activity_01.end_date)

    def test_attendance_sheet_generator_bimonthly_with_holiday(self):
        self.training_plan_01.hr_holiday_ids = self.hr_holidays_public.ids
        self.activity_01.write({
            'start_date': datetime.now().replace(day=1, month=1),
            'end_date': datetime.now().replace(day=15, month=7),
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'bimonthly',
                'weekday': '1',
            })],
        })
        plan_attendance_line = self.activity_01.plan_attendance_line_ids[0]
        plan_attendance_line.generate_attendances()
        self.assertEqual(len(plan_attendance_line.attendance_sheet_ids), 3)
        for attendance_sheet in plan_attendance_line.attendance_sheet_ids:
            self.assertEqual(attendance_sheet.date_start.weekday(), 1)
            self.assertEqual(attendance_sheet.date_end.weekday(), 1)
            self.assertTrue(attendance_sheet.date_start.date()
                            > self.activity_01.start_date)
            self.assertTrue(attendance_sheet.date_start.date()
                            < self.activity_01.end_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            > self.activity_01.start_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            < self.activity_01.end_date)

    def test_attendance_sheet_generator_quaterly_with_holiday(self):
        self.training_plan_01.hr_holiday_ids = self.hr_holidays_public.ids
        self.activity_01.write({
            'start_date': datetime.now().replace(day=1, month=1),
            'end_date': datetime.now().replace(day=15, month=7),
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'quaterly',
                'weekday': '1',
            })],
        })
        plan_attendance_line = self.activity_01.plan_attendance_line_ids[0]
        plan_attendance_line.generate_attendances()
        self.assertEqual(len(plan_attendance_line.attendance_sheet_ids), 2)
        for attendance_sheet in plan_attendance_line.attendance_sheet_ids:
            self.assertEqual(attendance_sheet.date_start.weekday(), 1)
            self.assertEqual(attendance_sheet.date_end.weekday(), 1)
            self.assertTrue(attendance_sheet.date_start.date()
                            > self.activity_01.start_date)
            self.assertTrue(attendance_sheet.date_start.date()
                            < self.activity_01.end_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            > self.activity_01.start_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            < self.activity_01.end_date)

    def test_attendance_sheet_generator_yearly(self):
        self.activity_01.write({
            'start_date': datetime.now().replace(day=1, month=1),
            'end_date': datetime.now().replace(day=31, month=12),
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'yearly',
                'weekday': '1',
            })],
        })
        plan_attendance_line = self.activity_01.plan_attendance_line_ids[0]
        plan_attendance_line.generate_attendances()
        self.assertEqual(len(plan_attendance_line.attendance_sheet_ids), 1)
        for attendance_sheet in plan_attendance_line.attendance_sheet_ids:
            self.assertEqual(attendance_sheet.date_start.weekday(), 1)
            self.assertEqual(attendance_sheet.date_end.weekday(), 1)
            self.assertTrue(attendance_sheet.date_start.date()
                            > self.activity_01.start_date)
            self.assertTrue(attendance_sheet.date_start.date()
                            < self.activity_01.end_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            > self.activity_01.start_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            < self.activity_01.end_date)

    def test_attendance_sheet_generator_biannual_with_holiday(self):
        self.training_plan_01.hr_holiday_ids = self.hr_holidays_public.ids
        self.training_plan_01.end_date = datetime(
            datetime.now().year + 2, 12, 31)
        self.activity_01.write({
            'start_date': datetime.now().replace(day=1, month=1),
            'end_date': self.training_plan_01.end_date,
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'biannual',
                'weekday': '1',
            })],
        })
        plan_attendance_line = self.activity_01.plan_attendance_line_ids[0]
        plan_attendance_line.generate_attendances()
        self.assertEqual(len(plan_attendance_line.attendance_sheet_ids), 1)
        for attendance_sheet in plan_attendance_line.attendance_sheet_ids:
            self.assertEqual(attendance_sheet.date_start.weekday(), 1)
            self.assertEqual(attendance_sheet.date_end.weekday(), 1)
            self.assertTrue(attendance_sheet.date_start.date()
                            > self.activity_01.start_date)
            self.assertTrue(attendance_sheet.date_start.date()
                            < self.activity_01.end_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            > self.activity_01.start_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            < self.activity_01.end_date)

    def test_attendance_sheet_generator_special(self):
        self.activity_01.write({
            'start_date': datetime.now().replace(day=1, month=1),
            'end_date': datetime.now().replace(day=1, month=1),
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'special',
            })],
        })
        plan_attendance_line = self.activity_01.plan_attendance_line_ids[0]
        plan_attendance_line.generate_attendances()
        self.assertEqual(len(plan_attendance_line.attendance_sheet_ids), 1)
        attendance_sheet = plan_attendance_line.attendance_sheet_ids
        self.assertEqual(attendance_sheet.date_start.weekday(),
                         datetime.now().replace(day=1, month=1).weekday())
        self.assertEqual(attendance_sheet.date_end.weekday(),
                         datetime.now().replace(day=1, month=1).weekday())
        self.assertTrue(attendance_sheet.date_start.date()
                        == self.activity_01.start_date)
        self.assertTrue(attendance_sheet.date_start.date()
                        == self.activity_01.end_date)
        self.assertTrue(attendance_sheet.date_end.date()
                        == self.activity_01.start_date)
        self.assertTrue(attendance_sheet.date_end.date()
                        == self.activity_01.end_date)

    def test_attendance_sheet_generator_two_year_calendar_without_holiday(
            self):
        self.training_plan_01.end_date = datetime(
            datetime.now().year + 2, 7, 15)
        self.activity_01.write({
            'start_date': datetime.now().replace(day=1, month=1),
            'end_date': datetime(datetime.now().year + 1, 7, 15),
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'weekly',
                'weekday': '1',
            })],
        })
        plan_attendance_line = self.activity_01.plan_attendance_line_ids[0]
        plan_attendance_line.generate_attendances()
        self.assertEqual(len(plan_attendance_line.attendance_sheet_ids), 80)

    def test_attendance_sheet_generator_two_year_calendar_with_holiday(self):
        self.training_plan_01.end_date = datetime(
            datetime.now().year + 1, 7, 15)
        hr_holidays_public = self.env['hr.holidays.public'].create({
            'year': datetime.now().year + 1,
            'line_ids': [(0, 0, {
                'date': datetime(datetime.now().year + 1, 7, 1),
                'name': 'Holiday test',
            })],
        })
        self.training_plan_01.hr_holiday_ids = hr_holidays_public
        self.activity_01.write({
            'start_date': datetime.now().replace(day=1, month=1),
            'end_date': datetime(datetime.now().year + 1, 7, 15),
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'weekly',
                'weekday': '1',
            })],
        })
        plan_attendance_line = self.activity_01.plan_attendance_line_ids[0]
        plan_attendance_line.generate_attendances()
        self.assertEqual(len(plan_attendance_line.attendance_sheet_ids), 79)
