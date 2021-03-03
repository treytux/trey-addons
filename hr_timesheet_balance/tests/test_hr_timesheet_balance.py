###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestHrTimesheetBalance(TransactionCase):

    def test_invoice_ok(self):
        product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
            'analytic_reset_balance': True,
        })
        project = self.env['project.project'].create({
            'name': 'Test project',
        })
        task = self.env['project.task'].create({
            'name': 'Test task',
            'project_id': project.id,
            'timesheet_ids': [
                (0, 0, {
                    'account_id': project.analytic_account_id.id,
                    'name': 'A task',
                    'product_id': product.id,
                    'unit_amount': 2,
                    'amount': -200,
                }),
            ],
        })
        self.assertEquals(len(task.timesheet_ids), 1)
        line = task.timesheet_ids
        self.assertEquals(line.unit_balance, -2)
        self.assertEquals(
            sum(project.analytic_account_id.line_ids.mapped('amount')), -200)
        line = self.env['account.analytic.line'].create({
            'account_id': project.analytic_account_id.id,
            'name': 'A simple line',
            'product_id': product.id,
            'unit_amount': 3,
            'amount': 300,
        })
        self.assertEquals(line.unit_balance, 3)
        self.assertEquals(line.account_id.unit_balance, 1)
        self.assertEquals(
            sum(project.analytic_account_id.line_ids.mapped('amount')), 100)
        line.create_reset_balance()
        self.assertEquals(line.account_id.unit_balance, 3)
        self.assertEquals(
            sum(project.analytic_account_id.line_ids.mapped('amount')), 100)
        self.assertEquals(len(line.account_id.line_ids), 3)
