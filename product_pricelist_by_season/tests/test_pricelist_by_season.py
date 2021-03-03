###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import SavepointCase
from odoo.tools import float_compare


class TestPricelistBySeason(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.season = cls.env['product.season'].create({
            'name': 'Season',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Product',
            'type': 'consu',
            'lst_price': 100.0,
        })
        cls.product_season = cls.env['product.product'].create({
            'name': 'Product With Season',
            'type': 'consu',
            'lst_price': 100.0,
            'season_id': cls.season.id,
        })
        cls.customer_pricelist = cls.env['product.pricelist'].create({
            'name': 'Customer Pricelist',
            'item_ids': [(0, 0, {
                'name': 'Season',
                'applied_on': '3_season',
                'product_season_id': cls.season.id,
                'compute_price': 'formula',
                'price_discount': 50,
                'base': 'list_price',
            }), (0, 0, {
                'name': 'All products',
                'applied_on': '3_global',
                'compute_price': 'formula',
                'price_discount': 0,
                'base': 'list_price',
            })]
        })

    def test_calculation_price_of_products_by_season(self):
        context = {'pricelist': self.customer_pricelist.id, 'quantity': 1}
        self.product = self.product.with_context(context)
        self.product_season = self.product_season.with_context(context)
        self.assertEqual(
            float_compare(
                self.product.price, 100.0, precision_digits=2), 0)
        self.assertEqual(
            float_compare(
                self.product_season.price, 50.0, precision_digits=2), 0)
