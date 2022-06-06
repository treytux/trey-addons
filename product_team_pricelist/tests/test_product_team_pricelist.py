###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductTeamPricelist(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product_01 = self.env['product.template'].create({
            'type': 'product',
            'name': 'Product 01',
        })
        self.team_01 = self.env['crm.team'].create({
            'name': 'Sales Team Test 01',
            'team_type': 'sales',
        })
        self.team_02 = self.env['crm.team'].create({
            'name': 'Sales Team Test 02',
            'team_type': 'sales',
        })

    def test_team_pricelist_one_line_for_product(self):
        self.product_01.update({
            'team_pricelist_ids': [
                (0, 0, {
                    'team_id': self.team_01.id,
                    'sale_price': 500,
                    'standard_price': 150,
                    'shipping_price': 20,
                    'commission': 10,
                }),
            ]
        })
        pricelist_ids = self.product_01.team_pricelist_ids
        self.assertEquals(len(pricelist_ids), 1)
        self.assertEquals(pricelist_ids[0].product_id, self.product_01)
        self.assertEquals(pricelist_ids[0].profit, 280)

    def test_team_pricelist_two_lines_for_product(self):
        self.product_01.update({
            'team_pricelist_ids': [
                (0, 0, {
                    'team_id': self.team_01.id,
                    'sale_price': 500,
                    'standard_price': 150,
                    'shipping_price': 20,
                    'commission': 10,
                }),
                (0, 0, {
                    'team_id': self.team_02.id,
                    'sale_price': 300,
                    'standard_price': 100,
                    'shipping_price': 10,
                    'commission': 20,
                }),
            ]
        })
        pricelist_ids = self.product_01.team_pricelist_ids
        self.assertEquals(len(pricelist_ids), 2)
        self.assertEquals(pricelist_ids[0].product_id, self.product_01)
        self.assertEquals(pricelist_ids[1].product_id, self.product_01)
        self.assertEquals(pricelist_ids[0].profit, 280)
        self.assertEquals(pricelist_ids[1].profit, 130)
        pricelist_ids[0].sale_price = 600
        self.assertEquals(pricelist_ids[0].profit, 370)
