###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSurveyNotification(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.survey = self.env['survey.survey'].create({
            'title': 'Test Survey',
            'access_mode': 'public',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Follower',
            'email': 'follower@test.com',
        })
        self.survey.message_subscribe(partner_ids=[self.partner.id])

    def test_notification_enabled(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'survey_completion_notification.survey_notify', True)
        user_input = self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
            'email': 'respondent@test.com',
        })
        initial_count = len(user_input.message_ids)
        user_input._mark_done()
        self.assertEqual(len(user_input.message_ids), initial_count + 1)

    def test_notification_disabled(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'survey_completion_notification.survey_notify', False)
        user_input = self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
            'email': 'respondent@test.com',
        })
        initial_count = len(user_input.message_ids)
        user_input._mark_done()
        self.assertEqual(len(user_input.message_ids), initial_count)
