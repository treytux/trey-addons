###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import datetime

from odoo import fields
from odoo.exceptions import UserError, ValidationError

from .test_base import TestBase


class TestEducation(TestBase):
    def setUp(self):
        super().setUp()
        data = {
            'date': '2017-05-21',
            'training_plan_id': self.training_plan_01.id,
            'classroom_id': self.classroom_01.id,
            'student_id': self.student_01.id,
            'tutor_ids': [(6, 0, [self.father_01.id, self.mother_01.id])],
            'comments': 'Lorem ipsum',
        }
        self.enrollment_01 = self.env['edu.enrollment'].create(data)
        self.enrollment_01._onchange_student_id()

    def test_active(self):
        self.classroom_01.student_limit = 0
        with self.assertRaises(UserError):
            self.enrollment_01.to_active()
        self.assertEqual(self.enrollment_01.state, 'draft')
        self.classroom_01.student_limit = 1
        self.enrollment_01.to_active()
        self.assertEqual(self.enrollment_01.state, 'active')

    def test_limit_classroom(self):
        self.enrollment_01.to_active()
        self.assertEqual(self.enrollment_01.state, 'active')

    def test_cancelled(self):
        self.enrollment_01.to_cancelled()
        self.assertEqual(self.enrollment_01.state, 'cancelled')

    def test_ended(self):
        self.enrollment_01.to_ended()
        self.assertEqual(self.enrollment_01.state, 'draft')
        self.enrollment_01.classroom_id = self.classroom_01.id
        self.enrollment_01.to_active()
        self.enrollment_01.to_ended()
        self.assertEqual(self.enrollment_01.state, 'ended')

    def test_draft(self):
        self.enrollment_01.to_draft()
        self.assertEqual(self.enrollment_01.state, 'draft')

    def test_onchange_student_id(self):
        self.assertEqual(
            self.enrollment_01.tutor_ids, self.student_01.tutor_ids)
        self.student = self.env['res.partner'].create({
            'name': 'Student test2',
        })
        self.enrollment_01._onchange_student_id()
        self.assertEqual(self.enrollment_01.tutor_ids, self.student.tutor_ids)

    def test_onchange_training_plan_id(self):
        self.training_plan = self.env['edu.training.plan'].create({
            'name': 'Training plan test 2',
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today() + datetime.timedelta(days=90),
        })
        self.assertEqual(self.enrollment_01.comments, 'Lorem ipsum')

    def test_raise_duplicate_enrollment(self):
        data = {
            'date': '2017-05-25',
            'training_plan_id': self.training_plan_01.id,
            'classroom_id': self.classroom_01.id,
            'student_id': self.student_01.id,
            'tutor_ids': [(6, 0, [self.father_01.id, self.mother_01.id])],
            'comments': 'tutu',
        }
        self.enrollment_01.to_active()
        with self.assertRaises(ValidationError):
            self.env['edu.enrollment'].create(data)

    def test_education_maks_evaluation_lines_mark_tacking(self):
        concept_02 = self.env['edu.concept'].create({
            'name': 'Concept 02',
            'value_type': 'numeric',
            'values_valid': '1,2,3,4,5,6,7,8,9,10',
        })
        self.training_plan_line_01.subject_id.write({
            'evaluable_concept_ids': [(4, concept_02.id)],
        })
        self.assertEqual(len(
            self.training_plan_line_01.subject_id.evaluable_concept_ids), 2)
        self.enrollment_01.to_active()
        self.enrollment_01.fill_subjects()
        enrollment = self.env['edu.enrollment'].search([
            ('student_id', '=', self.student_01.id),
        ], limit=1)
        bulletin = self.env['edu.marks.bulletin'].create({
            'name': self.student_01.id,
            'enrollment_id': enrollment.id,
            'classroom_id': self.classroom_01.id,
            'promote': 'promote',
            'observations': 'comments',
        })
        wizard = self.env['edu.wizard.fill.subjects'].with_context(
            active_id=bulletin.id).create({
                'evaluation_id': self.evaluation_01.id,
            })
        wizard.button_accept()
        self.assertEqual(len(bulletin.evaluation_line_ids), 3)
        subject_1_concepts = bulletin.evaluation_line_ids.filtered(
            lambda line: line.subject_id.name == 'Subject 01')
        self.assertEqual(len(subject_1_concepts), 2)
        subject_2_concepts = bulletin.evaluation_line_ids.filtered(
            lambda line: line.subject_id.name == 'Subject 03')
        self.assertEqual(len(subject_2_concepts), 1)
        self.assertEqual(len(bulletin.message_ids), 1)
        with self.assertRaises(ValidationError):
            bulletin.evaluation_line_ids[1].write({'mark': 'PA'})
        bulletin.evaluation_line_ids[1].mark = 5
        self.assertEqual(len(bulletin.message_ids), 2)
        self.assertIn(
            bulletin.evaluation_line_ids[1].subject_id.name,
            bulletin.message_ids[0].body)
        self.assertIn(
            bulletin.evaluation_line_ids[1].evaluation_id.name,
            bulletin.message_ids[0].body)
        self.assertIn(
            bulletin.evaluation_line_ids[1].concept_id.name,
            bulletin.message_ids[0].body)
        self.assertTrue(bulletin.has_pending_evaluation)
        for ev_line in bulletin.evaluation_line_ids:
            if ev_line.concept_id.values_valid:
                ev_line.mark = ev_line.concept_id.values_valid.split(',')[0]
            else:
                ev_line.mark = 5
        self.assertFalse(bulletin.has_pending_evaluation)
