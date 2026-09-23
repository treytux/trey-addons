###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, timedelta

from odoo.tests.common import TransactionCase


class TestMailBirthday(TransactionCase):

    def setUp(self):
        super().setUp()
        current_datetime = datetime.now()
        next_day = datetime.now() + timedelta(days=1)
        self.partner1 = self.env['res.partner'].create({
            'name': 'Partner test 1',
            'email': 'partnertest1@example.com',
            'birthdate_date': current_datetime,
        })
        self.partner2 = self.env['res.partner'].create({
            'name': 'Partner test 2',
            'email': 'partnertest2@example.com',
            'birthdate_date': next_day,
        })

    def test_check_message(self):
        self.assertEquals(len(self.partner1.message_ids), 1)
        self.env['res.partner'].send_birthday_mail_alert()
        self.assertEquals(len(self.partner1.message_ids), 2)
        self.assertTrue(self.partner1.message_ids)
        birth_msg = self.partner1.message_ids[0].body
        self.assertIn('we wish you ', birth_msg)

    def test_check_mail(self):
        before_mails = self.env['mail.mail'].search([
            ('recipient_ids', 'in', self.partner1.ids),
        ])
        self.env['res.partner'].send_birthday_mail_alert()
        after_mails = self.env['mail.mail'].search([
            ('recipient_ids', 'in', self.partner1.ids),
        ])
        my_mail = after_mails - before_mails
        self.assertTrue(my_mail)
