###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import SavepointCase
from odoo.tools import float_compare


class TestPricelistFormulaMargin(SavepointCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'name': 'Product',
            'type': 'consu',
            'lst_price': 200.0,
            'standard_price': 100.0,
        })
        self.customer_pricelist = self.env['product.pricelist'].create({
            'name': 'Customer Pricelist',
            'item_ids': [
                (0, 0, {
                    'name': 'Global',
                    'applied_on': '3_global',
                    'compute_price': 'margin',
                    'percent_margin': 20,
                    'base': 'list_price',
                }),
            ]
        })

    def test_compute_margin(self):
        context = {'pricelist': self.customer_pricelist.id, 'quantity': 1}
        product = self.product.with_context(context)
        self.assertEqual(product.price, 125)
        self.assertEqual(
            float_compare(product.price, 125, precision_digits=2), 0)
        item = self.customer_pricelist.item_ids[0]
        item.write({
            'compute_price': 'formula',
            'price_discount': 50,
        })
        self.assertEqual(
            float_compare(product.price, 100.0, precision_digits=2), 0)
