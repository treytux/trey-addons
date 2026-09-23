###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo.tests.common import TransactionCase


class TestMailServerCrmLogo(TransactionCase):

    def setUp(self):
        super().setUp()
        self.sale_installed = self.env['ir.module.module'].search([
            ('name', '=', 'sale'),
            ('state', '=', 'installed')
        ])
        self.test_partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@example.com',
        })
        self.crm_team = self.env['crm.team'].create({
            'name': 'Test Sales Team',
            'logo': base64.b64encode(b'test-logo').decode(),
        })

    def test_sale_order_email_logo_replacement(self):
        if not self.sale_installed:
            self.skipTest('sale module not installed')
        sale_order = self.env['sale.order'].create({
            'partner_id': self.test_partner.id,
            'team_id': self.crm_team.id,
        })
        message = self.env['mail.message'].create({
            'model': 'sale.order',
            'res_id': sale_order.id,
            'message_id': '<logo-team-test@example.com>',
            'message_type': 'comment',
        })
        smtp_message = self.env['ir.mail_server'].build_email(
            email_from='"Administrator" <admin@example.com>',
            email_to=['customer@example.com'],
            subject='Test',
            body=('<html><body>Text with accents: áéíóú ñ '
                  '<img src="/logo.png?company=1"/></body></html>'),
            message_id=message.message_id,
            subtype='html')
        smtp_session = (
            type('SMTP', (), {'from_filter': False, 'smtp_from': False})())
        _smtp_from, _smtp_to_list, message = (
            self.env['ir.mail_server']._prepare_email_message(
                smtp_message, smtp_session)
        )
        html_part = next(
            part for part in message.walk()
            if part.get_content_type() == 'text/html')
        html = html_part.get_payload(decode=True).decode(
            html_part.get_content_charset() or 'utf-8')
        self.assertIn('Text with accents: áéíóú ñ', html)
        self.assertIn(f'/team_logo/{self.crm_team.id}', html)
        self.assertNotIn('/logo.png', html)
