###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestDeliveryPricelistApply(TransactionCase):

    def setUp(self):
        super().setUp()
        self.public_pricelist = self.env.ref('product.list0')
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'property_product_pricelist': self.public_pricelist.id,
        })
        self.product_carrier = self.env['product.product'].create({
            'name': 'Carrier product',
            'type': 'service',
        })
        self.carrier_test = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'delivery_type': 'fixed',
            'product_id': self.product_carrier.id,
            'fixed_price': 4.95,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 80,
            'list_price': 100,
        })
        self.pricelist = self.env['product.pricelist'].create({
            'name': 'Test pricelist',
            'item_ids': [(0, 0, {
                'applied_on': '1_product',
                'compute_price': 'fixed',
                'fixed_price': 1.95,
                'product_tmpl_id': self.product_carrier.product_tmpl_id.id,
            })],
        })

    def create_sale(self, partner, product, qty=1):
        return self.env['sale.order'].create({
            'partner_id': partner.id,
            'pricelist_id': partner.property_product_pricelist.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': product.list_price,
                    'product_uom_qty': qty,
                }),
            ],
        })

    def test_delivery_pricelist_default(self):
        sale = self.create_sale(self.partner, self.product)
        self.assertEqual(sale.pricelist_id, self.public_pricelist)
        sale.carrier_id = self.carrier_test
        sale.get_delivery_price()
        sale.set_delivery_line()
        self.assertEqual(len(sale.order_line), 2)
        delivery_line = sale.order_line.filtered(lambda ln: ln.is_delivery)
        self.assertEqual(len(delivery_line), 1)
        self.assertEqual(delivery_line.price_unit, 4.95)

    def test_delivery_pricelist_test(self):
        self.partner.property_product_pricelist = self.pricelist.id
        sale = self.create_sale(self.partner, self.product)
        self.assertEqual(sale.pricelist_id, self.pricelist)
        sale.carrier_id = self.carrier_test
        sale.get_delivery_price()
        sale.set_delivery_line()
        self.assertEqual(len(sale.order_line), 2)
        delivery_line = sale.order_line.filtered(lambda ln: ln.is_delivery)
        self.assertEqual(len(delivery_line), 1)
        self.assertEqual(delivery_line.price_unit, 1.95)

    def test_delivery_pricelist_force_in_sale(self):
        sale = self.create_sale(self.partner, self.product)
        sale.pricelist_id = self.pricelist.id
        self.assertEqual(sale.pricelist_id, self.pricelist)
        sale.carrier_id = self.carrier_test
        sale.get_delivery_price()
        sale.set_delivery_line()
        self.assertEqual(len(sale.order_line), 2)
        delivery_line = sale.order_line.filtered(lambda ln: ln.is_delivery)
        self.assertEqual(len(delivery_line), 1)
        self.assertEqual(delivery_line.price_unit, 1.95)

    def test_delivery_pricelist_default_with_free_over_zero(self):
        self.carrier_test.free_over = True
        self.carrier_test.amount = 10.0
        sale = self.create_sale(self.partner, self.product)
        self.assertEqual(sale.pricelist_id, self.public_pricelist)
        sale.carrier_id = self.carrier_test
        sale.get_delivery_price()
        sale.set_delivery_line()
        self.assertEqual(len(sale.order_line), 2)
        delivery_line = sale.order_line.filtered(lambda ln: ln.is_delivery)
        self.assertEqual(len(delivery_line), 1)
        self.assertEqual(delivery_line.price_unit, 0)

    def test_delivery_pricelist_default_with_free_over_not_zero(self):
        self.carrier_test.free_over = True
        self.carrier_test.amount = 500.0
        sale = self.create_sale(self.partner, self.product)
        self.assertEqual(sale.pricelist_id, self.public_pricelist)
        sale.carrier_id = self.carrier_test
        sale.get_delivery_price()
        sale.set_delivery_line()
        self.assertEqual(len(sale.order_line), 2)
        delivery_line = sale.order_line.filtered(lambda ln: ln.is_delivery)
        self.assertEqual(len(delivery_line), 1)
        self.assertEqual(delivery_line.price_unit, 4.95)
