###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import date, timedelta

from odoo.exceptions import ValidationError

from .test_base import TestBase


class TestAcademyTrainingPlanAndActivity(TestBase):
    def setUp(self):
        super().setUp()
        last_month = date.today() - timedelta(days=30)
        next_month = date.today() + timedelta(days=30)
        self.training_plan_03 = self.env['academy.training.plan'].create({
            'name': 'Trainig Plan Test',
            'user_id': self.manager_01.id,
            'start_date': last_month,
            'end_date': next_month,
        })
        self.activity_03 = self.env['academy.activity'].create({
            'name': 'Activity Test',
            'training_plan_id': self.training_plan_03.id,
            'user_id': self.manager_01.id,
            'start_date': last_month,
            'end_date': next_month,
            'teacher_id': self.teacher_01.id,
        })
        self.enrollment_03 = self.env['academy.enrollment'].create({
            'training_plan_id': self.training_plan_03.id,
            'activity_id': self.activity_03.id,
            'student_id': self.student_01.id,
            'start_date': last_month,
            'end_date': next_month,
        })

    def test_training_plan_date_constraint(self):
        with self.assertRaises(ValidationError) as result:
            self.training_plan_03.write({
                'start_date': date(2024, 12, 31),
                'end_date': date(2024, 1, 1),
            })
        self.assertIn(
            'Start date cannot be later than the end', result.exception.args[0])
        with self.assertRaises(ValidationError) as result:
            self.training_plan_03.write({
                'start_date': date.today(),
            })
        self.assertIn(
            'The dates of the activity (Activity Test) must be compatible '
            'with the dates of the training plan.', result.exception.args[0])
        with self.assertRaises(ValidationError) as result:
            self.training_plan_03.write({
                'end_date': date.today(),
            })
        self.assertIn(
            'The dates of the activity (Activity Test) must be compatible '
            'with the dates of the training plan.', result.exception.args[0])

    def test_close_active_training_plans(self):
        yesterday = date.today() - timedelta(days=1)
        self.enrollment_03.end_date = yesterday
        self.activity_03.end_date = yesterday
        self.training_plan_03.end_date = yesterday
        closed_plans = self.training_plan_03.close_active_training_plans()
        self.assertIn(self.training_plan_03, closed_plans)
        self.assertFalse(self.training_plan_03.active)
        self.assertEqual(self.training_plan_03.state, 'closed')

    def test_wizard_close_training_plan(self):
        self.activity_01.state = 'active'
        self.activity_03.state = 'active'
        self.enrollment_03.state = 'active'
        self.training_plan_03.to_closed()
        self.assertEqual(self.training_plan_03.state, 'closed')
        self.assertEqual(self.activity_03.state, 'ended')
        self.assertEqual(self.enrollment_03.state, 'ended')
        self.assertEqual(self.training_plan_03.end_date, date.today())
        self.assertEqual(self.activity_03.end_date, date.today())
        self.assertEqual(self.enrollment_03.end_date, date.today())

    def test_activity_state_transitions(self):
        self.activity_03.to_active()
        self.assertEqual(self.activity_03.state, 'active')
        self.activity_03.to_ended()
        self.assertEqual(self.activity_03.state, 'ended')
        self.assertEqual(self.activity_03.end_date, date.today())
        self.activity_03.state = 'active'
        self.activity_03.end_date = date.today() + timedelta(days=30)
        self.activity_03.to_cancelled()
        self.assertEqual(self.activity_03.state, 'cancelled')

    def test_onchange_training_plan_id(self):
        self.user_02 = self.env['res.users'].create({
            'name': 'Internal User 02',
            'login': 'internal.user02@test.odoo.com',
            'email': 'internal.user02@test.odoo.com',
            'partner_id': self.teacher_02.work_contact_id.id,
        })
        self.training_plan_02.user_id = self.user_02
        self.activity_01.training_plan_id = self.training_plan_02
        self.activity_01._onchange_training_plan_id()
        self.assertEqual(
            self.user_02, self.training_plan_02.user_id)
        self.assertEqual(
            self.activity_01.user_id, self.training_plan_02.user_id)
        self.assertEqual(
            self.activity_01.start_date, self.training_plan_02.start_date)
        self.assertEqual(
            self.activity_01.end_date, self.training_plan_02.end_date)

    def test_activity_date_constraint(self):
        self.assertEqual(
            self.activity_01.start_date, self.training_plan_01.start_date)
        start_date = self.training_plan_01.start_date
        end_date = self.training_plan_01.end_date
        with self.assertRaises(ValidationError) as result:
            self.activity_01.start_date = start_date - timedelta(days=1)
        self.assertEqual(
            'The dates of the activity (Activity 01) must be compatible '
            'with the dates of the training plan.', result.exception.args[0])
        with self.assertRaises(ValidationError) as result:
            self.activity_01.end_date = end_date + timedelta(days=1)
        self.assertEqual(
            'The dates of the activity (Activity 01) must be compatible '
            'with the dates of the training plan.', result.exception.args[0])
        with self.assertRaises(ValidationError) as result:
            self.activity_01.end_date = start_date - timedelta(days=1)
        self.assertEqual(
            'Start date must be equal or before than date end.',
            result.exception.args[0])
