###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from time import sleep

from odoo.tests.common import TransactionCase


class TestProductLastInventory(TransactionCase):

    def test_product_last_standard_price(self):
        product = self.env['product.product'].create({
            'company_id': False,
            'name': 'Product',
            'list_price': 100,
            'standard_price': 5,
        })
        pre_date = product.last_standard_price_date
        self.assertTrue(product.last_standard_price_date)
        product.standard_price = 10
        self.assertEquals(product.standard_price, 10)
        self.assertTrue(product.last_standard_price_date)
        sleep(1)
        product.standard_price = 200
        self.assertNotEquals(pre_date, product.last_standard_price_date)
