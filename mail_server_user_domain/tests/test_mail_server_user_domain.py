###############################################################################
# For copyright and license notices, see __manifest__.py in root directory
###############################################################################
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestMailServerUserDomain(TransactionCase):

    def setUp(self):
        super().setUp()
        self.smtp_allowed = self.env['ir.mail_server'].create({
            'name': 'Allowed SMTP',
            'smtp_host': 'smtp.allowed.com',
            'smtp_user': 'user@allowed.com',
            'smtp_pass': 'pass',
        })
        self.smtp_fetch = self.env['ir.mail_server'].create({
            'name': 'Fetchmail SMTP',
            'smtp_host': 'smtp.fetch.com',
            'smtp_user': 'fetchuser@fetch.com',
            'smtp_pass': 'pass',
        })
        self.smtp_company = self.env['ir.mail_server'].create({
            'name': 'Company SMTP',
            'smtp_host': 'smtp.company.com',
            'smtp_user': 'company@company.com',
            'smtp_pass': 'pass',
        })
        self.fetchmail_server = self.env['fetchmail.server'].create({
            'name': 'Test Fetchmail',
            'server': 'mail.fetch.com',
            'user': 'fetchuser@fetch.com',
            'password': 'pass',
        })
        self.user_allowed = self.env['res.users'].create({
            'name': 'Allowed User',
            'login': 'allowed',
            'email': '"Sender" <sender@allowed.com>',
        })
        self.user_not_allowed = self.env['res.users'].create({
            'name': 'Not Allowed User',
            'login': 'notallowed',
            'email': 'sender@unknown.com',
        })
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
            'email': 'company@company.com',
        })
        self.record_with_company = self.env['res.partner'].create({
            'name': 'Company Record',
            'company_id': self.company.id,
        })
        self.env['ir.config_parameter'].set_param(
            'mail.catchall.alias', 'catchall')

    @patch('odoo.addons.mail.models.mail_mail.MailMail._send')
    def test_smtp_selected_by_email_from_domain(self, mock_send):
        mail = self.env['mail.mail'].create({
            'subject': 'Test',
            'body_html': '<p>Test</p>',
            'author_id': self.user_allowed.partner_id.id,
            'email_from': 'sender@allowed.com',
            'email_to': 'customer@example.com',
        })
        mail.send()
        self.assertEqual(mail.mail_server_id.id, self.smtp_allowed.id)

    @patch('odoo.addons.mail.models.mail_mail.MailMail._send')
    def test_fetchmail_server_determines_smtp(self, mock_send):
        mail = self.env['mail.mail'].create({
            'subject': 'Test',
            'body_html': '<p>Test</p>',
            'author_id': self.user_not_allowed.partner_id.id,
            'fetchmail_server_id': self.fetchmail_server.id,
            'email_to': 'customer@example.com',
        })
        mail.send()
        self.assertEqual(mail.mail_server_id.id, self.smtp_fetch.id)

    @patch('odoo.addons.mail.models.mail_mail.MailMail._send')
    def test_company_email_domain_fallback(self, mock_send):
        mail = self.env['mail.mail'].create({
            'subject': 'Test',
            'body_html': '<p>Test</p>',
            'author_id': self.user_not_allowed.partner_id.id,
            'model': 'res.partner',
            'res_id': self.record_with_company.id,
            'email_to': 'customer@example.com',
        })
        mail.send()
        self.assertEqual(mail.mail_server_id.id, self.smtp_company.id)

    @patch('odoo.addons.mail.models.mail_mail.MailMail._send')
    def test_reply_to_uses_catchall_and_user_domain(self, mock_send):
        mail = self.env['mail.mail'].create({
            'subject': 'Test',
            'body_html': '<p>Test</p>',
            'author_id': self.user_allowed.partner_id.id,
            'email_from': 'sender@allowed.com',
            'email_to': 'customer@example.com',
        })
        mail.send()
        self.assertEqual(mail.reply_to, 'catchall@allowed.com')

    @patch('odoo.addons.mail.models.mail_mail.MailMail._send')
    def test_email_from_rewritten_for_fetchmail_notification(self, mock_send):
        mail = self.env['mail.mail'].create({
            'subject': 'Test',
            'body_html': '<p>Test</p>',
            'author_id': self.user_not_allowed.partner_id.id,
            'fetchmail_server_id': self.fetchmail_server.id,
            'email_to': 'customer@example.com',
            'message_type': 'notification',
        })
        mail.send()
        name = self.user_not_allowed.partner_id.name.replace(',', ' ')
        expected = f'{name} <catchall@fetch.com>'
        self.assertEqual(mail.email_from, expected)

    @patch('odoo.addons.mail.models.mail_mail.MailMail._send')
    def test_email_from_rewritten_for_fetchmail_comment(self, mock_send):
        mail = self.env['mail.mail'].create({
            'subject': 'Test',
            'body_html': '<p>Test</p>',
            'author_id': self.user_not_allowed.partner_id.id,
            'fetchmail_server_id': self.fetchmail_server.id,
            'email_to': 'customer@example.com',
            'message_type': 'comment',
        })
        mail.send()
        name = self.user_not_allowed.partner_id.name.replace(',', ' ')
        expected = f'{name} <catchall@fetch.com>'
        self.assertEqual(mail.email_from, expected)

    @patch('odoo.addons.mail.models.mail_mail.MailMail.send', autospec=True)
    def test_send_supports_multiple_mails(self, mock_send):
        mails = self.env['mail.mail'].create([
            {
                'subject': 'Allowed domain',
                'body_html': '<p>Test</p>',
                'email_from': 'sender@allowed.com',
                'email_to': 'customer@example.com',
            },
            {
                'subject': 'Company fallback',
                'body_html': '<p>Test</p>',
                'author_id': self.user_not_allowed.partner_id.id,
                'model': 'res.partner',
                'res_id': self.record_with_company.id,
                'email_to': 'customer@example.com',
            },
        ])
        mails.send()
        self.assertEqual(mails[0].mail_server_id, self.smtp_allowed)
        self.assertEqual(mails[1].mail_server_id, self.smtp_company)
        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args.args[0], mails)
