###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductStandardPriceHistory(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'type': 'service',
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })

    def test_price_history(self):
        def get_price_history():
            return self.env['product.standard_price.history'].search(
                [('product_id', '=', self.product.id)])

        self.assertEquals(len(get_price_history()), 1)
        self.product.standard_price = 20
        prices = get_price_history()
        self.assertEquals(prices.mapped('standard_price'), [10, 20])
        self.product.standard_price = 11
        prices = get_price_history()
        self.assertEquals(prices.mapped('standard_price'), [10, 20, 11])
        self.product.standard_price = 15
        prices = get_price_history()
        self.assertEquals(prices.mapped('standard_price'), [10, 20, 11, 15])
