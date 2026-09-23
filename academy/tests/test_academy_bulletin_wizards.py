###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, timedelta

from odoo import exceptions

from .test_base import TestBase


class TestAcademyBulletinWizards(TestBase):
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
        self.enrollment_02 = self.env['academy.enrollment'].create({
            'training_plan_id': self.training_plan_01.id,
            'activity_id': self.activity_01.id,
            'student_id': self.student_02.id,
            'start_date': datetime.now() - timedelta(days=1),
            'end_date': datetime.now().replace(day=31, month=12),
            'comments': 'Lorem ipsum',
            'state': 'active',
        })
        self.enrollment_02._onchange_student_id()
        self.activity_01.state = 'active'
        self.wizard = self.env['academy.wizard.generate.bulletin'].with_context(
            {
                'active_model': 'academy.activity',
                'active_ids': self.activity_01.ids,
            }
        ).create({
            'evaluation_id': self.evaluation_01.id,
        })

    def test_wizard_generate_bulletins_successful_creation(self):
        self.wizard.button_accept()
        bulletins = self.env['academy.marks.bulletin'].search([])
        self.assertEqual(len(bulletins), 2)
        self.assertEqual(bulletins[0].activity_id, self.activity_01)
        self.assertEqual(bulletins[1].activity_id, self.activity_01)
        self.assertEqual(bulletins[0].name, self.student_01)
        self.assertEqual(bulletins[1].name, self.student_02)
        self.assertEqual(bulletins[0].enrollment_id, self.enrollment_01)
        self.assertEqual(bulletins[1].enrollment_id, self.enrollment_02)

    def test_duplicate_bulletins_not_created(self):
        bulletin = self.env['academy.marks.bulletin'].create({
            'name': self.student_01.id,
            'enrollment_id': self.enrollment_01.id,
        })
        self.wizard.button_accept()
        bulletins = self.env['academy.marks.bulletin'].search([
            ('enrollment_id', '=', self.enrollment_01.id),
        ])
        self.assertEqual(len(bulletins), 1)
        self.assertEqual(bulletins[0], bulletin)

    def test_evaluation_not_in_activity(self):
        wizard = self.env['academy.wizard.generate.bulletin'].with_context({
            'active_model': 'academy.activity',
            'active_ids': self.activity_01.ids,
        }).create({
            'evaluation_id': self.evaluation_02.id,
        })
        wizard.button_accept()
        bulletins = self.env['academy.marks.bulletin'].search([])
        self.assertEqual(len(bulletins), 0)

    def test_create_bulletin_lines_for_common_concepts(self):
        self.wizard.button_accept()
        bulletins = self.env['academy.marks.bulletin'].search([])
        self.assertTrue(bulletins)
        for bulletin in bulletins:
            self.assertTrue(bulletin.bulletin_line_ids)
            for line in bulletin.bulletin_line_ids:
                self.assertEqual(line.evaluation_id, self.evaluation_01)
                self.assertIn(
                    line.evaluable_concept_id,
                    self.activity_01.evaluable_concept_ids)

    def test_error_no_active_activity_selected(self):
        with self.assertRaises(exceptions.UserError) as result:
            wizard = self.env['academy.wizard.generate.bulletin'].with_context({
                'active_model': 'academy.activity',
                'active_ids': [],
            }).create({
                'evaluation_id': self.evaluation_01.id,
            })
            wizard.button_accept()
        self.assertEqual(
            'Please select one activity.', result.exception.args[0])

    def test_context_without_activity_model(self):
        with self.assertRaises(exceptions.UserError) as result:
            wizard = self.env['academy.wizard.generate.bulletin'].with_context(
                {
                    'active_model': 'res.partner',
                    'active_ids': [self.student_01.id],
                }
            ).create({
                'evaluation_id': self.evaluation_01.id,
            })
            wizard.button_accept()
        self.assertEqual(
            'Please select one activity.', result.exception.args[0])

    def test_bulletin_with_pending_evaluation(self):
        self.wizard.button_accept()
        bulletins = self.env['academy.marks.bulletin'].search([])
        for bulletin in bulletins:
            self.assertTrue(bulletin.has_pending_evaluation)

    def test_wizard_fill_bulletin_line_successful_creation(self):
        bulletin = self.env['academy.marks.bulletin'].create({
            'name': self.student_01.id,
            'enrollment_id': self.enrollment_01.id,
        })
        fill_wizard_line = self.env['academy.wizard.fill.bulletin.line']
        fill_wizard = fill_wizard_line.with_context({
            'active_model': 'academy.marks.bulletin',
            'active_id': bulletin.id,
        }).create({
            'evaluation_id': self.evaluation_01.id,
        })
        fill_wizard.button_accept()
        self.assertEqual(len(bulletin.bulletin_line_ids), 1)
        bulletin_line = bulletin.bulletin_line_ids[0]
        self.assertEqual(bulletin_line.evaluation_id, self.evaluation_01)
        self.assertEqual(bulletin_line.student_id, self.student_01)
        self.assertIn(
            bulletin_line.evaluable_concept_id,
            self.activity_01.evaluable_concept_ids)

    def test_wizard_publish_bulletins_lines(self):
        self.wizard.button_accept()
        bulletin_lines = self.env['academy.marks.bulletin.line'].search([
            ('activity_id', '=', self.activity_01.id),
            ('evaluation_id', '=', self.evaluation_01.id),
            ('portal_published', '=', False),
        ])
        self.assertTrue(len(bulletin_lines) > 0)
        self.assertEqual(len(bulletin_lines), 2)
        self.wizard = self.env['academy.publish.bulletin.lines'].with_context({
            'active_model': 'academy.activity',
            'active_ids': self.activity_01.ids,
        }).create({
            'evaluation_id': self.evaluation_01.id,
        })
        self.wizard.button_publish_bulletin_lines()
        self.assertTrue(bulletin_lines[0].portal_published)
        self.assertTrue(bulletin_lines[1].portal_published)
