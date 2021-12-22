###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests.common import TransactionCase


class TestHrTimesheetBalance(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
            'analytic_reset_balance': True,
        })
        self.project = self.env['project.project'].create({
            'name': 'Test project',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.follower = self.env['mail.followers'].create({
            'res_model': 'account.analytic.account',
            'res_id': self.project.analytic_account_id.id,
            'partner_id': self.partner.id,
        })

    def test_invoice_ok(self):
        task = self.env['project.task'].create({
            'name': 'Test task',
            'project_id': self.project.id,
            'timesheet_ids': [
                (0, 0, {
                    'account_id': self.project.analytic_account_id.id,
                    'name': 'A task',
                    'product_id': self.product.id,
                    'unit_amount': 2,
                    'amount': -200,
                }),
            ],
        })
        self.assertEquals(len(task.timesheet_ids), 1)
        line = task.timesheet_ids
        self.assertEquals(line.unit_balance, -2)
        self.assertEquals(
            sum(self.project.analytic_account_id.line_ids.mapped('amount')),
            -200)
        line = self.env['account.analytic.line'].create({
            'account_id': self.project.analytic_account_id.id,
            'name': 'A simple line',
            'product_id': self.product.id,
            'unit_amount': 3,
            'amount': 300,
        })
        self.assertEquals(line.unit_balance, 3)
        self.assertEquals(line.account_id.unit_balance, 1)
        self.assertEquals(
            sum(self.project.analytic_account_id.line_ids.mapped('amount')),
            100)
        line.create_reset_balance()
        self.assertEquals(line.account_id.unit_balance, 3)
        self.assertEquals(
            sum(self.project.analytic_account_id.line_ids.mapped('amount')),
            100)
        self.assertEquals(len(line.account_id.line_ids), 3)

    def test_send_mail_negative_balance(self):
        self.project.analytic_account_id.last_notification = '4'
        self.project.analytic_account_id.notify_unit_balance = True
        self.assertEquals(
            len(self.project.analytic_account_id.message_follower_ids), 2)
        self.project.analytic_account_id.message_follower_ids[0].unlink()
        self.assertEquals(
            len(self.project.analytic_account_id.message_follower_ids), 1)
        self.env['project.task'].create({
            'name': 'Test task',
            'project_id': self.project.id,
            'timesheet_ids': [
                (0, 0, {
                    'account_id': self.project.analytic_account_id.id,
                    'name': 'Task test',
                    'product_id': self.product.id,
                    'unit_amount': 2,
                    'amount': -200,
                })
            ],
        })
        self.assertEquals(
            self.project.analytic_account_id.message_follower_ids.partner_id,
            self.partner)
        self.assertEquals(self.project.analytic_account_id.unit_balance, -2)
        self.assertEquals(len(self.partner.message_ids), 1)
        self.assertIn('Contact', self.partner.message_ids[0].body)
        self.env['account.analytic.account'].send_negative_balance_mail()
        self.assertTrue(self.project.analytic_account_id.notify_unit_balance)
        self.assertEquals(
            self.project.analytic_account_id.last_notification,
            str(fields.Date.today().month))
        self.assertEquals(len(self.partner.message_ids), 2)
        self.assertIn(
            'Dear %s' % self.partner.display_name,
            self.partner.message_ids[0].body)
        self.assertIn(
            'Your hours balance for this month is <strong>negative</strong>.',
            self.partner.message_ids[0].body)

    def test_not_send_mail_positive_balance(self):
        self.project.analytic_account_id.last_notification = '4'
        self.project.analytic_account_id.notify_unit_balance = True
        self.assertEquals(
            len(self.project.analytic_account_id.message_follower_ids), 2)
        self.project.analytic_account_id.message_follower_ids[0].unlink()
        self.assertEquals(
            len(self.project.analytic_account_id.message_follower_ids), 1)
        self.assertEquals(
            self.project.analytic_account_id.message_follower_ids.partner_id,
            self.partner)
        self.assertEquals(self.project.analytic_account_id.unit_balance, 0)
        self.assertEquals(len(self.partner.message_ids), 1)
        self.assertIn('Contact', self.partner.message_ids[0].body)
        self.env['account.analytic.account'].send_negative_balance_mail()
        self.assertEquals(
            self.project.analytic_account_id.last_notification, '4')
        self.assertTrue(self.project.analytic_account_id.notify_unit_balance)
        self.assertEquals(len(self.partner.message_ids), 1)

    def test_not_send_mail_negative_balance_notify_false(self):
        self.project.analytic_account_id.last_notification = '4'
        self.project.analytic_account_id.notify_unit_balance = False
        self.assertEquals(
            len(self.project.analytic_account_id.message_follower_ids), 2)
        self.project.analytic_account_id.message_follower_ids[0].unlink()
        self.assertEquals(
            len(self.project.analytic_account_id.message_follower_ids), 1)
        self.env['project.task'].create({
            'name': 'Test task',
            'project_id': self.project.id,
            'timesheet_ids': [
                (0, 0, {
                    'account_id': self.project.analytic_account_id.id,
                    'name': 'Task test',
                    'product_id': self.product.id,
                    'unit_amount': 2,
                    'amount': -200,
                })
            ],
        })
        self.assertEquals(
            self.project.analytic_account_id.message_follower_ids.partner_id,
            self.partner)
        self.assertEquals(self.project.analytic_account_id.unit_balance, -2)
        self.env['account.analytic.account'].send_negative_balance_mail()
        self.assertEquals(
            self.project.analytic_account_id.last_notification, '4')
        self.assertFalse(self.project.analytic_account_id.notify_unit_balance)
        self.assertEquals(len(self.partner.message_ids), 1)
        self.assertIn('Contact', self.partner.message_ids[0].body)

    def test_not_send_mail_actual_month_notify_true(self):
        month = str(fields.Date.today().month)
        self.project.analytic_account_id.last_notification = month
        self.project.analytic_account_id.notify_unit_balance = True
        self.assertEquals(
            len(self.project.analytic_account_id.message_follower_ids), 2)
        self.project.analytic_account_id.message_follower_ids[0].unlink()
        self.assertEquals(
            len(self.project.analytic_account_id.message_follower_ids), 1)
        self.env['project.task'].create({
            'name': 'Test task',
            'project_id': self.project.id,
            'timesheet_ids': [
                (0, 0, {
                    'account_id': self.project.analytic_account_id.id,
                    'name': 'Task test',
                    'product_id': self.product.id,
                    'unit_amount': 2,
                    'amount': -200,
                })
            ],
        })
        self.assertEquals(
            self.project.analytic_account_id.message_follower_ids.partner_id,
            self.partner)
        self.assertEquals(self.project.analytic_account_id.unit_balance, -2)
        self.env['account.analytic.account'].send_negative_balance_mail()
        self.assertTrue(self.project.analytic_account_id.notify_unit_balance)
        self.assertEquals(
            self.project.analytic_account_id.last_notification, month)
        self.assertEquals(len(self.partner.message_ids), 1)
        self.assertIn('Contact', self.partner.message_ids[0].body)

    def test_not_send_mail_actual_month_notify_false(self):
        month = str(fields.Date.today().month)
        self.project.analytic_account_id.last_notification = month
        self.project.analytic_account_id.notify_unit_balance = False
        self.assertEquals(
            len(self.project.analytic_account_id.message_follower_ids), 2)
        self.project.analytic_account_id.message_follower_ids[0].unlink()
        self.assertEquals(
            len(self.project.analytic_account_id.message_follower_ids), 1)
        self.env['project.task'].create({
            'name': 'Test task',
            'project_id': self.project.id,
            'timesheet_ids': [
                (0, 0, {
                    'account_id': self.project.analytic_account_id.id,
                    'name': 'Task test',
                    'product_id': self.product.id,
                    'unit_amount': 2,
                    'amount': -200,
                })
            ],
        })
        self.assertEquals(
            self.project.analytic_account_id.message_follower_ids.partner_id,
            self.partner)
        self.assertEquals(self.project.analytic_account_id.unit_balance, -2)
        self.env['account.analytic.account'].send_negative_balance_mail()
        self.assertFalse(self.project.analytic_account_id.notify_unit_balance)
        self.assertEquals(
            self.project.analytic_account_id.last_notification, month)
        self.assertEquals(len(self.partner.message_ids), 1)
        self.assertIn('Contact', self.partner.message_ids[0].body)
