###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil import relativedelta
from odoo import fields
from odoo.tests.common import TransactionCase


class TestContractBusinessUnit(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
            'analytic_reset_balance': True,
        })

    def test_contract_line(self):
        account = self.env['account.analytic.account'].create({
            'name': 'Contract test analytic account',
        })
        line = self.env['account.analytic.line'].create({
            'account_id': account.id,
            'name': 'A task',
            'unit_amount': 2,
            'amount': 200,
        })
        self.assertEquals(account.unit_balance, 2)
        line.create_reset_balance()
        self.assertEquals(len(account.line_ids), 1)
        self.assertEquals(account.unit_balance, 2)
        line = self.env['account.analytic.line'].create({
            'account_id': account.id,
            'name': 'A task',
            'unit_amount': 3,
            'amount': 300,
        })
        line.create_reset_balance()
        self.assertEquals(len(account.line_ids), 2)
        self.assertEquals(account.unit_balance, 5)
        line = self.env['account.analytic.line'].create({
            'account_id': account.id,
            'name': 'A task',
            'unit_amount': 3,
            'amount': 300,
            'product': self.product.id,
        })
        line.create_reset_balance()
        self.assertEquals(len(account.line_ids), 3)
        self.assertEquals(account.unit_balance, 8)

    def test_contract_with_project(self):
        account = self.env['account.analytic.account'].create({
            'name': 'Contract test analytic account',
        })
        start_date = fields.Date.to_date('2020-01-01')
        contract = self.env['contract.contract'].create({
            'name': 'Contract template',
            'partner_id': self.partner.id,
            'contract_type': 'sale',
            'contract_line_ids': [
                (0, 0, {
                    'name': 'Contract line test',
                    'product_id': self.product.id,
                    'analytic_account_id': account.id,
                    'quantity': 1,
                    'price_unit': 100,
                    'date_start': start_date,
                    'recurring_interval': 12,
                    'recurring_rule_type': 'monthly',
                }),
            ],
        })
        project = self.env['project.project'].create({
            'name': 'Test project',
            'analytic_account_id': account.id,
        })
        self.env['project.task'].create({
            'name': 'Test task',
            'project_id': project.id,
            'timesheet_ids': [
                (0, 0, {
                    'account_id': account.id,
                    'name': 'A task',
                    'unit_amount': 2,
                    'amount': -200,
                    'product_id': self.product.id,
                }),
            ],
        })
        contract.contract_line_ids.recurring_next_date = (
            start_date + relativedelta.relativedelta(months=1)
        )
        self.assertEquals(account.unit_balance, -2)
        contract.recurring_create_invoice()
        invoices = contract._get_related_invoices()
        self.assertEquals(len(invoices), 1)
        invoice = invoices[0]
        self.assertEquals(len(invoice.invoice_line_ids), 1)
        self.assertEquals(account.unit_balance, -2)
        invoice.action_invoice_open()
        self.assertEquals(account.unit_balance, 1)
        invoice.journal_id.update_posted = True
        invoice.action_cancel()
        self.assertEquals(account.unit_balance, -2)
