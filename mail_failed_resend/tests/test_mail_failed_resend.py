###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime, timedelta

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestMailFailedResend(TransactionCase):

    def setUp(self):
        super().setUp()
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        self.wizard1 = self.env['mail.failed.resend'].create({
            'date_from': today,
            'date_to': tomorrow,
        })

    def test_check_dates(self):
        yesterday = datetime.now().date() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.wizard1.date_to = yesterday
