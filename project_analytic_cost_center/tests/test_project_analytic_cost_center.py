###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProjectAnalyticDistribution(TransactionCase):

    def setUp(self):
        super().setUp()
        self.cost_center = self.env['account.analytic.cost_center'].create({
            'name': 'Cost center test',
        })
        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'Account one',
            'plan_id': self.env.ref('analytic.analytic_plan_departments').id,
        })
        self.project = self.env['project.project'].create({
            'name': 'Analytic distribution test project',
            'cost_center_id': self.cost_center.id,
        })

    def test_create_task_default_cost_center(self):
        task = self.env['project.task'].create({
            'name': 'Test task',
            'project_id': self.project.id,
        })
        self.assertTrue(bool(task.cost_center_id))
        self.assertEqual(task.cost_center_id, task.project_id.cost_center_id)
        task = self.env['project.task'].create({
            'name': 'Test task',
        })
        self.assertFalse(bool(task.cost_center_id))
        task.project_id = self.project.id
        self.assertTrue(bool(task.cost_center_id))
        self.assertEqual(task.cost_center_id, task.project_id.cost_center_id)

    def test_create_analytic_line_from_timesheet(self):
        task = self.env['project.task'].create({
            'name': 'Test task',
            'project_id': self.project.id,
        })
        self.assertEqual(task.cost_center_id, task.project_id.cost_center_id)
        task.timesheet_ids.create({
            'name': 'Test timesheet',
            'employee_id': self.env.ref('base.user_admin').id,
            'task_id': task.id,
            'unit_amount': 1,
        })
        self.assertEqual(
            task.timesheet_ids[0].cost_center_id,
            task.cost_center_id,
        )
