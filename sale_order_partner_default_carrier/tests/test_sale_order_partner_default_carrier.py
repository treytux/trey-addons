###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleOrderPartnerDefaultCarrier(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service test product',
            'standard_price': 10,
            'list_price': 30,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        self.product_shipping_cost = self.env['product.product'].create({
            'type': 'service',
            'name': 'Product shipping cost test',
            'standard_price': '10',
            'list_price': '20',
        })
        self.carrier_01 = self.env['delivery.carrier'].create({
            'name': 'Delivery test for partner',
            'delivery_type': 'fixed',
            'product_id': self.product_shipping_cost.id,
            'fixed_price': 4.99,
            'prod_environment': False,
        })
        self.carrier_02 = self.env['delivery.carrier'].create({
            'name': 'Delivery test for partner shipping',
            'delivery_type': 'fixed',
            'product_id': self.product_shipping_cost.id,
            'fixed_price': 4.99,
            'prod_environment': False,
        })

    def test_add_carrier_to_sale_order_from_partner_shipping_id_01(self):
        self.assertFalse(self.sale.carrier_id)
        self.assertFalse(self.partner.default_carrier_id)
        self.partner.default_carrier_id = self.carrier_01.id
        self.assertEqual(self.partner.default_carrier_id, self.carrier_01)
        self.assertEqual(self.sale.partner_id, self.sale.partner_shipping_id)
        self.sale.onchange_partner_shipping_id()
        self.assertEqual(self.sale.carrier_id, self.partner.default_carrier_id)

    def test_add_carrier_to_sale_order_from_partner_shipping_id_02(self):
        self.assertFalse(self.sale.carrier_id)
        self.assertFalse(self.partner.default_carrier_id)
        self.assertEqual(self.sale.partner_id, self.sale.partner_shipping_id)
        self.sale.onchange_partner_shipping_id()
        self.assertFalse(self.sale.carrier_id)

    def test_add_carrier_to_sale_order_from_partner_shipping_id_03(self):
        partner_delivery = self.env['res.partner'].create({
            'name': 'Test shipping partner',
            'parent_id': self.partner.id,
            'type': 'delivery',
        })
        self.sale.onchange_partner_id()
        self.assertFalse(self.sale.carrier_id)
        self.assertFalse(self.partner.default_carrier_id)
        self.assertFalse(partner_delivery.default_carrier_id)
        partner_delivery.default_carrier_id = self.carrier_02.id
        self.assertTrue(partner_delivery.default_carrier_id)
        self.assertEqual(partner_delivery.default_carrier_id, self.carrier_02)
        self.assertNotEqual(
            self.sale.partner_id, self.sale.partner_shipping_id)
        self.sale.onchange_partner_shipping_id()
        self.assertEqual(
            self.sale.carrier_id, partner_delivery.default_carrier_id)
        self.assertEqual(self.sale.carrier_id, self.carrier_02)

    def test_add_carrier_to_sale_order_from_partner_shipping_id_04(self):
        partner_delivery = self.env['res.partner'].create({
            'name': 'Test shipping partner',
            'parent_id': self.partner.id,
            'type': 'delivery',
        })
        self.sale.onchange_partner_id()
        self.assertFalse(self.sale.carrier_id)
        self.assertNotEqual(
            self.sale.partner_id, self.sale.partner_shipping_id)
        self.assertEqual(self.sale.partner_shipping_id, partner_delivery)
        self.assertFalse(self.partner.default_carrier_id)
        self.assertFalse(partner_delivery.default_carrier_id)
        self.partner.default_carrier_id = self.carrier_01.id
        self.assertEqual(self.partner.default_carrier_id, self.carrier_01)
        self.sale.onchange_partner_shipping_id()
        self.assertEqual(self.sale.carrier_id, self.partner.default_carrier_id)

    def test_add_carrier_to_sale_order_from_partner_shipping_id_05(self):
        self.assertFalse(self.sale.carrier_id)
        self.assertEqual(self.sale.partner_id, self.sale.partner_shipping_id)
        self.assertFalse(self.partner.default_carrier_id)
        self.sale.onchange_partner_shipping_id()
        self.assertFalse(self.sale.carrier_id)
        self.partner.default_carrier_id = self.carrier_01.id
        self.assertTrue(self.partner.default_carrier_id)
        self.sale.onchange_partner_shipping_id()
        self.assertEqual(self.sale.carrier_id, self.partner.default_carrier_id)
        self.assertEqual(self.sale.carrier_id, self.carrier_01)
        partner_delivery = self.env['res.partner'].create({
            'name': 'Test shipping partner',
            'parent_id': self.partner.id,
            'type': 'delivery',
        })
        self.assertFalse(partner_delivery.default_carrier_id)
        self.sale.onchange_partner_id()
        self.assertNotEqual(
            self.sale.partner_id, self.sale.partner_shipping_id)
        self.sale.onchange_partner_shipping_id()
        self.assertEqual(self.sale.carrier_id, self.partner.default_carrier_id)
        self.assertEqual(self.sale.carrier_id, self.carrier_01)
        partner_delivery.default_carrier_id = self.carrier_02.id
        self.assertTrue(partner_delivery.default_carrier_id)
        self.sale.onchange_partner_shipping_id()
        self.assertNotEqual(
            self.sale.carrier_id, self.partner.default_carrier_id)
        self.assertEqual(
            self.sale.carrier_id, partner_delivery.default_carrier_id)
        self.assertEqual(self.sale.carrier_id, self.carrier_02)
