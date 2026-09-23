###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase
from psycopg2.errors import NotNullViolation


class TestAcademyWebsiteTrainingPlan(TransactionCase):

    def setUp(self):
        super().setUp()
        self.typology = self.env['academy.typology'].create({
            'name': 'Test Typology',
        })
        self.company = self.env.company
        self.user = self.env.user

    def test_create_minimal_fields(self):
        plan = self.env['academy.training.plan'].create({
            'name': 'Minimal Plan',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
        })
        self.assertTrue(plan)
        self.assertEqual(plan.name, 'Minimal Plan')
        self.assertEqual(fields.Date.to_string(plan.start_date), '2024-01-01')
        self.assertEqual(fields.Date.to_string(plan.end_date), '2024-12-31')
        self.assertEqual(plan.user_id, self.user)
        self.assertTrue(plan.active)
        self.assertEqual(plan.state, 'in_progress')
        self.assertFalse(plan.visible_website)
        self.assertTrue(plan.analytic_account_id)

    def test_create_all_fields(self):
        plan = self.env['academy.training.plan'].create({
            'name': 'Full Plan',
            'short_name': 'FP',
            'description': 'Test description',
            'active': True,
            'start_date': '2024-03-01',
            'end_date': '2024-08-31',
            'state': 'in_progress',
            'typology_id': self.typology.id,
            'company_id': self.company.id,
            'user_id': self.user.id,
            'visible_website': True,
        })
        self.assertTrue(plan)
        self.assertEqual(plan.name, 'Full Plan')
        self.assertEqual(plan.short_name, 'FP')
        self.assertEqual(plan.description, 'Test description')
        self.assertTrue(plan.active)
        self.assertEqual(fields.Date.to_string(plan.start_date), '2024-03-01')
        self.assertEqual(fields.Date.to_string(plan.end_date), '2024-08-31')
        self.assertEqual(plan.state, 'in_progress')
        self.assertEqual(plan.typology_id, self.typology)
        self.assertEqual(plan.company_id, self.company)
        self.assertEqual(plan.user_id, self.user)
        self.assertTrue(plan.visible_website)
        self.assertTrue(plan.analytic_account_id)
        self.assertEqual(plan.website_status_text, 'Published')

    def test_required_fields(self):
        required_fields = ['name', 'start_date', 'end_date']
        base_values = {
            'name': 'Test Plan',
            'start_date': '2024-01-01',
            'end_date': '2024-02-01',
        }
        for field in required_fields:
            vals = base_values.copy()
            vals.pop(field)
            with self.assertRaises(NotNullViolation):
                self.env['academy.training.plan'].create(vals)
        with self.assertRaises(ValidationError):
            self.env['academy.training.plan'].create({
                'name': 'Invalid Dates',
                'start_date': '2024-02-01',
                'end_date': '2024-01-01',
                'user_id': self.user.id,
            })
