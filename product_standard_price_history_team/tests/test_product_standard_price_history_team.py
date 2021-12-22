###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductStandardPriceHistoryTeam(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'type': 'product',
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.delivery_product = self.env['product.product'].create({
            'type': 'service',
            'name': 'Transport cost',
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Test carrier',
            'delivery_type': 'base_on_rule',
            'product_id': self.delivery_product.id,
            'price_rule_ids': [
                (0, 0, {
                    'max_value': 10,
                    'list_base_price': 1,
                }),
                (0, 0, {
                    'max_value': 20,
                    'list_base_price': 2,
                }),
            ],
        })

    def test_commission_market(self):
        team = self.env['crm.team'].create({
            'name': 'Test market',
            'is_market': True,
            'market_commission': 15,
            'market_carrier_id': self.carrier.id,
        })
        sales_before = self.env['sale.order'].search([])
        price = team.price_cost_compute(self.product)
        self.assertEquals(round(price, 2), 12.65)
        self.product.weight = 5
        price = team.price_cost_compute(self.product)
        self.assertEquals(round(price, 2), 12.65)
        self.product.weight = 15
        price = team.price_cost_compute(self.product)
        self.assertEquals(round(price, 2), 13.8)
        sales_after = self.env['sale.order'].search([])
        self.assertEquals(len(sales_before), len(sales_after))

    def test_price_history(self):
        def get_price_history():
            return self.env['product.standard_price.history'].search(
                [('product_id', '=', self.product.id)])

        team_1 = self.env['crm.team'].create({
            'name': 'Test market 1',
            'is_market': True,
            'market_commission': 10,
            'market_carrier_id': self.carrier.id,
        })
        team_2 = self.env['crm.team'].create({
            'name': 'Test market 2',
            'is_market': True,
            'market_commission': 20,
            'market_carrier_id': self.carrier.id,
        })
        self.assertEquals(len(get_price_history()), 1)
        self.product.standard_price = 20
        prices = get_price_history()
        self.assertEquals(len(prices), 4)
        self.assertEquals(
            prices.filtered(lambda p: p.team_id == team_1).market_cost, 23.1)
        self.assertEquals(
            prices.filtered(lambda p: p.team_id == team_2).market_cost, 25.2)
        self.product.standard_price = 10
        self.assertEquals(len(get_price_history()), 7)
        team_2.is_market = False
        self.product.standard_price = 15
        self.assertEquals(len(get_price_history()), 9)

    def test_price_history_without_market(self):
        def get_price_history():
            return self.env['product.standard_price.history'].search(
                [('product_id', '=', self.product.id)])

        self.assertEquals(
            len(self.env['crm.team'].search([('is_market', '=', True)])), 0)
        self.assertEquals(len(get_price_history()), 1)
        self.product.standard_price = 20
        self.assertEquals(
            get_price_history().mapped('standard_price'), [10, 20])
