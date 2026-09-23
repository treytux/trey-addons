###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import HttpCase, tagged

PIXEL_PNG = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk'
    '+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')


@tagged('post_install', '-at_install')
class TestWebsiteSaleProductIcon(HttpCase):

    def setUp(self):
        super().setUp()
        self.icons = self.env['product.icon'].create([
            {'name': 'Waterproof', 'image_1920': PIXEL_PNG},
            {'name': 'Eco Friendly', 'image_1920': PIXEL_PNG},
            {'name': 'Made in Spain', 'image_1920': PIXEL_PNG},
        ])
        self.product = self.env['product.template'].create({
            'name': 'Icon Test Product',
            'sale_ok': True,
            'website_published': True,
            'description_sale': 'A great product for testing icons',
        })

    def _get_product_page(self):
        response = self.url_open(self.product.website_url)
        self.assertEqual(response.status_code, 200)
        return response.text

    def test_icons_shown_on_product_page(self):
        self.product.write({
            'icon_ids': [
                (0, 0, {'icon_id': self.icons[0].id, 'sequence': 1}),
                (0, 0, {'icon_id': self.icons[1].id, 'sequence': 2}),
            ],
        })
        body = self._get_product_page()
        self.assertIn('o_wspi_icons', body)
        self.assertIn('o_wspi_icon_image', body)
        self.assertIn('title="Waterproof"', body)
        self.assertIn('title="Eco Friendly"', body)
        self.assertIn('alt="Waterproof"', body)

    def test_block_absent_without_icons(self):
        body = self._get_product_page()
        self.assertNotIn('o_wspi_icons', body)
