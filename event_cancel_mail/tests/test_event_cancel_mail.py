from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestEventEvent(TransactionCase):

    def setUp(self):
        super(TestEventEvent, self).setUp()
        self.Event = self.env['event.event']
        self.Registration = self.env['event.registration']

        self.event = self.Event.create({
            'name': 'Test Event',
            'date_begin': '2024-06-12 10:00:00',
            'date_end': '2024-06-12 12:00:00',
        })

        self.registration = self.Registration.create({
            'event_id': self.event.id,
            'partner_id': self.env.ref('base.partner_admin').id,
            'state': 'done',
        })

    def test_button_cancel(self):
        self.registration.write({'state': 'draft'})
        action = self.event.button_cancel_email()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'event.cancel.wizard')
        self.assertEqual(action['target'], 'new')

    def test_send_apology_email(self):
        mock_path = (
            'odoo.addons.mail.models.mail_template.'
            'MailTemplate.send_mail'
        )
        with patch(mock_path, return_value=True) as mock_send_mail:
            result = self.event.send_apology_email()
            self.assertTrue(result)
            self.assertEqual(
                mock_send_mail.call_count,
                len(self.event.registration_ids.filtered(
                    lambda reg: reg.partner_id.email))
            )

    def test_wizard_confirm_cancel_with_notify(self):
        wizard = self.env['event.cancel.wizard'].create({
            'notify_attendees': True,
        })
        mock_path = (
            'odoo.addons.mail.models.mail_template.'
            'MailTemplate.send_mail'
        )
        self.registration.write({'state': 'draft'})
        with patch(mock_path, return_value=True) as mock_send_mail:
            (wizard
                .with_context(active_ids=[self.event.id])
                .action_confirm_cancel())
            self.assertEqual(
                mock_send_mail.call_count,
                len(self.event.registration_ids.filtered(
                    lambda reg: reg.partner_id.email))
            )
        action = wizard.action_confirm_cancel()
        self.assertEqual(action, {'type': 'ir.actions.act_window_close'})

    def test_wizard_confirm_cancel_without_notify(self):
        wizard = self.env['event.cancel.wizard'].create({
            'notify_attendees': False,
        })
        mock_path = (
            'odoo.addons.mail.models.mail_template.'
            'MailTemplate.send_mail'
        )
        self.registration.write({'state': 'draft'})
        with patch(mock_path, return_value=True) as mock_send_mail:
            (wizard
                .with_context(active_ids=[self.event.id])
                .action_confirm_cancel())
            self.assertEqual(mock_send_mail.call_count, 0)
        action = wizard.action_confirm_cancel()
        self.assertEqual(action, {'type': 'ir.actions.act_window_close'})
