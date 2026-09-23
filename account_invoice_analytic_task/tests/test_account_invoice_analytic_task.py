###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestAccountInvoiceAnalyticTask(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer01@test.com',
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Product 01',
            'standard_price': 5,
            'list_price': 10,
        })
        type_revenue = self.env.ref('account.data_account_type_revenue')
        type_payable = self.env.ref('account.data_account_type_payable')
        account_customer = self.env['account.account'].create({
            'name': 'Customer',
            'code': 'XX_430',
            'user_type_id': type_payable.id,
            'reconcile': True,
        })
        self.account_sale = self.env['account.account'].create({
            'name': 'Sale',
            'code': 'XX_700',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        self.partner.property_account_receivable_id = account_customer.id
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': self.account_sale.id,
            'default_credit_account_id': self.account_sale.id,
        })
        self.task = self.env['project.task'].create({
            'name': 'Task test',
        })
        self.analytic_account = self.env['account.analytic.account'].create({
            'name': 'Analytic account test',
        })

    def test_invoice_line_with_task(self):
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_01.id,
                'name': self.product_01.name,
                'account_id': self.account_sale.id,
                'account_analytic_id': self.analytic_account.id,
                'price_unit': 100,
                'quantity': 1,
                'task_id': self.task.id,
            })],
        })
        invoice.action_invoice_open()
        inv_line = invoice.invoice_line_ids[0]
        move_lines = self.env['account.move.line'].search([
            ('analytic_account_id', '=', self.analytic_account.id),
        ])
        self.assertEquals(len(move_lines), 1)
        self.assertEquals(move_lines[0].task_id, inv_line.task_id)
        self.assertEquals(move_lines[0].invoice_id, inv_line.invoice_id)
        analytic_lines = self.env['account.analytic.line'].search([
            ('account_id', '=', self.analytic_account.id),
        ])
        self.assertEquals(len(analytic_lines), 1)
        self.assertEquals(analytic_lines[0].task_id, inv_line.task_id)

    def test_invoice_line_without_task(self):
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_01.id,
                'name': self.product_01.name,
                'account_id': self.account_sale.id,
                'account_analytic_id': self.analytic_account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice.action_invoice_open()
        inv_line = invoice.invoice_line_ids[0]
        move_lines = self.env['account.move.line'].search([
            ('analytic_account_id', '=', self.analytic_account.id),
        ])
        self.assertEquals(len(move_lines), 1)
        self.assertFalse(move_lines[0].task_id)
        self.assertEquals(move_lines[0].invoice_id, inv_line.invoice_id)
        analytic_lines = self.env['account.analytic.line'].search([
            ('account_id', '=', self.analytic_account.id),
        ])
        self.assertEquals(len(analytic_lines), 1)
        self.assertFalse(analytic_lines[0].task_id)
