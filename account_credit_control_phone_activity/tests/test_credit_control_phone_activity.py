###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from dateutil import relativedelta
from odoo import fields
from odoo.tests import common


class TestCreditControlPhoneActivity(common.TransactionCase):

    def setUp(self):
        super().setUp()
        journal = self.env['account.invoice']._default_journal()
        account_type_rec = self.env.ref('account.data_account_type_receivable')
        self.account = self.env['account.account'].create({
            'code': '430001',
            'name': 'Customer (test)',
            'user_type_id': account_type_rec.id,
            'reconcile': True,
        })
        tag_operation = self.env.ref('account.account_tag_operating')
        account_type_inc = self.env.ref('account.data_account_type_revenue')
        analytic_account = self.env['account.account'].create({
            'code': '700001',
            'name': 'Sales (test)',
            'user_type_id': account_type_inc.id,
            'reconcile': True,
            'tag_ids': [(6, 0, [tag_operation.id])],
        })
        payment_term = self.env.ref('account.account_payment_term_immediate')
        product = self.env['product.product'].create({
            'name': 'Product test',
        })
        email_template = self.env.ref(
            'account_credit_control.email_template_credit_control_base')
        self.policy = self.env['credit.control.policy'].create({
            'name': 'Phone policy',
            'account_ids': [(6, 0, [self.account.id])],
            'level_ids': [
                (0, 0, {
                    'name': 'Phone call',
                    'level': 1,
                    'channel': 'phone',
                    'delay_days': 0,
                    'computation_mode': 'net_days',
                    'email_template_id': email_template.id,
                    'custom_text': 'Do a phone call!',
                    'custom_mail_text': 'Please do a phone call to customer!',
                }),
            ],
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner',
            'property_account_receivable_id': self.account.id,
        })
        self.partner.credit_policy_id = self.policy.id
        date_invoice = datetime.today() - relativedelta.relativedelta(years=1)
        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'journal_id': journal.id,
            'type': 'out_invoice',
            'payment_term_id': payment_term.id,
            'date_invoice': fields.Datetime.to_string(date_invoice),
            'date_due': fields.Datetime.to_string(date_invoice),
        })
        self.invoice.invoice_line_ids.create({
            'invoice_id': self.invoice.id,
            'product_id': product.id,
            'name': product.name,
            'account_id': analytic_account.id,
            'quantity': 5,
            'price_unit': 100,
        })
        self.invoice.action_invoice_open()

    def test_generate_credit_lines(self):
        control_run = self.env['credit.control.run'].create({
            'date': fields.Date.today(),
            'policy_ids': [(6, 0, [self.policy.id])],
        })
        control_run.with_context(lang='en_US').generate_credit_lines()
        self.assertEqual(len(self.invoice.credit_control_line_ids), 1)
        self.assertEqual(control_run.state, 'done')
        self.assertEqual(control_run.line_ids.state, 'draft')
        control_run.set_to_ready_lines()
        self.assertEqual(len(control_run.line_ids), 1)
        self.assertEqual(control_run.line_ids.state, 'to_be_sent')
        self.assertEqual(len(control_run.line_ids.activity_ids), 0)
        control_run.run_channel_action()
        control_run.line_ids.refresh()
        self.assertEqual(len(control_run.line_ids.activity_ids), 1)
        activity = control_run.line_ids.activity_ids
        self.assertEqual(activity.summary, 'Phone call')
        self.assertIn('Do a phone call!', activity.note)
        self.assertIn('Do a phone call!', self.partner.payment_next_action)
