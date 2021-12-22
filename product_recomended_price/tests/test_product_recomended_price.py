###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductRecomendedPrice(TransactionCase):

    def test_recomended_price(self):
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
            'recomended_price': 200,
        })
        pricelist = self.env['product.pricelist'].create({
            'name': 'Test pricelist',
            'item_ids': [
                (0, 0, {
                    'applied_on': '1_product',
                    'product_id': product.id,
                    'compute_price': 'formula',
                    'base': 'list_price',
                }),
            ],
        })
        pricelist = pricelist.with_context(
            lang=partner.lang,
            partner=partner,
            quantity=1,
            pricelist=pricelist.id,
        )
        price, rule = pricelist.get_product_price_rule(product, 1.0, partner)
        self.assertEquals(price, 100)
        pricelist.item_ids[0].base = 'recomended_price'
        price, rule = pricelist.get_product_price_rule(product, 1.0, partner)
        self.assertEquals(price, 200)
