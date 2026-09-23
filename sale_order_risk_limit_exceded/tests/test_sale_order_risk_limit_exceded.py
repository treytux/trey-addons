###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleOrderPartnerGroup(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
            'customer': True,
        })
        self.contact = self.env['res.partner'].create({
            'name': 'Test contact',
            'customer': True,
            'type': 'contact',
            'parent_id': self.partner.id,
        })
        self.product = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Consumible product',
            'standard_price': 10,
            'list_price': 100,
        })

    def create_sale(self, partner, price_unit):
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': price_unit,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.onchange_partner_id()
        return sale

    def test_risk_limit_exceded_sale_order_include(self):
        sale_1 = self.create_sale(self.partner, 100)
        self.partner.risk_sale_order_include = True
        self.assertTrue(self.partner.risk_sale_order_include)
        self.assertFalse(sale_1.is_risk_sale_order_limit_exceded)
        sale_1.action_confirm()
        self.assertTrue(sale_1.is_risk_sale_order_limit_exceded)
        self.assertNotEqual(sale_1.state, 'sale')
        self.partner.risk_sale_order_include = False
        self.assertEqual(sale_1.state, 'sale')
        self.assertFalse(sale_1.is_risk_sale_order_limit_exceded)
        self.partner.risk_sale_order_include = True
        sale_2 = self.create_sale(self.contact, 100)
        sale_2.action_confirm()
        self.assertNotEqual(sale_2.state, 'sale')
        self.assertTrue(sale_2.is_risk_sale_order_limit_exceded)
        self.partner.risk_sale_order_include = False
        self.assertEqual(sale_2.state, 'sale')
        self.assertFalse(sale_2.is_risk_sale_order_limit_exceded)

    def test_risk_limit_exceded_credit_limit(self):
        sale_1 = self.create_sale(self.partner, 100)
        self.partner.risk_sale_order_include = True
        self.assertTrue(self.partner.risk_sale_order_include)
        self.assertFalse(sale_1.is_risk_sale_order_limit_exceded)
        sale_1.action_confirm()
        self.assertTrue(sale_1.is_risk_sale_order_limit_exceded)
        self.assertNotEqual(sale_1.state, 'sale')
        self.partner.credit_limit = 50
        self.assertNotEqual(sale_1.state, 'sale')
        self.partner.credit_limit = 200
        self.assertEqual(sale_1.state, 'sale')
        self.assertFalse(sale_1.is_risk_sale_order_limit_exceded)
        sale_2 = self.create_sale(self.contact, 100)
        self.assertTrue(self.partner.risk_sale_order_include)
        self.assertFalse(sale_2.is_risk_sale_order_limit_exceded)
        sale_2.action_confirm()
        self.assertTrue(sale_2.is_risk_sale_order_limit_exceded)
        self.assertNotEqual(sale_2.state, 'sale')
        self.partner.credit_limit = 300
        self.assertEqual(sale_2.state, 'sale')
        self.assertFalse(sale_2.is_risk_sale_order_limit_exceded)

    def test_risk_limit_exceded_sale_order_limit(self):
        sale_1 = self.create_sale(self.partner, 100)
        self.partner.risk_sale_order_limit = 50
        self.assertFalse(sale_1.is_risk_sale_order_limit_exceded)
        sale_1.action_confirm()
        self.assertTrue(sale_1.is_risk_sale_order_limit_exceded)
        self.assertNotEqual(sale_1.state, 'sale')
        self.partner.risk_sale_order_limit = 150
        self.assertEqual(sale_1.state, 'sale')
        self.assertFalse(sale_1.is_risk_sale_order_limit_exceded)
        sale_2 = self.create_sale(self.contact, 100)
        sale_2.action_confirm()
        self.assertNotEqual(sale_2.state, 'sale')
        self.assertTrue(sale_2.is_risk_sale_order_limit_exceded)
        self.partner.risk_sale_order_limit = 250
        self.assertEqual(sale_2.state, 'sale')
        self.assertFalse(sale_2.is_risk_sale_order_limit_exceded)
