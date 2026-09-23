###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import TransactionCase


class TestAccountMoveUnpaidReminder(TransactionCase):

    def setUp(self):
        super().setUp()
        self.sale_installed = self.env['ir.module.module'].search([
            ('name', '=', 'sale'),
            ('state', '=', 'installed'),
        ])
        self.partner = self.env['res.partner'].create({
            'name': 'Partner with email',
            'email': 'partner@example.com',
        })
        self.partner_no_email = self.env['res.partner'].create({
            'name': 'Partner without email',
        })
        self.company = self.env.ref('base.main_company')
        self.income_account = self.env['account.account'].create({
            'name': 'Test Income',
            'code': 'TSTINC',
            'account_type': 'income',
            'company_id': self.company.id,
        })
        vals = {
            'name': 'Test Product',
            'type': 'service',
            'property_account_income_id': self.income_account.id,
            'company_id': self.company.id,
        }
        if 'sale_line_warn' in self.env['product.template']._fields:
            vals['sale_line_warn'] = 'no-message'
        if 'purchase_line_warn' in self.env['product.template']._fields:
            vals['purchase_line_warn'] = 'no-message'
        self.product_template = self.env['product.template'].create(vals)
        self.product = self.product_template.product_variant_id
        self.template = self.env.ref(
            'account_move_unpaid_reminder.email_tmpl_unpaid_reminder')
        self.assertTrue(self.template)
        self.template.write({
            'auto_delete': False,
        })

    def _create_invoice(
            self, unpaid_reminder=True, partner=None, state='draft'):
        partner = partner or self.partner
        invoice = self.env['account.move'].create({
            'partner_id': partner.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100,
            })],
            'unpaid_reminder': unpaid_reminder,
        })
        if state == 'posted':
            invoice.action_post()
        elif state == 'cancel':
            invoice.action_post()
            invoice.button_cancel()
        return invoice

    def test_01_invoice_meets_conditions_sends_reminder(self):
        if not self.sale_installed:
            self.skipTest('sale module not installed')
        invoice = self._create_invoice(
            unpaid_reminder=True, state='posted')
        follower = self.env['res.partner'].create({
            'name': 'Follower with email',
            'email': 'follower@example.com',
        })
        invoice.message_subscribe([follower.id])
        self.env['mail.mail'].search([]).unlink()
        self.env['account.move']._send_unpaid_reminders()
        messages = self.env['mail.message'].search([
            ('res_id', '=', invoice.id),
            ('model', '=', 'account.move'),
            ('subject', '=', 'Unpaid reminder sent'),
        ])
        self.assertEqual(len(messages), 1)
        self.assertIn('Unpaid reminder sent', messages.body)
        mails = self.env['mail.mail'].search([])
        self.assertTrue(mails)
        self.assertIn(follower.email, mails.email_to)

    def test_02_invoice_no_email_followers_no_reminder(self):
        if not self.sale_installed:
            self.skipTest('sale module not installed')
        invoice = self._create_invoice(unpaid_reminder=True, state='draft')
        invoice.message_subscribe([self.partner_no_email.id])
        self.env['mail.mail'].search([]).unlink()
        self.env['account.move']._send_unpaid_reminders()
        mails = self.env['mail.mail'].search([])
        self.assertFalse(mails)
        messages = self.env['mail.message'].search([
            ('res_id', '=', invoice.id),
            ('subject', '=', 'Unpaid reminder sent'),
        ])
        self.assertFalse(messages)

    def test_03_invoice_does_not_meet_domain_ignored(self):
        if not self.sale_installed:
            self.skipTest('sale module not installed')
        invoice_no_flag = self._create_invoice(
            unpaid_reminder=False, state='draft')
        invoice_no_flag.message_subscribe([self.partner.id])
        invoice_paid = self._create_invoice(
            unpaid_reminder=True, state='posted')
        invoice_paid.message_subscribe([self.partner.id])
        invoice_paid.payment_state = 'paid'
        invoice_cancel = self._create_invoice(
            unpaid_reminder=True, state='cancel')
        invoice_cancel.message_subscribe([self.partner.id])
        self.env['mail.mail'].search([]).unlink()
        self.env['account.move']._send_unpaid_reminders()
        all_invoices = invoice_no_flag | invoice_paid | invoice_cancel
        mails = self.env['mail.mail'].search([])
        self.assertFalse(mails)
        messages = self.env['mail.message'].search([
            ('res_id', 'in', all_invoices.ids),
            ('subject', '=', 'Unpaid reminder sent'),
        ])
        self.assertFalse(messages)

    def test_04_mixed_followers_only_email_receives(self):
        if not self.sale_installed:
            self.skipTest('sale module not installed')
        invoice = self._create_invoice(unpaid_reminder=True, state='posted')
        follower_with_email = self.env['res.partner'].create({
            'name': 'With Email',
            'email': 'follower@example.com',
        })
        follower_without_email = self.env['res.partner'].create({
            'name': 'Without Email',
        })
        invoice.message_subscribe([
            follower_with_email.id,
            follower_without_email.id,
        ])
        self.env['mail.mail'].search([]).unlink()
        self.env['account.move']._send_unpaid_reminders()
        mails = self.env['mail.mail'].search([])
        self.assertTrue(mails)
        self.assertIn(follower_with_email.email, mails.email_to)
        recipients = [email for email in mails.email_to.split(',') if email]
        self.assertNotIn(follower_without_email.email, recipients)
        messages = self.env['mail.message'].search([
            ('res_id', '=', invoice.id),
            ('subject', '=', 'Unpaid reminder sent'),
        ])
        self.assertEqual(len(messages), 1)
