###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from urllib.parse import urlparse

from odoo.tests import HttpCase, TransactionCase, tagged


class TestNexmartSettings(TransactionCase):

    def test_api_key_is_saved_as_configuration_parameter(self):
        settings = self.env['res.config.settings'].create({
            'nexmart_apikey': 'test-partner-key',
        })
        settings.set_values()
        self.assertEqual(
            self.env['ir.config_parameter'].sudo().get_param(
                'website.nexmart_apikey'), 'test-partner-key')

    def test_product_has_nexmart_display_flag(self):
        product = self.env['product.template'].create({
            'name': 'Nexmart test product',
            'show_nexmart_data': True,
        })
        self.assertTrue(product.show_nexmart_data)


@tagged('post_install', '-at_install')
class TestNexmartProductPage(HttpCase):

    def setUp(self):
        super().setUp()
        netloc = urlparse(self.base_url()).netloc
        website_id = self.env['website']._get_current_website_id(netloc)
        self.website = self.env['website'].browse(website_id)
        self.website.nexmart_apikey = 'test-partner-key'
        self.product = self.env['product.template'].create({
            'name': 'Nexmart product page test',
            'barcode': '8412345678901',
            'show_nexmart_data': True,
            'website_published': True,
            'sale_ok': True,
            'website_id': self.website.id,
        })

    def _product_page(self):
        self.env.cr.flush()
        return self.url_open(self.product.website_url)

    def test_product_page_contains_nexmart_iframe(self):
        response = self._product_page()
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'https://www.nexmart.com/api/dataview/', response.text)
        self.assertIn('gtin=8412345678901', response.text)
        self.assertIn('partnerkey=test-partner-key', response.text)
        self.assertIn(
            'class="js_wsn_nexmart_iframe js_wir_iframe"', response.text)

    def test_product_page_does_not_contain_iframe_when_disabled(self):
        self.product.show_nexmart_data = False
        response = self._product_page()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            'https://www.nexmart.com/api/dataview/', response.text)

    def test_product_page_does_not_contain_iframe_without_barcode(self):
        self.product.barcode = False
        response = self._product_page()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            'https://www.nexmart.com/api/dataview/', response.text)

    def test_product_page_does_not_contain_iframe_without_api_key(self):
        self.website.nexmart_apikey = False
        response = self._product_page()
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            'https://www.nexmart.com/api/dataview/', response.text)
