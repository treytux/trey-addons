from odoo import _, api, models
from odoo.exceptions import ValidationError


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    @api.constrains('event_id', 'attendee_partner_id')
    def _check_custom_forbid_duplicates(self):
        for event_reg in self.filtered('event_id.forbid_duplicates'):
            dupes = self.search(event_reg._duplicate_search_domain())
            if dupes:
                error_message = _('Your company is already registered for this event!')
                raise ValidationError(error_message)

    def _duplicate_search_domain(self):
        return [
            ("id", "!=", self.id),
            ("event_id", "=", self.event_id.id),
            ("attendee_partner_id.email", "=", self.attendee_partner_id.email),
            ("attendee_partner_id", "!=", False),
        ]
