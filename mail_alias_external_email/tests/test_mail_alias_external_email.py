###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import re

from odoo import exceptions
from odoo.addons.test_mail.tests.test_mail_gateway import MAIL_TEMPLATE
from odoo.tests import SavepointCase


class TestMailAliasExternalEmail(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.server = cls.env['fetchmail.server'].create({
            'name': 'Demo server',
            'type': 'pop',
            'server': 'pop3.example.com',
        })
        cls.mail_server = cls.env['ir.mail_server'].create({
            'name': 'localhost',
            'smtp_host': 'localhost',
            'smtp_user': 'email_smtp_user@test.com',
        })

    def test_check_thread_and_not_send_email(self):
        self.assertFalse(self.server.object_id)
        self.server.object_id = self.env['ir.model'].search([], limit=1)
        self.assertTrue(self.server.object_id)
        alias_name = 'alias'
        self.env['mail.alias'].create({
            'alias_model_id': self.server.object_id.id,
            'alias_name': alias_name,
            'external_email': 'you@example.com',
        })
        alias = self.env['mail.alias'].search([
            ('alias_name', '=', alias_name),
        ])
        self.assertEqual(len(alias), 1)
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        comments = len(partner.message_ids)
        msg = 'This is a test'
        partner.with_context(
            fetchmail_server_id=self.server.id).message_process(
                partner._name, msg, thread_id=partner.id)
        partner.refresh()
        self.assertNotEqual(comments, len(partner.message_ids))
        self.assertEqual(comments + 1, len(partner.message_ids))
        mail = self.env['mail.mail'].search([
            ('subject', '=', 'Partner test'),
            ('email_to', '=', 'you@example.com'),
            ('email_from', '=', self.mail_server.smtp_user),
        ])
        self.assertEqual(len(mail), 0)

    def test_check_send_email_to_external_email_alias_no_thread(self):
        self.assertFalse(self.server.object_id)
        self.server.object_id = self.env['ir.model'].search([], limit=1)
        self.assertTrue(self.server.object_id)
        self.env['mail.alias'].create({
            'alias_model_id': self.server.object_id.id,
            'alias_name': 'alias',
            'external_email': 'you@example.com',
        })
        alias_name = 'alias@example.com'
        self.env['mail.thread'].with_context(
            fetchmail_server_id=self.server.id).message_process(
                self.server.object_id.model,
                MAIL_TEMPLATE.format(
                    email_from='spambot@example.com',
                    to=alias_name,
                    cc='nobody@example.com',
                    subject='Im a robot, hello',
                    extra='',
                    msg_id='<filter.happier.more.productive@example.com>'
                ).encode('utf-8'),
                save_original=self.server.original,
                strip_attachments=not self.server.attach)
        mail = alias_name and re.findall(
            r'[\w.+-]+@[\w-]+\.[\w.-]+', alias_name) or []
        self.assertEqual(len(mail), 1)
        pos = mail[0].find('@')
        alias = self.env['mail.alias'].search([
            ('alias_name', '=', mail[0][:pos]),
        ])
        self.assertEqual(len(alias), 1)
        mail = self.env['mail.mail'].search([
            ('subject', '=', 'Im a robot, hello'),
            ('email_to', '=', 'you@example.com'),
            ('email_from', '=', self.mail_server.smtp_user),
        ])
        self.assertEqual(len(mail), 1)

    def test_check_multiples_email_to_01(self):
        self.assertFalse(self.server.object_id)
        self.server.object_id = self.env['ir.model'].search([], limit=1)
        self.assertTrue(self.server.object_id)
        self.env['mail.alias'].create({
            'alias_model_id': self.server.object_id.id,
            'alias_name': 'alias',
            'external_email': 'you@example.com',
        })
        email_to = 'alias@example.com, prueba@example.com'
        self.env['mail.thread'].with_context(
            fetchmail_server_id=self.server.id).message_process(
                self.server.object_id.model,
                MAIL_TEMPLATE.format(
                    email_from='spambot@example.com',
                    to=email_to,
                    cc='nobody@example.com',
                    subject='Im a robot, hello',
                    extra='',
                    msg_id='<filter.happier.more.productive@example.com>'
                ).encode('utf-8'),
            save_original=self.server.original,
            strip_attachments=not self.server.attach,
        )
        mail = email_to and re.findall(
            r'[\w.+-]+@[\w-]+\.[\w.-]+', email_to) or []
        self.assertEqual(len(mail), 2)
        pos_01 = mail[0].find('@')
        pos_02 = mail[1].find('@')
        alias = self.env['mail.alias'].search([
            '|',
            ('alias_name', '=', mail[0][:pos_01]),
            ('alias_name', '=', mail[1][:pos_02]),
        ])
        self.assertEqual(len(alias), 1)
        mail = self.env['mail.mail'].search([
            ('subject', '=', 'Im a robot, hello'),
            ('email_to', '=', 'you@example.com'),
            ('email_from', '=', self.mail_server.smtp_user),
        ])
        self.assertEqual(len(mail), 1)

    def test_check_multiples_email_to_02(self):
        self.assertFalse(self.server.object_id)
        self.server.object_id = self.env['ir.model'].search([], limit=1)
        self.assertTrue(self.server.object_id)
        self.env['mail.alias'].create({
            'alias_model_id': self.server.object_id.id,
            'alias_name': 'alias',
            'external_email': 'you@example.com',
        })
        email_to = (
            'Dominique Pinon <support+unnamed@test.com>, alias@example.com')
        self.env['mail.thread'].with_context(
            fetchmail_server_id=self.server.id).message_process(
                self.server.object_id.model,
                MAIL_TEMPLATE.format(
                    email_from='spambot@example.com',
                    to=email_to,
                    cc='nobody@example.com',
                    subject='Im a robot, hello',
                    extra='',
                    msg_id='<filter.happier.more.productive@example.com>'
                ).encode('utf-8'),
                save_original=self.server.original,
                strip_attachments=not self.server.attach,
        )
        mail = email_to and re.findall(
            r'[\w.+-]+@[\w-]+\.[\w.-]+', email_to) or []
        self.assertEqual(len(mail), 2)
        pos_01 = mail[0].find('@')
        pos_02 = mail[1].find('@')
        alias = self.env['mail.alias'].search([
            '|',
            ('alias_name', '=', mail[0][:pos_01]),
            ('alias_name', '=', mail[1][:pos_02]),
        ])
        self.assertEqual(len(alias), 1)
        mail = self.env['mail.mail'].search([
            ('subject', '=', 'Im a robot, hello'),
            ('email_to', '=', 'you@example.com'),
            ('email_from', '=', self.mail_server.smtp_user),
        ])
        self.assertEqual(len(mail), 1)

    def test_not_alias_find(self):
        self.assertFalse(self.server.object_id)
        self.server.object_id = self.env['ir.model'].search([], limit=1)
        self.assertTrue(self.server.object_id)
        alias_name = 'alias@example'
        email_to = 'you@example.com'
        self.env['mail.thread'].with_context(
            fetchmail_server_id=self.server.id).message_process(
                self.server.object_id.model,
                MAIL_TEMPLATE.format(
                    email_from='spambot@example.com',
                    to=email_to,
                    cc='nobody@example.com',
                    subject='Im a robot, hello',
                    extra='',
                    msg_id='<filter.happier.more.productive@example.com>'
                ).encode('utf-8'),
                save_original=self.server.original,
                strip_attachments=not self.server.attach)
        mail = email_to and re.findall(
            r'[\w.+-]+@[\w-]+\.[\w.-]+', email_to) or []
        self.assertEqual(len(mail), 1)
        pos = mail[0].find('@')
        alias = self.env['mail.alias'].search([
            ('alias_name', '=', mail[0][:pos]),
        ])
        self.assertFalse(alias)
        mail = self.env['mail.mail'].search([
            ('subject', '=', 'Im a robot, hello'),
            ('email_to', '=', alias_name),
            ('email_from', '=', self.mail_server.smtp_user),
        ])
        self.assertFalse(mail)

    def test_check_error_constraint_external_email_is_valid(self):
        alias = self.env['mail.alias'].create({
            'alias_model_id': self.env['ir.model']._get('res.partner').id,
            'alias_name': 'support+unnamed',
        })
        self.assertFalse(alias.external_email)
        with self.assertRaises(exceptions.ValidationError) as result:
            alias.external_email = 'test_XX_999'
        self.assertEqual(
            result.exception.name, 'Not a valid email')

    def test_check_ok_constraint_external_email_is_valid(self):
        alias = self.env['mail.alias'].create({
            'alias_model_id': self.env['ir.model']._get('res.partner').id,
            'alias_name': 'support+unnamed',
        })
        self.assertFalse(alias.external_email)
        alias.external_email = 'test@example.com'
        self.assertTrue(alias.external_email)
