###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests import TransactionCase
from psycopg2.errors import NotNullViolation


class TestAcademyActivity(TransactionCase):

    def setUp(self):
        super().setUp()
        self.training_plan = self.env['academy.training.plan'].create({
            'name': 'Test Plan',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        })
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
        })

    def test_create_minimal_fields(self):
        activity = self.env['academy.activity'].create({
            'name': 'Test Activity',
            'training_plan_id': self.training_plan.id,
            'user_id': self.user.id,
            'start_date': '2024-05-01',
            'end_date': '2024-05-10',
        })
        self.assertTrue(activity)
        self.assertEqual(activity.name, 'Test Activity')
        self.assertEqual(activity.training_plan_id, self.training_plan)
        self.assertEqual(activity.user_id, self.user)
        self.assertEqual(fields.Date.to_string(activity.start_date),
                         '2024-05-01')
        self.assertEqual(fields.Date.to_string(activity.end_date),
                         '2024-05-10')
        self.assertEqual(activity.state, 'draft')
        self.assertFalse(activity.visible_website)

    def test_create_all_fields(self):
        activity = self.env['academy.activity'].create({
            'name': 'Full Activity',
            'training_plan_id': self.training_plan.id,
            'user_id': self.user.id,
            'start_date': '2024-06-01',
            'end_date': '2024-06-15',
            'state': 'active',
            'invoice_tutors': True,
            'product_id': self.product.id,
            'activity_price_reduced': 100.0,
            'activity_price': 120.0,
            'student_limit': 20,
            'estimated_hours': 10.0,
            'notes': 'Test notes',
            'visible_website': True,
        })
        self.assertTrue(activity)
        self.assertEqual(activity.name, 'Full Activity')
        self.assertEqual(activity.state, 'active')
        self.assertTrue(activity.invoice_tutors)
        self.assertEqual(activity.product_id, self.product)
        self.assertEqual(activity.activity_price_reduced, 100.0)
        self.assertEqual(activity.activity_price, 120.0)
        self.assertEqual(activity.student_limit, 20)
        self.assertEqual(activity.notes, 'Test notes')
        self.assertTrue(activity.visible_website)
        self.assertEqual(activity.website_status_text, 'Published')

    def test_required_fields(self):
        required_fields = [
            'name', 'training_plan_id', 'user_id', 'start_date', 'end_date',
        ]
        base_values = {
            'name': 'Test',
            'training_plan_id': self.training_plan.id,
            'user_id': self.user.id,
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        }
        for field in required_fields:
            vals = base_values.copy()
            vals.pop(field)
            with self.assertRaises(NotNullViolation):
                self.env['academy.activity'].create(vals)
