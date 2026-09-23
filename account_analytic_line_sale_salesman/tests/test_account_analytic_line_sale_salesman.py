###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestAccountAnalyticLineSaleSalesman(TransactionCase):

    def setUp(self):
        super().setUp()
        self.salesman = self.env['res.users'].create({
            'name': 'Test Salesman',
            'login': 'test_salesman',
            'groups_id': [(6, 0, [
                self.env.ref('sales_team.group_sale_salesman').id,
                self.env.ref('base.group_user').id,
            ])],
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test product',
            'type': 'service',
            'company_id': False,
            'list_price': 100,
        })
        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'Analytic account test',
            'plan_id': self.env.ref('analytic.analytic_plan_departments').id,
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': self.salesman.id,
            'analytic_account_id': self.analytic_account.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_uom_qty': 1,
                'price_unit': 100,
            })],
        })

    def test_sale_user_id_populated(self):
        analytic_line = self.env['account.analytic.line'].create({
            'name': 'Test analytic line',
            'account_id': self.analytic_account.id,
            'unit_amount': 1,
            'amount': 100,
        })
        self.assertEqual(
            analytic_line.sale_user_id,
            self.salesman,
        )

    def test_sale_user_id_empty_no_sale_order(self):
        other_account = self.env['account.analytic.account'].create({
            'name': 'Analytic account without sale order',
            'plan_id': self.env.ref('analytic.analytic_plan_departments').id,
        })
        analytic_line = self.env['account.analytic.line'].create({
            'name': 'Test analytic line without SO',
            'account_id': other_account.id,
            'unit_amount': 1,
            'amount': 50,
        })
        self.assertFalse(analytic_line.sale_user_id)

    def test_sale_user_id_updates_on_account_change(self):
        other_account = self.env['account.analytic.account'].create({
            'name': 'Analytic account without sale order',
            'plan_id': self.env.ref('analytic.analytic_plan_departments').id,
        })
        analytic_line = self.env['account.analytic.line'].create({
            'name': 'Test analytic line',
            'account_id': other_account.id,
            'unit_amount': 1,
            'amount': 100,
        })
        self.assertFalse(analytic_line.sale_user_id)
        analytic_line.account_id = self.analytic_account.id
        self.assertEqual(
            analytic_line.sale_user_id,
            self.salesman,
        )

    def test_sale_user_id_with_different_salesman(self):
        salesman2 = self.env['res.users'].create({
            'name': 'Second Salesman',
            'login': 'test_salesman2',
            'groups_id': [(6, 0, [
                self.env.ref('sales_team.group_sale_salesman').id,
                self.env.ref('base.group_user').id,
            ])],
        })
        analytic_account2 = self.env['account.analytic.account'].create({
            'name': 'Second analytic account',
            'plan_id': self.env.ref('analytic.analytic_plan_departments').id,
        })
        self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'user_id': salesman2.id,
            'analytic_account_id': analytic_account2.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_uom_qty': 1,
                'price_unit': 200,
            })],
        })
        analytic_line = self.env['account.analytic.line'].create({
            'name': 'Test line with salesman2',
            'account_id': analytic_account2.id,
            'unit_amount': 1,
            'amount': 200,
        })
        self.assertEqual(analytic_line.sale_user_id, salesman2)
