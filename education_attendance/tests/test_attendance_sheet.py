###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, timedelta

from odoo.addons.education.tests.test_base import TestBase


class TestAttendanceSheet(TestBase):

    def setUp(self):
        super().setUp()
        today = datetime.now().date()
        last_month = (today.replace(day=1) - timedelta(days=1))
        self.enrollment_01 = self.env['edu.enrollment'].create({
            'date': last_month,
            'training_plan_id': self.training_plan_01.id,
            'classroom_id': self.classroom_01.id,
            'student_id': self.student_01.id,
            'tutor_ids': [(6, 0, [self.father_01.id, self.mother_01.id])],
            'comments': 'Lorem ipsum',
        })
        self.enrollment_01._onchange_student_id()
        self.attendance_sheet_01 = self.env['edu.attendance.sheet'].create({
            'date': last_month,
            'teacher_id': self.teacher_01.id,
            'substitution': False,
            'filters': 'all',
            'training_plan_line_id': self.training_plan_line_01.id,
        })
        self.hr_holidays_public = self.env['hr.holidays.public'].create({
            'year': 2024,
            'line_ids': [(0, 0, {
                'date': '2024-01-02',
                'name': 'Holiday test',
            })],
        })

    def test_test_attendance_sheet(self):
        self.attendance_sheet_01.to_ready()
        self.assertEquals(len(self.attendance_sheet_01.attendance_line_ids), 0)
        self.enrollment_01.to_active()
        self.attendance_sheet_01.to_cancelled()
        self.attendance_sheet_01.to_draft()
        self.attendance_sheet_01.to_ready()
        self.assertEquals(len(self.attendance_sheet_01.attendance_line_ids), 1)
        self.attendance_sheet_01.to_cancelled()
        self.attendance_sheet_01.to_draft()
        self.attendance_sheet_01.filters = 'manual'
        self.attendance_sheet_01.to_ready()
        self.assertEquals(len(self.attendance_sheet_01.attendance_line_ids), 0)

    def test_check_student_attendance_email(self):
        self.student_01.tutor_ids = [
            (6, 0, [self.father_01.id, self.mother_01.id])]
        self.enrollment_01.to_active()
        self.attendance_sheet_01.to_ready()
        self.assertEquals(len(self.attendance_sheet_01.attendance_line_ids), 1)
        before_mails = self.env['mail.mail'].search([
            ('recipient_ids', 'in', [self.father_01.id, self.mother_01.id]),
        ])
        self.student_01._send_student_attendance_email()
        after_mails = self.env['mail.mail'].search([
            ('recipient_ids', 'in', [self.father_01.id, self.mother_01.id]),
        ])
        my_mail = after_mails - before_mails
        self.assertFalse(my_mail)
        self.attendance_sheet_01.attendance_line_ids.present = False
        self.student_01._send_student_attendance_email()
        after_mails = self.env['mail.mail'].search([
            ('recipient_ids', 'in', [self.father_01.id, self.mother_01.id]),
        ])
        my_mail = after_mails - before_mails
        self.assertEquals(len(my_mail), 2)

    def test_training_plan_line_schedule(self):
        training_plan = self.env.ref('education.training_plan_01')
        training_plan.hr_holiday_id = self.hr_holidays_public.id
        training_plan_line = self.env.ref('education.training_plan_line_01')
        training_plan_line.write({
            'start_date': '2024-01-01',
            'end_date': '2024-07-15',
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'weekly',
                'weekday': 'tuesday',
            })],
        })
        self.assertEquals(training_plan_line.schedule, 'T(10:00:00 - 11:00:00)')
        training_plan_line.write({
            'start_date': '2024-01-01',
            'end_date': '2024-07-15',
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 11.,
                'time_end': 12.,
                'period': 'weekly',
                'weekday': 'wednesday',
            })],
        })
        self.assertEquals(
            training_plan_line.schedule,
            'T(10:00:00 - 11:00:00)-W(11:00:00 - 12:00:00)')

    def test_attendance_sheet_generator_weekly_with_holiday(self):
        training_plan = self.env.ref('education.training_plan_01')
        training_plan.hr_holiday_id = self.hr_holidays_public.id
        training_plan_line = self.env.ref('education.training_plan_line_01')
        training_plan_line.write({
            'start_date': '2024-01-01',
            'end_date': '2024-07-15',
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'weekly',
                'weekday': 'tuesday',
            })],
        })
        plan_attendance_line = training_plan_line.plan_attendance_line_ids[0]
        plan_attendance_line.generate_attendances()
        self.assertEquals(len(plan_attendance_line.attendance_sheet_ids), 27)
        for attendance_sheet in plan_attendance_line.attendance_sheet_ids:
            self.assertEquals(attendance_sheet.date_start.weekday(), 1)
            self.assertEquals(attendance_sheet.date_end.weekday(), 1)
            self.assertTrue(attendance_sheet.date_start.date()
                            > training_plan_line.start_date)
            self.assertTrue(attendance_sheet.date_start.date()
                            < training_plan_line.end_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            > training_plan_line.start_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            < training_plan_line.end_date)

    def test_attendance_sheet_generator_biweekly_with_holiday(self):
        training_plan = self.env.ref('education.training_plan_01')
        training_plan.hr_holiday_id = self.hr_holidays_public.id
        training_plan_line = self.env.ref('education.training_plan_line_01')
        training_plan_line.write({
            'start_date': '2024-01-01',
            'end_date': '2024-07-15',
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'biweekly',
                'weekday': 'tuesday',
            })],
        })
        plan_attendance_line = training_plan_line.plan_attendance_line_ids[0]
        plan_attendance_line.generate_attendances()
        self.assertEquals(len(plan_attendance_line.attendance_sheet_ids), 14)
        for attendance_sheet in plan_attendance_line.attendance_sheet_ids:
            self.assertEquals(attendance_sheet.date_start.weekday(), 1)
            self.assertEquals(attendance_sheet.date_end.weekday(), 1)
            self.assertTrue(attendance_sheet.date_start.date()
                            > training_plan_line.start_date)
            self.assertTrue(attendance_sheet.date_start.date()
                            < training_plan_line.end_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            > training_plan_line.start_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            < training_plan_line.end_date)

    def test_attendance_sheet_generator_monthly_with_holiday(self):
        training_plan = self.env.ref('education.training_plan_01')
        training_plan.hr_holiday_id = self.hr_holidays_public.id
        training_plan_line = self.env.ref('education.training_plan_line_01')
        training_plan_line.write({
            'start_date': '2024-01-01',
            'end_date': '2024-07-15',
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'monthly',
                'weekday': 'tuesday',
            })],
        })
        plan_attendance_line = training_plan_line.plan_attendance_line_ids[0]
        plan_attendance_line.generate_attendances()
        self.assertEquals(len(plan_attendance_line.attendance_sheet_ids), 6)
        for attendance_sheet in plan_attendance_line.attendance_sheet_ids:
            self.assertEquals(attendance_sheet.date_start.weekday(), 1)
            self.assertEquals(attendance_sheet.date_end.weekday(), 1)
            self.assertTrue(attendance_sheet.date_start.date()
                            > training_plan_line.start_date)
            self.assertTrue(attendance_sheet.date_start.date()
                            < training_plan_line.end_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            > training_plan_line.start_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            < training_plan_line.end_date)

    def test_attendance_sheet_generator_bimonthly_with_holiday(self):
        training_plan = self.env.ref('education.training_plan_01')
        training_plan.hr_holiday_id = self.hr_holidays_public.id
        training_plan_line = self.env.ref('education.training_plan_line_01')
        training_plan_line.write({
            'start_date': '2024-01-01',
            'end_date': '2024-07-15',
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'bimonthly',
                'weekday': 'tuesday',
            })],
        })
        plan_attendance_line = training_plan_line.plan_attendance_line_ids[0]
        plan_attendance_line.generate_attendances()
        self.assertEquals(len(plan_attendance_line.attendance_sheet_ids), 3)
        for attendance_sheet in plan_attendance_line.attendance_sheet_ids:
            self.assertEquals(attendance_sheet.date_start.weekday(), 1)
            self.assertEquals(attendance_sheet.date_end.weekday(), 1)
            self.assertTrue(attendance_sheet.date_start.date()
                            > training_plan_line.start_date)
            self.assertTrue(attendance_sheet.date_start.date()
                            < training_plan_line.end_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            > training_plan_line.start_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            < training_plan_line.end_date)

    def test_attendance_sheet_generator_quaterly_with_holiday(self):
        training_plan = self.env.ref('education.training_plan_01')
        training_plan.hr_holiday_id = self.hr_holidays_public.id
        training_plan_line = self.env.ref('education.training_plan_line_01')
        training_plan_line.write({
            'start_date': '2024-01-01',
            'end_date': '2024-07-15',
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'quaterly',
                'weekday': 'tuesday',
            })],
        })
        plan_attendance_line = training_plan_line.plan_attendance_line_ids[0]
        plan_attendance_line.generate_attendances()
        self.assertEquals(len(plan_attendance_line.attendance_sheet_ids), 2)
        for attendance_sheet in plan_attendance_line.attendance_sheet_ids:
            self.assertEquals(attendance_sheet.date_start.weekday(), 1)
            self.assertEquals(attendance_sheet.date_end.weekday(), 1)
            self.assertTrue(attendance_sheet.date_start.date()
                            > training_plan_line.start_date)
            self.assertTrue(attendance_sheet.date_start.date()
                            < training_plan_line.end_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            > training_plan_line.start_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            < training_plan_line.end_date)

    def test_attendance_sheet_generator_yearly(self):
        training_plan_line = self.env.ref('education.training_plan_line_01')
        training_plan_line.write({
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'yearly',
                'weekday': 'tuesday',
            })],
        })
        plan_attendance_line = training_plan_line.plan_attendance_line_ids[0]
        plan_attendance_line.generate_attendances()
        self.assertEquals(len(plan_attendance_line.attendance_sheet_ids), 1)
        for attendance_sheet in plan_attendance_line.attendance_sheet_ids:
            self.assertEquals(attendance_sheet.date_start.weekday(), 1)
            self.assertEquals(attendance_sheet.date_end.weekday(), 1)
            self.assertTrue(attendance_sheet.date_start.date()
                            > training_plan_line.start_date)
            self.assertTrue(attendance_sheet.date_start.date()
                            < training_plan_line.end_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            > training_plan_line.start_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            < training_plan_line.end_date)

    def test_attendance_sheet_generator_biannual_with_holiday(self):
        training_plan = self.env.ref('education.training_plan_01')
        training_plan.hr_holiday_id = self.hr_holidays_public.id
        training_plan_line = self.env.ref('education.training_plan_line_01')
        training_plan_line.write({
            'start_date': '2024-01-01',
            'end_date': '2027-01-03',
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'biannual',
                'weekday': 'tuesday',
            })],
        })
        plan_attendance_line = training_plan_line.plan_attendance_line_ids[0]
        plan_attendance_line.generate_attendances()
        self.assertEquals(len(plan_attendance_line.attendance_sheet_ids), 1)
        for attendance_sheet in plan_attendance_line.attendance_sheet_ids:
            self.assertEquals(attendance_sheet.date_start.weekday(), 1)
            self.assertEquals(attendance_sheet.date_end.weekday(), 1)
            self.assertTrue(attendance_sheet.date_start.date()
                            > training_plan_line.start_date)
            self.assertTrue(attendance_sheet.date_start.date()
                            < training_plan_line.end_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            > training_plan_line.start_date)
            self.assertTrue(attendance_sheet.date_end.date()
                            < training_plan_line.end_date)

    def test_attendance_sheet_generator_special(self):
        training_plan_line = self.env.ref('education.training_plan_line_01')
        training_plan_line.write({
            'start_date': '2024-01-01',
            'end_date': '2024-01-01',
            'plan_attendance_line_ids': [(0, 0, {
                'teacher_id': self.teacher_01.id,
                'time_begin': 10.,
                'time_end': 11.,
                'period': 'special',
            })],
        })
        plan_attendance_line = training_plan_line.plan_attendance_line_ids[0]
        plan_attendance_line.generate_attendances()
        self.assertEquals(len(plan_attendance_line.attendance_sheet_ids), 1)
        attendance_sheet = plan_attendance_line.attendance_sheet_ids
        self.assertEquals(attendance_sheet.date_start.weekday(), 0)
        self.assertEquals(attendance_sheet.date_end.weekday(), 0)
        self.assertTrue(attendance_sheet.date_start.date()
                        == training_plan_line.start_date)
        self.assertTrue(attendance_sheet.date_start.date()
                        == training_plan_line.end_date)
        self.assertTrue(attendance_sheet.date_end.date()
                        == training_plan_line.start_date)
        self.assertTrue(attendance_sheet.date_end.date()
                        == training_plan_line.end_date)
