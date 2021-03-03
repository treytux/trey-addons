###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestDeliveryCostToSaleOrder(TransactionCase):
    def test_copy_product(self):
        partner = self.env['res.partner'].create({
            'name': 'Partner supplier test',
            'supplier': True,
        })
        product = self.env['product.template'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
            'seller_ids': [(0, 0, {
                'name': partner.id,
                'price': 10,
                'discount': 15,
            })]
        })
        self.assertTrue(product.seller_ids)
        new_product = product.copy()
        self.assertTrue(new_product.seller_ids)
        self.assertTrue(new_product.seller_ids != product.seller_ids)
