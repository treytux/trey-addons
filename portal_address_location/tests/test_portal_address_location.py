###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json

import odoo.tests
from odoo import Command
from odoo.http import Request


@odoo.tests.tagged('post_install', '-at_install')
class TestPortalAddressLocation(odoo.tests.HttpCase):

    def setUp(self):
        super().setUp()
        self.country = self.env.ref('base.es')
        self.state = self.env['res.country.state'].create({
            'name': 'Portal Location State',
            'code': 'TST-PORTAL-LOCATION',
            'country_id': self.country.id,
        })
        self.city = self.env['res.city'].create({
            'name': 'Portal Location City',
            'zipcode': '12345',
            'country_id': self.country.id,
            'state_id': self.state.id,
        })
        self.location = self.env['res.city.zip'].create({
            'name': '12345',
            'city_id': self.city.id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Portal Location User',
            'email': 'portal_location@test.com',
        })
        self.login = 'portal_location_user'
        self.password = 'portal_location_password'
        self.user = self.env['res.users'].with_context(
            no_reset_password=True).create({
                'name': self.partner.name,
                'login': self.login,
                'email': self.partner.email,
                'password': self.password,
                'partner_id': self.partner.id,
                'groups_id': [Command.set([
                    self.env.ref('base.group_portal').id,
                ])],
            })

    def _location_jsonrpc(self, params):
        return self.url_open(
            '/address_location_autocomplete/search',
            data=json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'id': 1,
                'params': params,
            }),
            headers={'Content-Type': 'application/json'},
        ).json()

    def test_location_search_by_zip_and_city(self):
        self.authenticate(self.login, self.password)
        by_zip = self._location_jsonrpc({
            'search': '12345',
            'country_id': self.country.id,
        })
        by_city = self._location_jsonrpc({
            'search': 'Portal Location City',
            'country_id': self.country.id,
        })
        self.assertEqual(by_zip['result'][0]['id'], self.location.id)
        self.assertEqual(by_city['result'][0]['city_id'], self.city.id)

    def test_location_search_is_filtered_by_country(self):
        other_country = self.env.ref('base.fr')
        other_city = self.env['res.city'].create({
            'name': self.city.name,
            'country_id': other_country.id,
        })
        other_location = self.env['res.city.zip'].create({
            'name': self.location.name,
            'city_id': other_city.id,
        })
        self.authenticate(self.login, self.password)
        response = self._location_jsonrpc({
            'search': self.location.name,
            'country_id': self.country.id,
        })
        result_ids = [item['id'] for item in response['result']]
        self.assertIn(self.location.id, result_ids)
        self.assertNotIn(other_location.id, result_ids)

    def test_account_updates_location_from_zip_id(self):
        self.authenticate(self.login, self.password)
        response = self.url_open('/my/account', data={
            'csrf_token': Request.csrf_token(self),
            'name': self.partner.name,
            'email': self.partner.email,
            'phone': '600000000',
            'street': 'Portal street 1',
            'city': 'Invalid city from client',
            'zipcode': '00000',
            'country_id': self.country.id,
            'state_id': self.state.id,
            'zip_id': self.location.id,
        }, allow_redirects=False)
        self.assertIn(response.status_code, (301, 302, 303, 307, 308))
        self.partner.invalidate_recordset()
        self.assertEqual(self.partner.zip_id, self.location)
        self.assertEqual(self.partner.city, self.city.name)
        self.assertEqual(self.partner.zip, self.location.name)

    def test_account_rejects_invalid_location(self):
        self.authenticate(self.login, self.password)
        response = self.url_open('/my/account', data={
            'csrf_token': Request.csrf_token(self),
            'name': self.partner.name,
            'email': self.partner.email,
            'phone': '600000000',
            'street': 'Portal street 1',
            'city': self.city.name,
            'zipcode': self.location.name,
            'country_id': self.country.id,
            'state_id': self.state.id,
            'zip_id': 999999999,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('The selected location is invalid.', response.text)
