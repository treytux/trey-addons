# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.addons.education.tests.test_enrollment import TestEnrollment
from openerp import tools
import os


class TestAttendanceSheet(TestEnrollment):

    def setUp(self):
        super(TestAttendanceSheet, self).setUp()
        # self.enrollment_01
        self.attendance_sheet_01 = self.env['edu.attendance.sheet'].create({
            'date': '2017-05-21',
            'teacher_id': self.teacher_01.id,
            'substitution': True,
            'substitute_teacher_id': self.teacher_02.id,
            'training_plan_line_id': self.training_plan_line_01.id,
            'attendance_line_ids': [
                (0, 0, {
                    'student_id': self.student_01.id,
                    'present': True,
                    'comments': 'All right!'})]})

    def test_print_attendance_sheet_report(self):
        instance_path = os.path.join(
            tools.config['test_report_directory'],
            'attendance_sheet_report.pdf')
        self.print_report(
            self.attendance_sheet_01,
            'education_attendance.edu_attendance_sheet',
            instance_path)
