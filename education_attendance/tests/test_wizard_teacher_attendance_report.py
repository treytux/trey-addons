###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.education.tests.test_base import TestBase


class TestWizardTeacherAttendanceReport(TestBase):

    def setUp(self):
        super().setUp()
        self.enrollment_01 = self.env['edu.enrollment'].create({
            'date': '2017-05-21',
            'training_plan_id': self.training_plan_01.id,
            'classroom_id': self.classroom_01.id,
            'student_id': self.student_01.id,
            'tutor_ids': [(6, 0, [self.father_01.id, self.mother_01.id])],
            'comments': 'Lorem ipsum',
        })
        self.enrollment_01._onchange_student_id()
        self.enrollment_01.to_active()
        self.attendance_sheet_01 = self.env['edu.attendance.sheet'].create({
            'date': '2017-05-21',
            'teacher_id': self.teacher_01.id,
            'substitution': True,
            'substitute_teacher_id': self.teacher_02.id,
            'training_plan_line_id': self.training_plan_line_01.id,
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
        wizard_1 = self.env['edu.wizard.teacher.attendance.report'].create({
            'teacher_id': self.teacher_01.id,
            'date_start': '2017-05-1',
            'date_end': '2017-05-31',
        })
        wizard_1.onchange_wizard_data()
        self.assertEquals(len(wizard_1.line_ids), 1)
        self.assertEquals(
            wizard_1.line_ids[0].attendance_sheet_id, self.attendance_sheet_01)
        self.assertEquals(wizard_1.total_classes, 1)
        self.assertEquals(wizard_1.total_minutes, 55)
        self.assertEquals(wizard_1.total_hours, 0.92)
        wizard_2 = self.env['edu.wizard.teacher.attendance.report'].create({
            'teacher_id': self.teacher_01.id,
            'date_start': '2017-06-1',
            'date_end': '2017-06-30',
        })
        wizard_2.onchange_wizard_data()
        self.assertEquals(len(wizard_2.line_ids), 0)
