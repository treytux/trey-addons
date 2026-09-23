###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from .test_base import TestBase


class TestEnrollment(TestBase):
    def setUp(self):
        super().setUp()
        data = {
            'date': '2017-05-21',
            'training_plan_id': self.training_plan_01.id,
            'classroom_id': self.classroom_01.id,
            'student_id': self.student_01.id,
            'tutor_ids': [(6, 0, [self.father_01.id, self.mother_01.id])],
            'comments': 'Lorem ipsum',
            'state': 'draft',
        }
        self.enrollment_01 = self.env['edu.enrollment'].create(data)
        self.enrollment_01._onchange_student_id()

    def test_education_wizard_migrate_student(self):
        self.enrollment_01.to_active()
        enrollments = self.env['edu.enrollment'].search([
            ('student_id', '=', self.student_01.id),
        ])
        self.assertEquals(len(enrollments), 1)
        wizard = self.env['edu.wizard.migrate.student'].create({
            'tp_origin_id': self.training_plan_01.id,
            'tp_dest_id': self.training_plan_02.id,
            'class_origin_id': self.classroom_01.id,
            'class_dest_id': self.classroom_02.id,
        })
        wizard._onchange_class_dest_id()
        wizard.button_migrate()
        self.assertEquals(self.enrollment_01.state, 'ended')
        enrollments = self.env['edu.enrollment'].search([
            ('student_id', '=', self.student_01.id),
        ])
        self.assertEquals(len(enrollments), 2)
        self.assertEquals(
            len(enrollments.filtered(lambda enr: enr.state == 'draft')), 1)

    def test_education_wizard_fill_subjects(self):
        self.enrollment_01.to_active()
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
        self.assertEquals(len(bulletin.evaluation_line_ids), 2)
        self.assertEquals(
            bulletin.evaluation_line_ids[0].subject_id.name, 'Subject 01')
        self.assertEquals(
            bulletin.evaluation_line_ids[1].subject_id.name, 'Subject 03')

    def test_education_wizard_enroll_student(self):
        enrollment = self.env['edu.enrollment'].search([
            ('student_id', '=', self.student_01.id),
        ], limit=1)
        wizard = self.env['edu.wizard.enroll.student'].create({
            'training_plan_id': self.training_plan_01.id,
            'classroom_id': self.classroom_01.id,
            'student_ids': [(6, 0, self.student_01.ids)],
        })
        wizard._onchange_classroom_id()
        self.assertEquals(enrollment.state, 'draft')
        self.assertEquals(len(wizard.student_enrolled_ids), 1)
        wizard.button_enroll()
        self.assertEquals(enrollment.state, 'active')
        self.assertEquals(enrollment.classroom_id.id, self.classroom_01.id)

    def test_education_wizard_generate_bulletins(self):
        self.enrollment_01.to_active()
        training_plan_line = self.training_plan_01.line_ids[0]
        wizard_ctx = {
            'active_model': 'edu.training.plan.line',
            'active_ids': training_plan_line.id,
        }
        wizard = self.env['edu.wizard.generate.bulletins'].with_context(
            wizard_ctx).create({
                'evaluation_id': self.evaluation_01.id,
            })
        wizard.button_accept()
        bulletin = self.env['edu.marks.bulletin'].search([
            ('name', '=', self.student_01.id),
            ('enrollment_id', '=', self.enrollment_01.id),
        ])
        self.assertEquals(len(bulletin.evaluation_line_ids), 2)
        self.assertEquals(
            bulletin.evaluation_line_ids[0].subject_id.name, 'Subject 01')
        self.assertEquals(
            bulletin.evaluation_line_ids[1].subject_id.name, 'Subject 03')

    def test_education_wizard_fill_subjects_with_concepts(self):
        concept_02 = self.env['edu.concept'].create({
            'name': 'Concept 02',
            'value_type': 'numeric',
            'values_valid': '1,2,3,4,5,6,7,8,9,10',
        })
        self.training_plan_line_01.subject_id.write({
            'evaluable_concept_ids': [(4, concept_02.id)]
        })
        self.assertEquals(len(
            self.training_plan_line_01.subject_id.evaluable_concept_ids), 2)
        self.enrollment_01.to_active()
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
        self.assertEquals(len(bulletin.evaluation_line_ids), 3)
        subject_1_concepts = bulletin.evaluation_line_ids.filtered(
            lambda line: line.subject_id.name == 'Subject 01')
        self.assertEquals(len(subject_1_concepts), 2)
        subject_2_concepts = bulletin.evaluation_line_ids.filtered(
            lambda line: line.subject_id.name == 'Subject 03')
        self.assertEquals(len(subject_2_concepts), 1)
