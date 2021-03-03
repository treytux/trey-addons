###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductListPriceFromMargin(TransactionCase):

    def test_list_price(self):
        def compute(standard, margin):
            product = self.env['product.template'].create({
                'name': 'Test Product',
                'standard_price': standard,
                'margin': margin,
                'list_price': 0.,
            })
            product._compute_list_price()
            return product.list_price

        self.assertEquals(compute(0, 0), 0)
        self.assertEquals(compute(100, 0), 100)
        self.assertEquals(compute(100, 25), 133.33)
        self.assertEquals(compute(100, 20), 125)
        self.assertEquals(compute(100, 100), 1000000.0)
        self.assertEquals(compute(100, 200), 1000000.0)
        self.assertEquals(compute(100, -100), 50)

    def test_margin(self):
        def compute(standard, price):
            product = self.env['product.template'].new({
                'name': 'Test Product',
                'standard_price': standard,
                'list_price': price,
            })
            product.onchange_list_price()
            return round(product.margin, 2)

        self.assertEquals(compute(0, 0), 0)
        self.assertEquals(compute(100, 100), 0)
        self.assertEquals(compute(100, 133.33), 25)
        self.assertEquals(compute(100, 125), 20)
        self.assertEquals(compute(100, 1000000.0), 99.99)
        self.assertEquals(compute(100, 50), -100)
        self.assertEquals(compute(100, 0), 0)
        self.assertEquals(compute(100, 1), -9900)

    def test_product_template(self):
        product = self.env['product.template'].new({
            'name': 'Test Product',
            'standard_price': 0,
            'list_price': 11.11,
        })
        self.assertEquals(product.list_price, 11.11)
        product.onchange_list_price()
        self.assertEquals(product.list_price, 11.11)

    def test_product_product(self):
        product = self.env['product.product'].new({
            'name': 'Test Product',
            'standard_price': 0,
            'list_price': 11.11,
        })
        self.assertEquals(product.list_price, 11.11)
        product.onchange_lst_price()
        self.assertEquals(product.list_price, 11.11)
