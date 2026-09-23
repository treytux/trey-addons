###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductLastInventory(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'company_id': False,
            'name': 'Product',
            'list_price': 100,
            'standard_price': 5,
        })

    def test_product_last_standard_price(self):
        self.assertTrue(self.product.last_standard_price_date)
        valuation_layer = self.env['stock.valuation.layer'].create({
            'company_id': self.env.company.id,
            'product_id': self.product.id,
            'quantity': 1,
            'unit_cost': 10,
            'value': 10,
            'remaining_qty': 1,
            'remaining_value': 10,
        })
        self.product.standard_price = 10
        self.assertEqual(self.product.standard_price, 10)
        expected_date = valuation_layer.create_date
        self.assertEqual(self.product.last_standard_price_date, expected_date)
        last_valuation_layer = self.env['stock.valuation.layer'].create({
            'company_id': self.env.company.id,
            'product_id': self.product.id,
            'quantity': 1,
            'unit_cost': 200,
            'value': 200,
            'remaining_qty': 1,
            'remaining_value': 200,
        })
        self.product.standard_price = 200
        expected_date = last_valuation_layer.create_date
        self.assertEqual(self.product.last_standard_price_date, expected_date)

    def test_product_last_standard_price_without_valuation_layer(self):
        self.assertEqual(
            self.product.last_standard_price_date, self.product.create_date)
