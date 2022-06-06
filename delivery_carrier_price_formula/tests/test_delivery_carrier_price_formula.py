###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestDeliveryCarrierPriceFormula(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product_1 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test',
            'standard_price': 10,
            'list_price': 100,
            'weight': 20,
        })
        self.product_2 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 2',
            'standard_price': 5,
            'list_price': 10,
            'weight': 14,
        })
        self.delivery_product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service delivery test',
            'standard_price': 10,
            'list_price': 100,
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'delivery_type': 'formula',
            'product_id': self.delivery_product.id,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 1,
                }),
            ],
        })

    def test_delivery_carrier_price_formula(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertEqual(len(self.sale.order_line), 2)
        self.assertFalse(self.sale.carrier_id)
        self.sale.carrier_id = self.carrier.id
        self.assertTrue(self.sale.carrier_id)
        self.assertEqual(self.sale.carrier_id, self.carrier)
        res = self.sale.carrier_id.rate_shipment(self.sale)
        self.assertEqual(res['price'], 5.99)
        self.sale.get_delivery_price()
        self.assertEqual(self.sale.delivery_price, res['price'])

    def test_change_formula_delivery_carrier_price(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        self.sale.carrier_id = self.carrier.id
        self.assertTrue(self.sale.carrier_id)
        self.assertEqual(self.sale.carrier_id, self.carrier)
        res = self.sale.carrier_id.rate_shipment(self.sale)
        self.assertEqual(res['price'], 5.99)
        self.sale.get_delivery_price()
        self.assertEqual(self.sale.delivery_price, res['price'])
        self.sale.order_line[1].unlink()
        self.assertEqual(len(self.sale.order_line), 1)
        res = self.sale.carrier_id.rate_shipment(self.sale)
        self.assertEqual(res['price'], 3.99)
        self.sale.get_delivery_price()
        self.assertEqual(self.sale.delivery_price, res['price'])
