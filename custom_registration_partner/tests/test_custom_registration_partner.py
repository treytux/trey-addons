from datetime import timedelta

from odoo import fields, http
from odoo.tests.common import HttpCase


class TestEventRegistrationError(HttpCase):
    def setUp(self):
        super(TestEventRegistrationError, self).setUp()
        res_config = self.env['res.config.settings']
        self.default_values = res_config.default_get(
            list(res_config.fields_get()))
        self.event = self.env['event.event'].create({
            'name': 'Test',
            'is_published': True,
            'forbid_duplicates': True,
            'date_begin': fields.Datetime.now(),
            'date_end': fields.Datetime.now() + timedelta(days=1),
        })
        self.test_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user@mail.com',
            'email': 'test_user@mail.com',
            'password': 'test_password',
        })

    def _get_free_login_url(self):
        return '/web/login'

    def test_event_registration_duplicate_error(self):
        username = 'test_user@mail.com'
        password = 'test_password'
        self.authenticate(None, None)
        csrf_token = http.Request.csrf_token(self)
        payload = {
            'login': username,
            'password': password,
            'csrf_token': csrf_token,
        }
        url_free_login = self._get_free_login_url()
        self.url_open(url_free_login, data=payload)
        data = {
            '1-name': username,
            '1-email': username,
            '1-phone': '',
            '1-event_ticket_id': '0',
            'csrf_token': csrf_token,
        }
        url = f'/event/{self.event.name}-{self.event.id}/registration/confirm'
        response_ok = self.url_open(url, data=data, timeout=6000)
        self.assertEqual(response_ok.status_code, 200)
        registrations = self.env['event.registration'].search([
            ('email', '=', username),
        ])
        self.assertEqual(len(registrations), 1)
        url = f'/event/{self.event.name}-{self.event.id}/registration/confirm'
        response_template_error = self.url_open(url, data=data, timeout=6000)
        self.assertIn(
            '<h4>Your company is already registered for this event!</h4>',
            response_template_error.text
        )
        self.assertEqual(response_template_error.status_code, 200)
        registrations = self.env['event.registration'].search([
            ('email', '=', username),
        ])
        self.assertEqual(len(registrations), 1)
