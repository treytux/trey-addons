###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProjectTaskPurchaseLink(TransactionCase):

    def setUp(self):
        super().setUp()
        self.analytic_plan = self.env['account.analytic.plan'].create({
            'name': 'Test Plan',
        })
        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'Test Analytic Account',
            'plan_id': self.analytic_plan.id,
        })
        self.project = self.env['project.project'].create({
            'name': 'Test Project',
            'analytic_account_id': self.analytic_account.id,
        })
        self.task = self.env['project.task'].create({
            'name': 'Test Task',
            'project_id': self.project.id,
        })

    def test_purchase_count_related_field(self):
        self.assertEqual(self.task.purchase_count, self.project.purchase_count)

    def test_button_open_purchase_order(self):
        action = self.task.button_open_purchase_order()
        self.assertIsInstance(action, dict)
        self.assertIn('context', action)
        self.assertIn('default_analytic_distribution', action['context'])
        expected_account_id_str = str(self.project.analytic_account_id.id)
        analytic_distribution = action['context'][
            'default_analytic_distribution']
        self.assertIn(expected_account_id_str, analytic_distribution)
        self.assertEqual(analytic_distribution[expected_account_id_str], 100)

    def test_button_open_purchase_order_ensure_one(self):
        task_2 = self.env['project.task'].create({
            'name': 'Test Task 2',
            'project_id': self.project.id,
        })
        tasks = self.task | task_2
        with self.assertRaises(ValueError) as result:
            tasks.button_open_purchase_order()
            self.assertIn('<bound method _BaseTestCaseContext._raiseFailure of'
                          '<unittest.case._AssertRaisesContext object at',
                          result)
