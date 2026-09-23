###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import date, datetime, timedelta

from odoo.exceptions import UserError, ValidationError

from .test_base import TestBase


class TestAcademyEnrollment(TestBase):
    def setUp(self):
        super().setUp()
        self.enrollment_01 = self.env['academy.enrollment'].create({
            'training_plan_id': self.training_plan_01.id,
            'activity_id': self.activity_01.id,
            'student_id': self.student_01.id,
            'start_date': datetime.now() - timedelta(days=1),
            'end_date': datetime.now().replace(day=31, month=12),
            'comments': 'Lorem ipsum',
        })
        self.enrollment_01._onchange_student_id()
        self.enrollment_01._onchange_activity_id()

    def test_create_enrollment_default_state(self):
        self.assertEqual(self.enrollment_01.state, 'pending_level')
        self.assertEqual(self.enrollment_01.student_id, self.student_01)
        self.assertEqual(self.enrollment_01.activity_id, self.activity_01)

    def test_limit_student_activity(self):
        data = {
            'training_plan_id': self.training_plan_01.id,
            'activity_id': self.activity_01.id,
            'student_id': self.student_02.id,
            'start_date': datetime.now() - timedelta(days=1),
            'end_date': datetime.now().replace(day=31, month=12),
        }
        self.activity_01.student_limit = 0
        with self.assertRaises(UserError) as result:
            self.enrollment_01.state = 'active'
        self.assertIn('Limit of students reached', result.exception.args[0])
        with self.assertRaises(UserError) as result:
            self.enrollment_02 = self.env['academy.enrollment'].create(data)
        self.assertIn('Limit of students reached', result.exception.args[0])
        self.assertEqual(self.enrollment_01.state, 'pending_level')
        self.activity_01.student_limit = 2
        self.enrollment_01.state = 'active'
        self.enrollment_02 = self.env['academy.enrollment'].create(data)
        self.enrollment_02.state = 'active'
        self.assertEqual(self.enrollment_01.state, 'active')
        self.assertEqual(self.enrollment_02.state, 'active')

    def test_limit_student_activity_can_be_disabled(self):
        self.env.company.check_student_limits = False
        self.activity_01.student_limit = 0
        enrollment = self.env['academy.enrollment'].create({
            'training_plan_id': self.training_plan_01.id,
            'activity_id': self.activity_01.id,
            'student_id': self.student_02.id,
            'start_date': datetime.now() - timedelta(days=1),
            'end_date': datetime.now().replace(day=31, month=12),
        })
        enrollment.state = 'active'
        self.assertEqual(enrollment.state, 'active')

    def test_finish_enrollments(self):
        training_plan = self.env['academy.training.plan'].create({
            'name': 'Trainig Plan Test',
            'user_id': self.manager_01.id,
            'start_date': date.today() - timedelta(days=30),
            'end_date': date.today() + timedelta(days=30),
        })
        activity = self.env['academy.activity'].create({
            'name': 'Activity Test',
            'training_plan_id': training_plan.id,
            'user_id': self.manager_01.id,
            'start_date': date.today() - timedelta(days=30),
            'end_date': date.today() + timedelta(days=30),
            'teacher_id': self.teacher_01.id,
        })
        enrollment = self.env['academy.enrollment'].create({
            'training_plan_id': training_plan.id,
            'activity_id': activity.id,
            'student_id': self.student_01.id,
            'comments': 'Lorem ipsum',
        })
        enrollment._onchange_student_id()
        enrollment._onchange_activity_id()
        self.assertEqual(training_plan.state, 'in_progress')
        self.assertEqual(activity.state, 'draft')
        self.assertEqual(enrollment.state, 'pending_level')
        enrollment._cron_check_enrollments_state()
        self.assertEqual(training_plan.state, 'in_progress')
        self.assertEqual(activity.state, 'draft')
        self.assertEqual(enrollment.state, 'pending_level')
        yesterday = date.today() - timedelta(days=1)
        enrollment.end_date = yesterday
        activity.end_date = yesterday
        training_plan.end_date = yesterday
        enrollment._cron_check_enrollments_state()
        self.assertEqual(training_plan.state, 'closed')
        self.assertEqual(activity.state, 'ended')
        self.assertEqual(enrollment.state, 'cancelled')
        enrollment.state = 'active'
        self.assertEqual(enrollment.state, 'active')
        enrollment.finish_enrollments(activity)
        self.assertEqual(enrollment.state, 'ended')
        self.assertEqual(len(self.student_01.tutor_ids), 1)
        self.assertEqual(self.student_01.tutor_ids.students_enrollment_count, 2)

    def test_update_academic_training_in_student_from_enrollment(self):
        self.assertEqual(
            self.student_01.academic_training_ids, self.academic_training_01)
        self.enrollment_01._onchange_student_id()
        self.assertEqual(
            self.enrollment_01.academic_training_ids, self.academic_training_01)
        self.enrollment_01.academic_training_ids = self.academic_training_02
        self.assertEqual(
            self.student_01.academic_training_ids, self.academic_training_02)

    def test_raise_duplicate_enrollment(self):
        self.assertEqual(self.enrollment_01.student_id, self.student_01)
        self.assertEqual(self.enrollment_01.activity_id, self.activity_01)
        with self.assertRaises(ValidationError) as result:
            self.enrollment_02 = self.env['academy.enrollment'].create({
                'training_plan_id': self.training_plan_01.id,
                'activity_id': self.activity_01.id,
                'student_id': self.student_01.id,
                'start_date': datetime.now() - timedelta(days=1),
                'end_date': datetime.now().replace(day=31, month=12),
            })
        self.assertIn(
            'There are duplicate active enrollments', result.exception.args[0])

    def test_check_training_plan_activity_relation(self):
        self.assertEqual(
            self.enrollment_01.training_plan_id, self.training_plan_01)
        self.assertEqual(self.enrollment_01.activity_id, self.activity_01)
        with self.assertRaises(ValidationError) as result:
            self.enrollment_01.activity_id = self.activity_02
        self.assertIn(
            'The selected activity does not belong to the chosen training plan',
            result.exception.args[0])

    def test_academy_maks_bulletin_lines_mark_tacking(self):
        self.enrollment_01.state = 'active'
        bulletin = self.env['academy.marks.bulletin'].create({
            'name': self.student_01.id,
            'enrollment_id': self.enrollment_01.id,
            'activity_id': self.activity_01.id,
            'promote': 'promote',
            'observations': 'comments',
        })
        wizard = self.env['academy.wizard.fill.bulletin.line'].with_context(
            active_id=bulletin.id).create({
                'evaluation_id': self.evaluation_01.id,
            })
        wizard.button_accept()
        self.assertEqual(len(bulletin.bulletin_line_ids), 1)
        self.assertEqual(len(bulletin.message_ids), 1)
        self.assertTrue(bulletin.has_pending_evaluation)
        bulletin.bulletin_line_ids.eval_concept_mark_id = self.mark_01
        self.assertEqual(len(bulletin.message_ids), 2)
        self.assertIn(self.mark_01.name, bulletin.message_ids[0].body)
        bulletin.bulletin_line_ids.eval_concept_mark_id = self.mark_02
        self.assertEqual(len(bulletin.message_ids), 3)
        self.assertIn(self.mark_02.name, bulletin.message_ids[0].body)
        self.assertFalse(bulletin.has_pending_evaluation)

    def test_enrollment_date_constraint(self):
        with self.assertRaises(ValidationError) as result:
            self.enrollment_01.start_date = \
                self.enrollment_01.end_date + timedelta(days=1)
        self.assertIn(
            'Start date must be equal or before than date end.',
            result.exception.args[0])
        with self.assertRaises(ValidationError) as result:
            self.enrollment_01.start_date = \
                self.enrollment_01.start_date - timedelta(days=1)
        self.assertIn(
            f'The dates ({self.enrollment_01.name}) '
            f'must be between {self.enrollment_01.activity_id.start_date} and '
            f'{self.enrollment_01.activity_id.end_date}',
            result.exception.args[0])
        with self.assertRaises(ValidationError) as result:
            self.enrollment_01.end_date = \
                self.enrollment_01.end_date + timedelta(days=1)
        self.assertIn(
            f'The dates ({self.enrollment_01.name}) '
            f'must be between {self.enrollment_01.activity_id.start_date} and '
            f'{self.enrollment_01.activity_id.end_date}',
            result.exception.args[0])

    def test_enrollment_unique_constraint(self):
        self.enrollment_01.state = 'active'
        with self.assertRaises(ValidationError) as result:
            self.env['academy.enrollment'].create({
                'student_id': self.student_01.id,
                'activity_id': self.activity_01.id,
                'training_plan_id': self.training_plan_01.id,
                'start_date': datetime.now() - timedelta(days=1),
                'end_date': datetime.now().replace(day=31, month=12),
                'state': 'active',
            })
        self.assertIn(
            'There are duplicate active enrollments', result.exception.args[0])

    def test_avoid_cron_errors_in_enrollment_checks(self):
        self.enrollment_01.state = 'active'
        enrollment_2 = self.env['academy.enrollment'].with_context(
            skip_enrollment_checks=True).create({
                'student_id': self.student_01.id,
                'activity_id': self.activity_01.id,
                'training_plan_id': self.training_plan_01.id,
                'start_date': datetime.now() - timedelta(days=2),
                'end_date': datetime.now() - timedelta(days=1),
                'state': 'active',
            })
        self.env['academy.enrollment']._cron_check_enrollments_state()
        self.assertEqual(enrollment_2.state, 'ended')

    def test_enrollment_onchange_student_id(self):
        self.enrollment_01.student_id = self.student_02
        self.enrollment_01._onchange_student_id()
        self.assertEqual(
            self.enrollment_01.tutor_ids, self.student_02.tutor_ids)
        self.assertEqual(
            self.enrollment_01.academic_training_ids,
            self.student_02.academic_training_ids)

    def test_enrollment_onchange_training_plan_id(self):
        self.training_plan_01.typology_id = self.env['academy.typology'].create(
            {
                'name': 'Standard Typology',
                'enrollment_conditions': 'Standard enrollment conditions.',
            }
        )
        enrollment = self.env['academy.enrollment'].new({
            'training_plan_id': self.training_plan_01.id,
        })
        enrollment._onchange_training_plan_id()
        self.assertEqual(enrollment.comments, 'Standard enrollment conditions.')
