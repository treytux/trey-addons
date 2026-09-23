###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestAccountMoveAnalyticTask(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer_rank': 1,
            'email': 'customer01@test.com',
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Product 01',
            'standard_price': 5,
            'list_price': 10,
        })
        self.account_sale = self.env['account.account'].create({
            'name': 'Sale',
            'code': '700XXX',
            'account_type': 'income',
            'reconcile': True,
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
        })
        self.task = self.env['project.task'].create({
            'name': 'Task test',
        })
        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'Analytic account test',
            'plan_id': self.env.ref('analytic.analytic_plan_departments').id,
        })

    def test_invoice_line_with_task(self):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_01.id,
                'name': self.product_01.name,
                'account_id': self.account_sale.id,
                'analytic_distribution': {self.analytic_account.id: 100},
                'price_unit': 100,
                'quantity': 1,
                'task_id': self.task.id,
            })],
        })
        invoice.action_post()
        inv_line = invoice.invoice_line_ids[0]
        analytic_lines = self.env['account.analytic.line'].search([
            ('account_id', '=', self.analytic_account.id),
        ])
        self.assertEqual(len(analytic_lines), 1)
        self.assertEqual(analytic_lines[0].task_id, inv_line.task_id)

    def test_invoice_line_without_task(self):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_01.id,
                'name': self.product_01.name,
                'account_id': self.account_sale.id,
                'analytic_distribution': {self.analytic_account.id: 100},
                'quantity': 1,
            })],
        })
        invoice.action_post()
        analytic_lines = self.env['account.analytic.line'].search([
            ('account_id', '=', self.analytic_account.id),
        ])
        self.assertEqual(len(analytic_lines), 1)
        self.assertFalse(analytic_lines[0].task_id)
