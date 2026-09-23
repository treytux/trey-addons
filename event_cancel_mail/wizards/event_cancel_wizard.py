from odoo import api, fields, models


class EventCancelWizard(models.TransientModel):
    _name = 'event.cancel.wizard'
    _description = 'Wizard to cancel event'

    notify_attendees = fields.Boolean(
        string='Notify attendees',
        default=True,
    )

    @api.multi
    def action_confirm_cancel(self):
        active_ids = self.env.context.get('active_ids')
        events = self.env['event.event'].browse(active_ids)
        for event in events:
            event.button_cancel()
            if self.notify_attendees:
                event.send_apology_email()
        return {'type': 'ir.actions.act_window_close'}
