###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestMailRetrySendMassive(TransactionCase):

    def setUp(self):
        super().setUp()
        self.mail_exception = self.env['mail.mail'].create({
            'subject': 'Test Mail Exception',
            'body_html': '<p>Test content</p>',
            'email_to': 'test@example.com',
            'state': 'exception',
        })
        self.mail_sent = self.env['mail.mail'].create({
            'subject': 'Test Mail Sent',
            'body_html': '<p>Test content 2</p>',
            'email_to': 'test2@example.com',
            'state': 'sent',
        })

    def test_retry_send_with_exception_state(self):
        wizard = self.env['mail.retry.send.massive'].with_context(
            active_ids=[self.mail_exception.id]
        ).create({})
        wizard.action_retry_send()
        self.assertEqual(self.mail_exception.state, 'sent')

    def test_retry_send_with_sent_state_fails(self):
        wizard = self.env['mail.retry.send.massive'].with_context(
            active_ids=[self.mail_sent.id]
        ).create({})
        with self.assertRaises(UserError) as result:
            wizard.action_retry_send()
        self.assertIn(
            'No emails in exception or cancel state found', str(result.exception)
        )

    def test_retry_send_mixed_states(self):
        wizard = self.env['mail.retry.send.massive'].with_context(
            active_ids=[self.mail_exception.id, self.mail_sent.id]
        ).create({})
        wizard.action_retry_send()
        self.assertEqual(self.mail_exception.state, 'sent')
        self.assertEqual(self.mail_sent.state, 'sent')

    def test_no_emails_selected(self):
        wizard = self.env['mail.retry.send.massive'].with_context(
            active_ids=[]
        ).create({})
        with self.assertRaises(AssertionError) as result:
            wizard.action_retry_send()
        self.assertIn('Missing active_ids', str(result.exception))
