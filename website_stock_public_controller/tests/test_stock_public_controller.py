###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import HttpCase


class TestStockPublicController(HttpCase):
    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.location = self.env.ref('stock.stock_location_stock')

    def test_check_product_stock(self):
        url = '/product/stock/available/%s' % self.product.id
        quantity = 100.0
        quant = self.env['stock.quant']
        quant._update_available_quantity(
            self.product, self.location, quantity)
        self.assertEqual(self.product.qty_available, quantity)
        self.product.inventory_availability = 'never'
        response = self.url_open(url)
        data = response.content.decode('utf-8')
        self.assertEqual(data, '{"qty_available": 9999}')
        self.product.inventory_availability = 'always'
        response = self.url_open(url)
        data = response.content.decode('utf-8')
        self.assertEqual(data, '{"qty_available": 100.0}')
        self.product.inventory_availability = 'threshold'
        self.product.available_threshold = 50
        response = self.url_open(url)
        data = response.content.decode('utf-8')
        self.assertEqual(data, '{"qty_available": 9999}')
        self.product.available_threshold = 200
        response = self.url_open(url)
        data = response.content.decode('utf-8')
        self.assertEqual(data, '{"qty_available": 100.0}')
        self.product.inventory_availability = 'custom'
        response = self.url_open(url)
        data = response.content.decode('utf-8')
        self.assertEqual(data, '{"qty_available": 100.0, "custom_message": ""}')

    def test_check_product_error(self):
        url = '/product/stock/available/500000'
        response = self.url_open(url)
        data = response.content.decode('utf-8')
        self.assertEqual(data, '{"Error": "ID not found"}')
        url = '/product/stock/available/TEXT'
        response = self.url_open(url)
        data = response.content.decode('utf-8')
        self.assertEqual(data, '{"Error": "ID must be Integer"}')
