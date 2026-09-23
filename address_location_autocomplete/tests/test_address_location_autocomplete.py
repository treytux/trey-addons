###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json

import odoo.tests


@odoo.tests.tagged('post_install', '-at_install')
class TestAddressLocationAutocomplete(odoo.tests.HttpCase):

    def setUp(self):
        super().setUp()
        self.country = self.env.ref('base.es')
        self.state = self.env['res.country.state'].create({
            'name': 'Address Location State',
            'code': 'TST-ADDRESS-LOCATION',
            'country_id': self.country.id,
        })
        self.city = self.env['res.city'].create({
            'name': 'Address Location City',
            'zipcode': '54321',
            'country_id': self.country.id,
            'state_id': self.state.id,
        })
        self.location = self.env['res.city.zip'].create({
            'name': '54321',
            'city_id': self.city.id,
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
            headers={'Content-Type': 'application/json'}
        ).json()

    def test_search_by_zip_and_city_is_public(self):
        by_zip = self._location_jsonrpc({
            'search': '54321',
            'country_id': self.country.id,
        })
        by_city = self._location_jsonrpc({
            'search': 'Address Location City',
            'country_id': self.country.id,
        })
        self.assertEqual(by_zip['result'][0]['id'], self.location.id)
        self.assertEqual(by_city['result'][0]['city_id'], self.city.id)

    def test_search_is_filtered_by_country(self):
        other_country = self.env.ref('base.fr')
        other_city = self.env['res.city'].create({
            'name': self.city.name,
            'country_id': other_country.id,
        })
        other_location = self.env['res.city.zip'].create({
            'name': self.location.name,
            'city_id': other_city.id,
        })
        response = self._location_jsonrpc({
            'search': self.location.name,
            'country_id': self.country.id,
        })
        result_ids = [item['id'] for item in response['result']]
        self.assertIn(self.location.id, result_ids)
        self.assertNotIn(other_location.id, result_ids)
