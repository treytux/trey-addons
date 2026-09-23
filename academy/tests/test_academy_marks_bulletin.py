###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, timedelta

from odoo import exceptions

from .test_base import TestBase


class TestAcademyMarksBulletin(TestBase):
    def setUp(self):
        super().setUp()
        self.bulletin_obj = self.env['academy.marks.bulletin']
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
        self.activity_01.state = 'active'

    def test_bulletin_creation(self):
        bulletin = self.bulletin_obj.create({
            'name': self.student_01.id,
            'enrollment_id': self.enrollment_01.id,
        })
        self.assertEqual(bulletin.name, self.student_01)
        self.assertEqual(bulletin.enrollment_id, self.enrollment_01)
        self.assertEqual(bulletin.activity_id, self.activity_01)

    def test_duplicated_bulletin_validation(self):
        self.bulletin_obj.create({
            'name': self.student_01.id,
            'enrollment_id': self.enrollment_01.id,
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            self.bulletin_obj.create({
                'name': self.student_01.id,
                'enrollment_id': self.enrollment_01.id,
            })
        self.assertIn(
            'There can only be a bulletin for the same enrollment',
            result.exception.args[0])

    def test_invalid_student_enrollment(self):
        other_student = self.env['res.partner'].create({'name': 'Student'})
        with self.assertRaises(exceptions.ValidationError) as result:
            self.bulletin_obj.create({
                'name': other_student.id,
                'enrollment_id': self.enrollment_01.id,
            })
        self.assertIn(
            f'The selected enrollment "{self.enrollment_01.name}" does not '
            'belong to the selected student', result.exception.args[0])

    def test_bulletin_line_creation(self):
        bulletin = self.bulletin_obj.create({
            'name': self.student_01.id,
            'enrollment_id': self.enrollment_01.id,
        })
        bulletin.create_bulletin_lines(self.evaluation_01)
        self.assertEqual(len(bulletin.bulletin_line_ids), 1)
        line = bulletin.bulletin_line_ids[0]
        self.assertEqual(line.evaluation_id, self.evaluation_01)
        self.assertEqual(line.evaluable_concept_id, self.concept_01)
        self.assertEqual(line.student_id, self.student_01)

    def test_bulletin_line_mark_update(self):
        bulletin = self.bulletin_obj.create({
            'name': self.student_01.id,
            'enrollment_id': self.enrollment_01.id,
        })
        bulletin.create_bulletin_lines(self.evaluation_01)
        bulletin_line = bulletin.bulletin_line_ids[0]
        bulletin_line.write({'eval_concept_mark_id': self.mark_01.id})
        message = bulletin.message_ids[0]
        self.assertIn('Mark changed', message.body)
        self.assertIn(bulletin_line.activity_id.name, message.body)
        self.assertIn(bulletin_line.evaluable_concept_id.name, message.body)
        self.assertIn(self.mark_01.name, message.body)

    def test_has_pending_evaluation_computation(self):
        bulletin = self.bulletin_obj.create({
            'name': self.student_01.id,
            'enrollment_id': self.enrollment_01.id,
        })
        bulletin.create_bulletin_lines(self.evaluation_01)
        self.assertTrue(bulletin.has_pending_evaluation)
        bulletin.bulletin_line_ids.write({
            'eval_concept_mark_id': self.mark_01.id,
        })
        self.assertFalse(bulletin.has_pending_evaluation)

    def test_onchange_name_filters_enrollment(self):
        bulletin = self.bulletin_obj.new({
            'name': self.student_01.id,
        })
        bulletin._onchange_name()
        self.assertIn(self.enrollment_01, bulletin.enrollment_id)
