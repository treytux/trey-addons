###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestWebsiteSaleNotifyEmail(TransactionCase):
    def setUp(self):
        super().setUp()
        self.website = self.env['website'].create({
            'name': 'Test Website',
            'notify_new_sale': True,
            'notification_type': 'email',
            'notification_email': 'test@yourdomain.com',
            'notification_body': 'You have a new sale',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })

    def test_new_sale_notify_email(self):
        self.assertEqual(len(self.env['mail.mail'].search([])), 0)
        self.env['sale.order'].create({
            'website_id': self.website.id,
            'partner_id': self.partner.id,
        })
        mail = self.env['mail.mail'].search([])
        self.assertEqual(len(mail), 1)
        self.assertEqual(mail.subject, 'New sale from web: Test Website')
        self.assertEqual(mail.body_html, '<p>You have a new sale</p>')
