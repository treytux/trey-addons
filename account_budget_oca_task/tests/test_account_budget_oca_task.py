###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import SavepointCase, tagged


@tagged('post_install', '-at_install')
class TestAccountBudgetOcaTask(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        plan = cls.env.ref('analytic.analytic_plan_departments')
        cls.analytic_account = cls.env['account.analytic.account'].create({
            'name': 'Analytic Account Budget Task Test',
            'plan_id': plan.id,
            'company_id': cls.company.id,
        })
        cls.project = cls.env['project.project'].create({
            'name': 'Project Budget Task Test',
            'analytic_account_id': cls.analytic_account.id,
            'allow_timesheets': True,
            'company_id': cls.company.id,
        })
        cls.task_1 = cls.env['project.task'].create({
            'name': 'Task 1', 'project_id': cls.project.id,
        })
        cls.task_2 = cls.env['project.task'].create({
            'name': 'Task 2', 'project_id': cls.project.id,
        })
        cls.employee = cls.env.user.employee_id
        if not cls.employee:
            cls.employee = cls.env['hr.employee'].create({
                'name': 'Budget Task Test Employee',
                'user_id': cls.env.user.id,
                'company_id': cls.company.id,
            })
        cls.account = cls.env['account.account'].search([
            ('account_type', '=', 'expense'),
            ('deprecated', '=', False),
            ('company_id', '=', cls.company.id),
        ], limit=1)
        if not cls.account:
            cls.account = cls.env['account.account'].create({
                'name': 'Budget Task Test Account',
                'code': 'XBT001', 'account_type': 'expense',
                'company_id': cls.company.id,
            })
        cls.other_account = cls.env['account.account'].search([
            ('account_type', '=', 'expense'),
            ('deprecated', '=', False),
            ('company_id', '=', cls.company.id),
            ('id', '!=', cls.account.id),
        ], limit=1)
        if not cls.other_account:
            cls.other_account = cls.env['account.account'].create({
                'name': 'Budget Task Test Other Account',
                'code': 'XBT002', 'account_type': 'expense',
                'company_id': cls.company.id,
            })
        cls.budget_post = cls.env['account.budget.post'].create({
            'name': 'Budget Post Task Test',
            'account_ids': [(6, 0, cls.account.ids)],
            'company_id': cls.company.id,
        })
        cls.budget = cls.env['crossovered.budget'].create({
            'name': 'Budget Task Test',
            'date_from': '2026-01-01', 'date_to': '2026-01-31',
            'company_id': cls.company.id,
        })

    def _create_budget_line(self, task=False):
        return self.env['crossovered.budget.lines'].create({
            'crossovered_budget_id': self.budget.id,
            'analytic_account_id': self.analytic_account.id,
            'general_budget_id': self.budget_post.id,
            'date_from': '2026-01-01', 'date_to': '2026-01-31',
            'planned_amount': 1000.0, 'task_id': task.id if task else False,
        })

    def _create_analytic_line(self, amount, date, general_account, task=False):
        vals = {
            'name': 'Budget Task Analytic Line', 'date': date,
            'amount': amount, 'account_id': self.analytic_account.id,
            'general_account_id': general_account.id,
            'project_id': self.project.id, 'employee_id': self.employee.id,
            'unit_amount': 1.0, 'company_id': self.company.id,
        }
        if task:
            vals['task_id'] = task.id
        return self.env['account.analytic.line'].create(vals)

    def test_practical_amount_without_task_uses_base_behavior(self):
        budget_line = self._create_budget_line(task=False)
        self._create_analytic_line(
            100.0, '2026-01-10', self.account, task=self.task_1
        )
        self._create_analytic_line(50.0, '2026-01-11', self.account)
        self._create_analytic_line(
            25.0, '2026-01-12', self.account, task=self.task_2
        )
        self._create_analytic_line(
            999.0, '2026-02-01', self.account, task=self.task_1
        )
        self._create_analytic_line(
            777.0, '2026-01-13', self.other_account, task=self.task_1
        )
        self.assertEqual(budget_line.practical_amount, 175.0)

    def test_practical_amount_with_task_filters_by_task(self):
        budget_line = self._create_budget_line(task=self.task_1)
        self._create_analytic_line(
            100.0, '2026-01-10', self.account, task=self.task_1
        )
        self._create_analytic_line(
            20.0, '2026-01-11', self.account, task=self.task_1
        )
        self._create_analytic_line(
            40.0, '2026-01-12', self.account, task=self.task_2
        )
        self._create_analytic_line(10.0, '2026-01-13', self.account)
        self._create_analytic_line(
            888.0, '2026-02-01', self.account, task=self.task_1
        )
        self._create_analytic_line(
            555.0, '2026-01-14', self.other_account, task=self.task_1
        )
        self.assertEqual(budget_line.practical_amount, 120.0)
