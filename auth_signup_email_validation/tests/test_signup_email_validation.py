###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from unittest.mock import patch

from lxml.html import document_fromstring
from odoo.addons.mail.models import mail_template
from odoo.tests.common import HttpCase


class TestSignupEmailValidation(HttpCase):

    def setUp(self):
        super().setUp()
        if 'website' in self.env:
            website = self.env['website'].get_current_website()
            website.auth_signup_uninvited = 'b2c'
        self.env['ir.config_parameter'].set_param(
            'auth_signup.invitation_scope', 'b2c')
        self.data = {
            'confirm_password': 'password',
            'csrf_token': self._csrf_token(),
            'name': 'Signup email validation test',
            'password': 'password',
        }

    def _get_signup_response(self, data=None):
        with patch.object(mail_template.MailTemplate, 'send_mail'):
            return self.url_open('/web/signup', data=data)

    def _csrf_token(self):
        document = document_fromstring(self._get_signup_response().content)
        return document.xpath("//input[@name='csrf_token']")[0].get('value')

    def test_signup_keeps_standard_password_fields(self):
        document = document_fromstring(self._get_signup_response().content)
        self.assertTrue(document.xpath("//input[@name='password']"))
        self.assertTrue(document.xpath("//input[@name='confirm_password']"))

    def test_signup_normalizes_email(self):
        self.data['login'] = '  USUARIO@DOMINIO.COM  '
        self._get_signup_response(data=self.data)
        user = self.env['res.users'].search([
            ('login', '=', 'usuario@dominio.com'),
        ])
        self.assertTrue(user)
        self.assertEqual(user.email, user.login)

    def test_signup_rejects_invalid_email(self):
        self.data['login'] = 'c1@c1'
        response = self._get_signup_response(data=self.data)
        document = document_fromstring(response.content)
        self.assertTrue(document.xpath('//p[@class="alert alert-danger"]'))
        self.assertIn('Invalid email address', response.text)
        self.assertFalse(self.env['res.users'].search([
            ('login', '=', 'c1@c1'),
        ]))

    def test_signup_does_not_check_deliverability(self):
        self.data['login'] = (
            'syntax.only@domain-that-does-not-exist-987654321.com')
        self._get_signup_response(data=self.data)
        user = self.env['res.users'].search([
            ('login', '=', self.data['login']),
        ])
        self.assertTrue(user)
