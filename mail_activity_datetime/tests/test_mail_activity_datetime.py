###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import timedelta

from odoo import fields
from odoo.tests import common


class TestMailActivityDatetime(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.employee = self.env['res.users'].create({
            'company_id': self.env.ref('base.main_company').id,
            'name': 'Test User',
            'login': 'testuser',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })
        self.meeting_activity = self.env['mail.activity.type'].search(
            [('name', '=', 'Meeting')], limit=1)
        self.call_activity = self.env['mail.activity.type'].search([
            ('name', '=', 'Call')], limit=1)

    def test_create_mail_activity_short_duration(self):
        activity = self.env['mail.activity'].create({
            'activity_type_id': self.call_activity.id,
            'res_id': self.env.ref('base.res_partner_1').id,
            'res_model_id': self.env['ir.model']._get('res.partner').id,
            'user_id': self.employee.id,
            'activity_all_day': False,
            'activity_date': fields.Datetime.now(),
            'activity_duration': 2,
        })
        self.assertEqual(self.employee.id, activity.user_id.id)
        self.assertFalse(activity.activity_all_day)
        self.assertEqual(activity.activity_id, self.call_activity.id)
        self.assertEqual(
            activity.date_deadline.strftime('%Y-%m-%d'),
            activity.activity_date.strftime('%Y-%m-%d'))
        self.assertEqual(activity.activity_duration, 2)

    def test_create_mail_activity_duration_all_day(self):
        activity = self.env['mail.activity'].create({
            'activity_type_id': self.call_activity.id,
            'res_id': self.env.ref('base.res_partner_1').id,
            'res_model_id': self.env['ir.model']._get('res.partner').id,
            'user_id': self.employee.id,
            'activity_all_day': True,
            'activity_all_day_date': fields.Date.today() + timedelta(days=2)
        })
        self.assertEqual(self.employee.id, activity.user_id.id)
        self.assertTrue(activity.activity_all_day)
        self.assertEqual(activity.activity_id, self.call_activity.id)
        self.assertEqual(
            activity.activity_all_day_date,
            fields.Date.today() + timedelta(days=2))
        self.assertEqual(activity.activity_duration, 1)
        self.assertEqual(
            activity.activity_date.strftime('%Y-%m-%d'),
            activity.date_deadline.strftime('%Y-%m-%d'))

    def test_create_planned_action_for_meeting(self):
        activity = self.env['mail.activity'].create({
            'activity_type_id': self.meeting_activity.id,
            'res_id': self.env.ref('base.res_partner_1').id,
            'res_model_id': self.env['ir.model']._get('res.partner').id,
            'user_id': self.employee.id,
        })
        self.assertFalse(activity.activity_all_day)
