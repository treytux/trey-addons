###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import fields
from odoo.tests import common


class TestAcademyWebsiteClose(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
        })
        analytic_plan = self.env.ref('academy.academy_analytic_plan')
        current = analytic_plan
        while current:
            current.company_id = self.company
            current = current.parent_id
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user',
            'company_id': self.company.id,
            'company_ids': [(4, self.company.id)],
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'service',
        })
        self.today = fields.Date.today()
        self.plan1 = self.env['academy.training.plan'].create({
            'name': 'Plan 1',
            'start_date': self.today - timedelta(days=30),
            'end_date': self.today - timedelta(days=1),
            'user_id': self.user.id,
            'company_id': self.company.id,
        })
        self.plan2 = self.env['academy.training.plan'].create({
            'name': 'Plan 2',
            'start_date': self.today - timedelta(days=30),
            'end_date': self.today + timedelta(days=10),
            'user_id': self.user.id,
            'company_id': self.company.id,
        })
        self.plan3 = self.env['academy.training.plan'].create({
            'name': 'Plan 3 (already closed)',
            'start_date': self.today - timedelta(days=30),
            'end_date': self.today - timedelta(days=1),
            'state': 'closed',
            'active': False,
            'user_id': self.user.id,
            'company_id': self.company.id,
        })
        self.activity1 = self.env['academy.activity'].create({
            'name': 'Activity 1 (draft, ended yesterday)',
            'state': 'draft',
            'start_date': self.today - timedelta(days=25),
            'end_date': self.today - timedelta(days=1),
            'training_plan_id': self.plan1.id,
            'user_id': self.user.id,
            'product_id': self.product.id,
        })
        self.activity2 = self.env['academy.activity'].create({
            'name': 'Activity 2 (active, ended yesterday)',
            'state': 'active',
            'start_date': self.today - timedelta(days=25),
            'end_date': self.today - timedelta(days=1),
            'training_plan_id': self.plan1.id,
            'user_id': self.user.id,
            'product_id': self.product.id,
        })
        self.activity3 = self.env['academy.activity'].create({
            'name': 'Activity 3 (ended, ended yesterday)',
            'state': 'ended',
            'start_date': self.today - timedelta(days=25),
            'end_date': self.today - timedelta(days=1),
            'training_plan_id': self.plan1.id,
            'user_id': self.user.id,
            'product_id': self.product.id,
        })
        self.activity4 = self.env['academy.activity'].create({
            'name': 'Activity 4 (cancelled, ended yesterday)',
            'state': 'cancelled',
            'start_date': self.today - timedelta(days=25),
            'end_date': self.today - timedelta(days=1),
            'training_plan_id': self.plan1.id,
            'user_id': self.user.id,
            'product_id': self.product.id,
        })
        self.activity5 = self.env['academy.activity'].create({
            'name': 'Activity 5 (draft, ends in future)',
            'state': 'draft',
            'start_date': self.today + timedelta(days=1),
            'end_date': self.today + timedelta(days=10),
            'training_plan_id': self.plan2.id,
            'user_id': self.user.id,
            'product_id': self.product.id,
        })
        self.activity6 = self.env['academy.activity'].create({
            'name': 'Activity 6 (active, plan closed)',
            'state': 'active',
            'start_date': self.today - timedelta(days=25),
            'end_date': self.today - timedelta(days=1),
            'training_plan_id': self.plan3.id,
            'user_id': self.user.id,
            'product_id': self.product.id,
        })

    def test_close_active_activities_no_plan_filter(self):
        closed = self.env['academy.activity'].close_active_activities(
            plan_ids=None)
        self.assertIn(self.activity1, closed)
        self.assertIn(self.activity2, closed)
        self.assertIn(self.activity6, closed)
        self.assertNotIn(self.activity3, closed)
        self.assertNotIn(self.activity4, closed)
        self.assertNotIn(self.activity5, closed)
        self.assertEqual(self.activity1.state, 'ended')
        self.assertEqual(self.activity2.state, 'ended')
        self.assertEqual(self.activity6.state, 'ended')
        self.assertFalse(self.activity1.visible_website)
        self.assertFalse(self.activity2.visible_website)
        self.assertFalse(self.activity6.visible_website)
        self.assertEqual(self.activity3.state, 'ended')
        self.assertEqual(self.activity4.state, 'cancelled')
        self.assertEqual(self.activity5.state, 'draft')
        self.assertFalse(self.activity3.visible_website)
        self.assertFalse(self.activity4.visible_website)
        self.assertFalse(self.activity5.visible_website)

    def test_close_active_activities_with_plan_filter(self):
        closed = self.env['academy.activity'].close_active_activities(
            plan_ids=self.plan1)
        self.assertIn(self.activity1, closed)
        self.assertIn(self.activity2, closed)
        self.assertIn(self.activity3, closed)
        self.assertIn(self.activity4, closed)
        self.assertIn(self.activity6, closed)
        self.assertNotIn(self.activity5, closed)
        self.assertEqual(self.activity1.state, 'ended')
        self.assertEqual(self.activity2.state, 'ended')
        self.assertEqual(self.activity3.state, 'ended')
        self.assertEqual(self.activity4.state, 'ended')
        self.assertEqual(self.activity6.state, 'ended')
        self.assertEqual(self.activity5.state, 'draft')
        self.assertFalse(self.activity1.visible_website)
        self.assertFalse(self.activity2.visible_website)
        self.assertFalse(self.activity3.visible_website)
        self.assertFalse(self.activity4.visible_website)
        self.assertFalse(self.activity6.visible_website)
        self.assertFalse(self.activity5.visible_website)

    def test_close_active_training_plans(self):
        closed = self.env['academy.training.plan'].close_active_training_plans()
        self.assertIn(self.plan1, closed)
        self.assertNotIn(self.plan2, closed)
        self.assertNotIn(self.plan3, closed)
        self.assertEqual(self.plan1.state, 'closed')
        self.assertFalse(self.plan1.active)
        self.assertFalse(self.plan1.visible_website)
        self.assertEqual(self.plan2.state, 'in_progress')
        self.assertTrue(self.plan2.active)
        self.assertFalse(self.plan2.visible_website)
        self.assertEqual(self.plan3.state, 'closed')
        self.assertFalse(self.plan3.active)
        self.assertFalse(self.plan3.visible_website)
