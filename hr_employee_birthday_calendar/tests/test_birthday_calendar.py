###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests.common import TransactionCase


class TestMailBirthday(TransactionCase):

    def setUp(self):
        super().setUp()
        now = fields.Datetime.now().date()
        birthday1 = now.replace(year=1980)
        birthday2 = now.replace(year=1990)
        self.employee1 = self.env['hr.employee'].create({
            'name': 'Employee 1',
            'birthday': birthday1,
        })
        self.employee2 = self.env['hr.employee'].create({
            'name': 'Employee 1',
            'birthday': birthday2,
        })

    def test_check_next_birhtday(self):
        now = fields.Datetime.now().date()
        self.assertEquals(self.employee1.current_birthday, now)
        self.assertEquals(self.employee2.current_birthday, now)

    def test_check_birhtday_notifications(self):
        self.env['ir.config_parameter'].set_param(
            'hr_employee_birthday_calendar.employee_birthday_notification', True
        )
        before_messages = self.env.ref('mail.channel_all_employees').message_ids
        self.employee1.cron_send_birthday_notification()
        after_messages = self.env.ref('mail.channel_all_employees').message_ids
        my_message = after_messages - before_messages
        self.assertTrue(my_message)
        self.assertIn('Today is the birthday of:', my_message.body)
