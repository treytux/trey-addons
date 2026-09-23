###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.website_event.controllers.main import WebsiteEventController
from odoo.http import request


class WebsiteEventController(WebsiteEventController):
    @http.route('/event/registration/error',
                type='http', auth='public', website=True)
    def event_registration_error(self):
        return request.render(
            'custom_registration_partner.registration_error_template')

    @http.route()
    def registration_confirm(self, event, **post):
        if event.forbid_duplicates:
            email_keys = [key for key in post if key.endswith('-email')]
            email_values = [post.get(key) for key in email_keys]
            if len(email_values) != len(set(email_values)):
                return self.event_registration_error()
            event_obj = request.env['event.registration'].sudo()
            registration_count = 0
            for email_key in email_keys:
                email = post.get(email_key)
                if email:
                    registration_count += event_obj.search_count([
                        ('event_id', '=', event.id),
                        ('email', '=', email),
                    ])
            if registration_count > 0:
                return self.event_registration_error()
        return super().registration_confirm(event, **post)
