###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase


class TestProjectNegativeBalanceReminder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._ensure_lang_installed('es_ES')

    @classmethod
    def _ensure_lang_installed(cls, code):
        lang_model = cls.env['res.lang'].with_context(active_test=False)
        lang = lang_model._activate_lang(code)
        if not lang:
            lang = lang_model._create_lang(code)
        mods = cls.env['ir.module.module'].search([
            ('state', '=', 'installed'),
        ])
        mods._update_translations([code], overwrite=True)
        return lang

    def setUp(self):
        super().setUp()
        self.project = self.env['project.project'].with_context(
            mail_create_nosubscribe=True
        ).create({
            'name': 'Test Project',
            'extra_balance': -1.0,
            'extra_balance_date': fields.Date.today(),
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Follower',
            'email': 'follower@example.com',
        })

    def test_negative_balance_notification(self):
        today = fields.Date.today()
        self.project.message_subscribe(partner_ids=self.partner.ids)
        with patch.object(
            type(self.project), '_get_notify_candidates_domain', return_value=[
                ('id', '=', self.project.id)]), patch.object(type(
                    self.project), '_has_negative_balance', return_value=True
        ):
            self.project.check_and_notify_negative_balance()
        self.assertEqual(self.project.last_notification_date, today)

    def test_non_negative_balance_does_not_notify(self):
        self.project.extra_balance = 2.0
        with patch.object(
            type(self.project), '_get_notify_candidates_domain', return_value=[
                ('id', '=', self.project.id)]), patch.object(type(
                    self.project), '_has_negative_balance', return_value=False
        ):
            self.project.check_and_notify_negative_balance()
        self.assertFalse(self.project.last_notification_date)

    def test_renewal_period_days_is_respected(self):
        today = fields.Date.today()
        self.project.last_notification_date = today
        self.project.message_subscribe(partner_ids=self.partner.ids)
        with patch.object(
            type(self.project), '_get_notify_candidates_domain', return_value=[
                ('id', '=', self.project.id)]), patch.object(type(
                    self.project), '_has_negative_balance', return_value=True
        ):
            self.project.check_and_notify_negative_balance()
        self.assertEqual(self.project.last_notification_date, today)

    def test_non_maintenance_project_does_not_notify(self):
        self.project.message_subscribe(partner_ids=self.partner.ids)
        with patch.object(
            type(self.project), '_get_notify_candidates_domain', return_value=[
                ('id', '=', False)]
        ):
            self.project.check_and_notify_negative_balance()
        self.assertFalse(self.project.last_notification_date)

    def test_false_follower_email_is_ignored(self):
        no_email_partner = self.env['res.partner'].create({
            'name': 'No Email Follower',
        })
        self.project.message_subscribe(
            partner_ids=(self.partner | no_email_partner).ids)
        self.project._send_negative_balance_email()
        notify_messages = self.env['mail.message'].search([
            ('model', '=', 'project.project'),
            ('res_id', '=', self.project.id),
            ('message_type', '=', 'user_notification'),
        ])
        self.assertTrue(notify_messages)
        notified_emails = set(
            notify_messages.notification_ids.mapped('res_partner_id.email')
        )
        self.assertIn('follower@example.com', notified_emails)
        self.assertNotIn(False, notified_emails)

    def test_no_follower_emails_does_not_crash(self):
        self.project._send_negative_balance_email()
        notify_messages = self.env['mail.message'].search([
            ('model', '=', 'project.project'),
            ('res_id', '=', self.project.id),
            ('message_type', '=', 'user_notification'),
        ])
        self.assertFalse(notify_messages)

    def test_notify_uses_partner_lang_for_email_and_company_for_wall(self):
        installed_langs = self.env['res.lang'].search([]).mapped('code')
        self.assertIn('es_ES', installed_langs)
        self.assertIn('en_US', installed_langs)
        self.env.company.partner_id.write({'lang': 'es_ES'})
        self.partner.write({'lang': 'es_ES'})
        follower_en = self.env['res.partner'].create({
            'name': 'Follower EN',
            'email': 'en@example.com',
            'lang': 'en_US',
        })
        self.project.message_subscribe(
            partner_ids=(self.partner | follower_en).ids
        )
        self.env.user.write({'lang': 'en_US'})
        self.project._send_negative_balance_email()
        wall_messages = self.project.message_ids.filtered(
            lambda m: 'Estimados seguidores' in (m.body or '')
        )
        self.assertTrue(wall_messages)
        wall_message = wall_messages.sorted('id')[-1]
        self.assertIn('Estimados seguidores', wall_message.body)
        self.assertNotIn('Dear followers', wall_message.body)
        notify_messages = self.env['mail.message'].search([
            ('model', '=', 'project.project'),
            ('res_id', '=', self.project.id),
            ('message_type', '=', 'user_notification'),
        ])
        self.assertTrue(notify_messages)
        notified_emails = set(
            notify_messages.notification_ids.mapped('res_partner_id.email')
        )
        self.assertIn('follower@example.com', notified_emails)
        self.assertIn('en@example.com', notified_emails)
        notify_bodies = ' '.join(notify_messages.mapped('body'))
        self.assertIn('Estimados seguidores', notify_bodies)
        self.assertIn('Dear followers', notify_bodies)
