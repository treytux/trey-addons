###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestAccountAnalyticGroup(TransactionCase):

    def setUp(self):
        super().setUp()
        self.AnalyticGroup = self.env['account.analytic.group']
        self.AnalyticLine = self.env['account.analytic.line']
        self.Plan = self.env['account.analytic.plan']
        self.AnalyticAccount = self.env['account.analytic.account']

    def _create_analytical_account(self):
        plan = self.Plan.create({'name': 'Test Plan'})
        return self.AnalyticAccount.create({
            'name': 'Test Analytic Account',
            'plan_id': plan.id,
        })

    def test_create_analytic_group(self):
        group = self.AnalyticGroup.create({
            'name': 'Test Group',
            'color': 5,
        })
        self.assertEqual(group.name, 'Test Group')
        self.assertEqual(group.color, 5)

    def test_analytic_group_company_default(self):
        group = self.AnalyticGroup.create({
            'name': 'Company Group',
        })
        self.assertEqual(group.company_id, self.env.company)

    def test_analytic_group_unique_names(self):
        group_a = self.AnalyticGroup.create({'name': 'Group A'})
        group_b = self.AnalyticGroup.create({'name': 'Group B'})
        self.assertNotEqual(group_a, group_b)
        self.assertEqual(group_a.name, 'Group A')
        self.assertEqual(group_b.name, 'Group B')

    def test_name_required(self):
        with self.assertRaises(Exception):
            self.AnalyticGroup.create({})

    def test_analytic_line_group_assign(self):
        group = self.AnalyticGroup.create({'name': 'Line Group'})
        account = self._create_analytical_account()
        line = self.AnalyticLine.create({
            'name': 'Test analytic item',
            'account_id': account.id,
            'group_id': group.id,
            'amount': 100.0,
        })
        self.assertEqual(line.group_id, group)
        self.assertEqual(line.group_id.name, 'Line Group')

    def test_analytic_line_group_unlink(self):
        group = self.AnalyticGroup.create({'name': 'Used Group'})
        account = self._create_analytical_account()
        line = self.AnalyticLine.create({
            'name': 'Referencing line',
            'account_id': account.id,
            'group_id': group.id,
            'amount': 50.0,
        })
        group.unlink()
        self.assertFalse(line.read(['group_id'])[0]['group_id'])

    def test_analytic_line_no_group(self):
        account = self._create_analytical_account()
        line = self.AnalyticLine.create({
            'name': 'No group line',
            'account_id': account.id,
            'amount': 200.0,
        })
        self.assertFalse(line.group_id)

    def test_group_order(self):
        self.AnalyticGroup.create({'name': 'Z Group'})
        self.AnalyticGroup.create({'name': 'A Group'})
        groups = self.AnalyticGroup.search([])
        names = groups.mapped('name')
        self.assertEqual(names, sorted(names))
