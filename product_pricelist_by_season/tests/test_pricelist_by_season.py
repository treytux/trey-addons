###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
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
                'applied_on': '1_season',
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
        cls.uom_unit_id = cls.env.ref('uom.product_uom_unit')

    def test_calculation_price_of_products_by_season(self):
        product_with_pricelist = self.customer_pricelist._compute_price_rule(
            products=self.product,
            qty=1,
            uom=self.uom_unit_id,
            date=fields.Date.today())[self.product.id][0]
        product_season_with_pricelist = self.customer_pricelist._compute_price_rule(
            products=self.product_season,
            qty=1,
            uom=self.uom_unit_id,
            date=fields.Date.today())[self.product_season.id][0]
        self.assertAlmostEqual(product_with_pricelist, 100.0, places=2)
        self.assertEqual(
            float_compare(
                product_season_with_pricelist, 50.0, precision_digits=2), 0)
