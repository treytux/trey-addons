###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductTemplateDeliveryCarrier(TransactionCase):

    def setUp(self):
        super().setUp()
        self.categ_id = self.env.ref('delivery.product_category_deliveries')
        self.product_delivery_carrier = self.env['product.product'].create({
            'name': 'Delivery Carrier 2',
            'categ_id': self.categ_id.id,
            'type': 'service',
            'list_price': 0.0,
            'sale_ok': False,
            'purchase_ok': False,
            'invoice_policy': 'order',
        })
        self.carrier_1 = self.env.ref('delivery.free_delivery_carrier')
        self.carrier_2 = self.env['delivery.carrier'].create({
            'name': 'Local Delivery',
            'delivery_type': 'fixed',
            'fixed_price': 10.0,
            'amount': 10.0,
            'product_id': self.product_delivery_carrier.id,
        })
        self.default_carrier = self.env['delivery.carrier'].create({
            'name': 'Default Carrier',
            'delivery_type': 'fixed',
            'fixed_price': 5.0,
            'amount': 5.0,
            'product_id': self.product_delivery_carrier.id,
        })
        self.product_template_1 = self.env['product.template'].create({
            'name': 'Test Product 1',
            'type': 'product',
            'carrier_ids': [(6, 0, [self.carrier_1.id])]
        })
        self.product_template_without_carrier = self.env['product.template'].create({
            'name': 'Test Product Without Carrier',
            'type': 'product',
        })
        self.product_template_2 = self.env['product.template'].create({
            'name': 'Test Product 2',
            'type': 'product',
            'carrier_ids': [(6, 0, [self.carrier_1.id])]
        })
        self.product_template_3 = self.env['product.template'].create({
            'name': 'Test Product 3',
            'type': 'product',
            'carrier_ids': [self.carrier_1.id, self.carrier_2.id]
        })
        self.product_template_4 = self.env['product.template'].create({
            'name': 'Test Product 4',
            'type': 'product',
            'carrier_ids': [self.carrier_1.id, self.carrier_2.id]
        })
        self.product_template_5 = self.env['product.template'].create({
            'name': 'Test Product 5',
            'type': 'product',
            'carrier_ids': [self.carrier_2.id]
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.env.ref('base.res_partner_1').id,
        })

    def test_available_carriers_with_products_same_carrier(self):
        self.sale_order.order_line.create({
            'order_id': self.sale_order.id,
            'product_id': self.product_template_1.product_variant_id.id,
            'product_uom_qty': 1,
        })
        self.sale_order.order_line.create({
            'order_id': self.sale_order.id,
            'product_id': self.product_template_2.product_variant_id.id,
            'product_uom_qty': 1,
        })
        wizard = self.env['choose.delivery.carrier'].with_context(
            active_id=self.sale_order.id,
            active_model='sale.order',
        ).create({
            'order_id': self.sale_order.id,
            'carrier_id': self.default_carrier.id,
        })
        wizard._compute_available_carrier()
        available_carriers = wizard.available_carrier_ids
        self.assertEqual(len(available_carriers), 1)
        self.assertEqual(available_carriers.id, self.carrier_1.id)

    def test_available_carriers_with_one_product_with_different_carrier(self):
        self.sale_order.order_line.create({
            'order_id': self.sale_order.id,
            'product_id': self.product_template_1.product_variant_id.id,
            'product_uom_qty': 1,
        })
        self.sale_order.order_line.create({
            'order_id': self.sale_order.id,
            'product_id': self.product_template_2.product_variant_id.id,
            'product_uom_qty': 1,
        })
        self.sale_order.order_line.create({
            'order_id': self.sale_order.id,
            'product_id': self.product_template_5.product_variant_id.id,
            'product_uom_qty': 1,
        })
        wizard = self.env['choose.delivery.carrier'].with_context(
            active_id=self.sale_order.id,
            active_model='sale.order',
        ).create({
            'order_id': self.sale_order.id,
            'carrier_id': self.default_carrier.id,
        })
        wizard._compute_available_carrier()
        available_carriers = wizard.available_carrier_ids
        self.assertEqual(len(available_carriers), 0)

    def test_available_carriers_with_products_with_multiples_carriers(self):
        self.sale_order.order_line.create({
            'order_id': self.sale_order.id,
            'product_id': self.product_template_3.product_variant_id.id,
            'product_uom_qty': 1,
        })
        self.sale_order.order_line.create({
            'order_id': self.sale_order.id,
            'product_id': self.product_template_4.product_variant_id.id,
            'product_uom_qty': 1,
        })
        wizard = self.env['choose.delivery.carrier'].with_context(
            active_id=self.sale_order.id,
            active_model='sale.order',
        ).create({
            'order_id': self.sale_order.id,
            'carrier_id': self.default_carrier.id,
        })
        wizard._compute_available_carrier()
        available_carriers = wizard.available_carrier_ids
        self.assertEqual(len(available_carriers), 2)
        self.assertIn(self.carrier_1, available_carriers)
        self.assertIn(self.carrier_2, available_carriers)

    def test_available_carriers_with_one_product_with_one_more_carriers(self):
        self.sale_order.order_line.create({
            'order_id': self.sale_order.id,
            'product_id': self.product_template_1.product_variant_id.id,
            'product_uom_qty': 1,
        })
        self.sale_order.order_line.create({
            'order_id': self.sale_order.id,
            'product_id': self.product_template_2.product_variant_id.id,
            'product_uom_qty': 1,
        })
        self.sale_order.order_line.create({
            'order_id': self.sale_order.id,
            'product_id': self.product_template_3.product_variant_id.id,
            'product_uom_qty': 1,
        })
        wizard = self.env['choose.delivery.carrier'].with_context(
            active_id=self.sale_order.id,
            active_model='sale.order',
        ).create({
            'order_id': self.sale_order.id,
            'carrier_id': self.default_carrier.id,
        })
        wizard._compute_available_carrier()
        available_carriers = wizard.available_carrier_ids
        self.assertEqual(len(available_carriers), 1)
        self.assertEqual(available_carriers.id, self.carrier_1.id)

    def test_available_carriers_with_product_without_carrier(self):
        self.sale_order.order_line.create({
            'order_id': self.sale_order.id,
            'product_id': (
                self.product_template_without_carrier.product_variant_id.id),
            'product_uom_qty': 1,
        })
        wizard = self.env['choose.delivery.carrier'].with_context(
            active_id=self.sale_order.id,
            active_model='sale.order',
        ).create({
            'order_id': self.sale_order.id,
            'carrier_id': self.default_carrier.id,
        })
        wizard._compute_available_carrier()
        available_carriers = wizard.available_carrier_ids
        self.assertEqual(len(available_carriers), 0)
        self.assertFalse(available_carriers)

    def test_available_carriers_with_product_without_carrier_and_with_carrier(
            self):
        self.sale_order.order_line.create({
            'order_id': self.sale_order.id,
            'product_id': (
                self.product_template_without_carrier.product_variant_id.id),
            'product_uom_qty': 1,
        })
        self.sale_order.order_line.create({
            'order_id': self.sale_order.id,
            'product_id': self.product_template_1.product_variant_id.id,
            'product_uom_qty': 1,
        })
        wizard = self.env['choose.delivery.carrier'].with_context(
            active_id=self.sale_order.id,
            active_model='sale.order',
        ).create({
            'order_id': self.sale_order.id,
            'carrier_id': self.default_carrier.id,
        })
        wizard._compute_available_carrier()
        available_carriers = wizard.available_carrier_ids
        self.assertEqual(len(available_carriers), 0)
        self.assertFalse(available_carriers)
