###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestDeliveryCarrierFilterBySaleAmount(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        product_shipping_cost = self.env['product.product'].create({
            'type': 'service',
            'name': 'Shipping costs',
            'standard_price': 10,
            'list_price': 100,
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Delivery carrier test',
            'delivery_type': 'fixed',
            'product_id': product_shipping_cost.id,
            'not_available_from': False,
        })

    def test_filter_no_active_delivery_carrier(self):
        self.assertFalse(self.carrier.not_available_from)
        self.assertEqual(self.carrier.limit_amount, 0)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2,
                }),
            ],
        })
        self.assertFalse(sale.carrier_id)
        self.assertIn(self.carrier.id, sale.available_carrier_ids.ids)

    def test_filter_carrier_active_exceeding_sale_amount_total(self):
        self.assertFalse(self.carrier.not_available_from)
        self.assertEqual(self.carrier.limit_amount, 0)
        self.carrier.write({
            'not_available_from': True,
            'limit_amount': 300,
        })
        self.assertTrue(self.carrier.not_available_from)
        self.assertEqual(self.carrier.limit_amount, 300)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2,
                }),
            ],
        })
        self.assertFalse(sale.carrier_id)
        self.assertNotIn(self.carrier.id, sale.available_carrier_ids.ids)

    def test_filter_carrier_active_without_exceeding_sale_amount_total(self):
        self.assertFalse(self.carrier.not_available_from)
        self.assertEqual(self.carrier.limit_amount, 0)
        self.carrier.write({
            'not_available_from': True,
            'limit_amount': 400,
        })
        self.assertTrue(self.carrier.not_available_from)
        self.assertEqual(self.carrier.limit_amount, 400)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2,
                }),
            ],
        })
        self.assertFalse(sale.carrier_id)
        self.assertIn(self.carrier.id, sale.available_carrier_ids.ids)

    def test_filter_add_new_product_and_update_amount_total(self):
        self.assertFalse(self.carrier.not_available_from)
        self.assertEqual(self.carrier.limit_amount, 0)
        self.carrier.write({
            'not_available_from': True,
            'limit_amount': 400,
        })
        self.assertTrue(self.carrier.not_available_from)
        self.assertTrue(self.carrier.limit_amount, 400)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2,
                }),
            ],
        })
        self.assertFalse(sale.carrier_id)
        self.assertIn(self.carrier.id, sale.available_carrier_ids.ids)
        sale.write({
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 80,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.assertIn(self.carrier.id, sale.available_carrier_ids.ids)
        sale._compute_available_carrier()
        self.assertNotIn(self.carrier.id, sale.available_carrier_ids.ids)
