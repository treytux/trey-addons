from odoo import api, models


class EventEvent(models.Model):
    _inherit = 'event.event'

    @api.multi
    def button_cancel_email(self):
        self.ensure_one()
        avoid_send_mail = self.env.context.get('avoid_send', False)
        if not self.seats_expected or avoid_send_mail:
            self.button_cancel()
            return
        action = self.env.ref(
            'event_cancel_mail.action_event_cancel_wizard').read()[0]
        return action

    @api.multi
    def send_apology_email(self):
        for event in self:
            email_template = self.env.ref(
                'event_cancel_mail.email_template_event_cancellation')
            for attendee in event.registration_ids.filtered(
                    lambda reg: reg.partner_id.email or reg.email):
                attendee.message_post_with_template(
                    email_template.id,
                    composition_mode='comment',
                )
        return True
