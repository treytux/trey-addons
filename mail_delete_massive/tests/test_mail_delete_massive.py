###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import TransactionCase


class TestMailDeleteMassive(TransactionCase):

    def setUp(self):
        super().setUp()
        self.mail = self.env['mail.mail'].create({
            'subject': 'Test Mail Exception',
            'body_html': '<p>Test content</p>',
            'email_to': 'test@example.com',
        })

    def test_delete(self):
        wizard = self.env['mail.delete.massive'].with_context(
            active_ids=[self.mail.id]
        ).create({})
        wizard.action_delete()
        self.assertFalse(self.mail.exists())

    def test_no_emails_selected(self):
        wizard = self.env['mail.delete.massive'].with_context(
            active_ids=[]
        ).create({})
        with self.assertRaises(AssertionError) as result:
            wizard.action_delete()
        self.assertIn('Missing active_ids', str(result.exception))
