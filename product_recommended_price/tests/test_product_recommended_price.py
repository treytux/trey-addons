###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductRecommendedPrice(TransactionCase):

    def test_recommended_price(self):
        product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
            'recommended_price': 200,
        })
        pricelist = self.env['product.pricelist'].create({
            'name': 'Test pricelist',
            'item_ids': [
                (0, 0, {
                    'applied_on': '1_product',
                    'product_tmpl_id': product.product_tmpl_id.id,
                    'compute_price': 'formula',
                    'base': 'list_price',
                }),
            ],
        })
        price = pricelist._get_product_price(product, 1.0)
        self.assertEqual(price, 100)
        pricelist.item_ids[0].base = 'recommended_price'
        price = pricelist._get_product_price(product, 1.0)
        self.assertEqual(price, 200)
