###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, timedelta

from odoo.addons.academy.tests.test_base import TestBase


class TestWizardTeacherAttendanceReport(TestBase):

    def setUp(self):
        super().setUp()
        self.enrollment_01 = self.env['academy.enrollment'].create({
            'training_plan_id': self.training_plan_01.id,
            'activity_id': self.activity_01.id,
            'student_id': self.student_01.id,
            'start_date': datetime.now() - timedelta(days=1),
            'end_date': datetime.now().replace(day=31, month=12),
            'comments': 'Lorem ipsum',
            'state': 'active',
        })
        self.enrollment_01._onchange_student_id()
        self.enrollment_01._onchange_activity_id()
        self.attendance_sheet_01 = self.env[
            'academy.attendance.sheet'].create({
                'date': datetime.now() + timedelta(days=1),
                'teacher_id': self.teacher_01.id,
                'substitution': True,
                'substitute_teacher_id': self.teacher_02.id,
                'activity_id': self.activity_01.id,
                'state': 'ended',
                'attendance_line_ids': [
                    (0, 0, {
                        'student_id': self.student_01.id,
                        'present': True,
                        'comments': 'All right!',
                    }),
                ],
            })

    def test_wizard_teacher_attendance(self):
        wizard_1 = self.env[
            'academy.wizard.teacher.attendance.report'].create({
                'teacher_id': self.teacher_01.id,
                'date_start': datetime.now(),
                'date_end': datetime.now() + timedelta(days=30),
            })
        wizard_1.onchange_wizard_data()
        self.assertEqual(len(wizard_1.line_ids), 1)
        self.assertEqual(
            wizard_1.line_ids[0].attendance_sheet_id, self.attendance_sheet_01)
        self.assertEqual(wizard_1.total_classes, 1)
        self.assertEqual(wizard_1.total_minutes, 60)
        self.assertEqual(wizard_1.total_hours, 1)
        wizard_2 = self.env[
            'academy.wizard.teacher.attendance.report'].create({
                'teacher_id': self.teacher_01.id,
                'date_start': datetime.now() + timedelta(days=90),
                'date_end': datetime.now() + timedelta(days=120),
            })
        wizard_2.onchange_wizard_data()
        self.assertEqual(len(wizard_2.line_ids), 0)
