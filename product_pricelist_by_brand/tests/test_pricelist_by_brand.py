###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import SavepointCase
from odoo.tools import float_compare


class TestSaleStockOrderSecondaryUnit(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand = cls.env['product.brand'].create({
            'name': 'Product Brand',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Product',
            'type': 'consu',
            'lst_price': 100.0,
        })
        cls.product_brand = cls.env['product.product'].create({
            'name': 'Product With Brand',
            'type': 'consu',
            'lst_price': 100.0,
            'product_brand_id': cls.brand.id,
        })
        cls.customer_pricelist = cls.env['product.pricelist'].create({
            'name': 'Customer Pricelist',
            'item_ids': [(0, 0, {
                'name': 'Brand',
                'applied_on': '3_brand',
                'product_brand_id': cls.brand.id,
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

    def test_calculation_price_of_products_by_brand(self):
        context = {'pricelist': self.customer_pricelist.id, 'quantity': 1}
        self.product = self.product.with_context(context)
        self.product_brand = self.product_brand.with_context(context)
        self.assertEqual(float_compare(
            self.product.price, 100.0, precision_digits=2), 0,
            "Wrong product price. Should be {} instead of {}".format(
                self.product.price, 100))
        self.assertEqual(float_compare(
            self.product_brand.price, 50.0, precision_digits=2), 0,
            "Wrong product brand price. Should be {} instead of {}".format(
                self.product_brand.price, 50.0))
