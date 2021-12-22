###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests import common


class TestDeliveryCheapest(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test',
            'standard_price': 10,
            'list_price': 100,
        })
        self.product_delivery = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service delivery test',
            'standard_price': 10,
            'list_price': 100,
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'delivery_type': 'fixed',
            'product_id': self.product_delivery.id,
            'fixed_price': 99.99,
            'include_cheapest_carrier': True,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 20,
                }),
            ],
        })
        self.free_delivery = self.env.ref('delivery.free_delivery_carrier')
        self.normal_delivery = self.env.ref('delivery.normal_delivery_carrier')
        self.carrier_02 = self.env.ref('delivery.delivery_carrier')

    def test_get_delivery_cheapest_sale_order_unique_option(self):
        self.assertTrue(self.carrier.include_cheapest_carrier)
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 1)
        self.assertEqual(self.carrier.name, carriers[0].name)
        self.sale.assign_cheapest_delivery_carrier()
        self.assertTrue(self.sale.carrier_id)
        self.assertEqual(self.sale.carrier_id.id, self.carrier.id)
        res = self.sale.carrier_id.rate_shipment(self.sale)
        self.assertEqual(self.sale.delivery_price, res['price'])
        self.assertFalse(res['error_message'])
        self.assertFalse(res['warning_message'])

    def test_get_cheapest_delivery_sale_order_multiple_option(self):
        self.assertTrue(self.carrier.include_cheapest_carrier)
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 1)
        self.assertEqual(self.carrier.name, carriers[0].name)
        self.normal_delivery.include_cheapest_carrier = True
        self.carrier_02.include_cheapest_carrier = True
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.assertTrue(self.normal_delivery.include_cheapest_carrier)
        self.assertTrue(self.carrier_02.include_cheapest_carrier)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 3)
        self.sale.assign_cheapest_delivery_carrier()
        self.assertTrue(self.sale.carrier_id)
        prices = []
        available_carriers = carriers.available_carriers(
            self.sale.partner_shipping_id) if (
                self.sale.partner_shipping_id) else carriers
        for carrier in available_carriers:
            res = carrier.rate_shipment(self.sale)
            prices += [res['price']]
        cheapest_carrier_id = available_carriers[prices.index(min(prices))].id
        self.assertEqual(self.sale.carrier_id.id, cheapest_carrier_id)
        res = self.sale.carrier_id.rate_shipment(self.sale)
        self.assertEqual(self.sale.delivery_price, res['price'])
        self.assertFalse(res['error_message'])
        self.assertFalse(res['warning_message'])

    def test_check_delivery_carrier_filter_by_sale_amount_01(self):
        self.assertFalse(self.carrier.not_available_from)
        self.assertFalse(self.carrier.limit_amount)
        self.assertTrue(self.carrier.include_cheapest_carrier)
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 1)
        self.assertEqual(self.carrier.name, carriers[0].name)
        self.normal_delivery.include_cheapest_carrier = True
        self.carrier_02.include_cheapest_carrier = True
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.assertTrue(self.normal_delivery.include_cheapest_carrier)
        self.assertTrue(self.carrier_02.include_cheapest_carrier)
        self.carrier.write({
            'not_available_from': True,
            'limit_amount': self.sale.amount_total - 200,
        })
        self.assertTrue(self.carrier.not_available_from)
        self.assertEqual(
            self.carrier.limit_amount, self.sale.amount_total - 200)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 3)
        carriers = self.env['delivery.carrier'].search(
            self.sale._get_sale_available_delivery_carrier_domain())
        self.assertEqual(len(carriers), 2)

    def test_check_delivery_carrier_filter_by_sale_amount_02(self):
        self.assertFalse(self.carrier.not_available_from)
        self.assertFalse(self.carrier.limit_amount)
        self.assertTrue(self.carrier.include_cheapest_carrier)
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 1)
        self.assertEqual(self.carrier.name, carriers[0].name)
        self.normal_delivery.include_cheapest_carrier = True
        self.carrier_02.include_cheapest_carrier = True
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.assertTrue(self.normal_delivery.include_cheapest_carrier)
        self.assertTrue(self.carrier_02.include_cheapest_carrier)
        self.carrier.write({
            'not_available_from': True,
            'limit_amount': self.sale.amount_total,
        })
        self.assertTrue(self.carrier.not_available_from)
        self.assertEqual(self.sale.amount_total, self.carrier.limit_amount)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 3)
        carriers = self.env['delivery.carrier'].search(
            self.sale._get_sale_available_delivery_carrier_domain())
        self.assertEqual(len(carriers), 3)

    def test_check_delivery_carrier_filter_by_sale_amount_03(self):
        self.assertFalse(self.carrier.not_available_from)
        self.assertFalse(self.carrier.limit_amount)
        self.assertTrue(self.carrier.include_cheapest_carrier)
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 1)
        self.assertEqual(self.carrier.name, carriers[0].name)
        self.normal_delivery.include_cheapest_carrier = True
        self.carrier_02.include_cheapest_carrier = True
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.assertTrue(self.normal_delivery.include_cheapest_carrier)
        self.assertTrue(self.carrier_02.include_cheapest_carrier)
        self.carrier.write({
            'not_available_from': True,
            'limit_amount': self.sale.amount_total + 200,
        })
        self.assertTrue(self.carrier.not_available_from)
        self.assertEqual(
            self.sale.amount_total + 200, self.carrier.limit_amount)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 3)
        carriers = self.env['delivery.carrier'].search(
            self.sale._get_sale_available_delivery_carrier_domain())
        self.assertEqual(len(carriers), 3)

    def test_no_carriers_found(self):
        self.assertFalse(self.carrier.not_available_from)
        self.assertFalse(self.carrier.limit_amount)
        self.carrier.include_cheapest_carrier = False
        self.assertFalse(self.carrier.include_cheapest_carrier)
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 0)
        self.normal_delivery.include_cheapest_carrier = False
        self.carrier_02.include_cheapest_carrier = False
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.assertFalse(self.normal_delivery.include_cheapest_carrier)
        self.assertFalse(self.carrier_02.include_cheapest_carrier)
        self.carrier.write({
            'not_available_from': True,
            'limit_amount': self.sale.amount_total + 200,
        })
        carriers = self.env['delivery.carrier'].search(
            self.sale._get_sale_available_delivery_carrier_domain())
        self.assertEqual(len(carriers), 0)

    def test_get_cheapest_delivery_sale_order_change_price(self):
        self.assertTrue(self.carrier.include_cheapest_carrier)
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 1)
        self.assertEqual(self.carrier.name, carriers[0].name)
        self.normal_delivery.include_cheapest_carrier = True
        self.carrier_02.include_cheapest_carrier = True
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.assertTrue(self.normal_delivery.include_cheapest_carrier)
        self.assertTrue(self.carrier_02.include_cheapest_carrier)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 3)
        self.sale.assign_cheapest_delivery_carrier()
        self.assertTrue(self.sale.carrier_id)
        prices = []
        available_carriers = carriers.available_carriers(
            self.sale.partner_shipping_id) if (
                self.sale.partner_shipping_id) else carriers
        for carrier in available_carriers:
            res = carrier.rate_shipment(self.sale)
            prices += [res['price']]
        cheapest_carrier_1 = available_carriers[prices.index(min(prices))].id
        self.assertEqual(self.sale.carrier_id.id, cheapest_carrier_1)
        self.sale.get_delivery_price()
        res = self.sale.carrier_id.rate_shipment(self.sale)
        price_1 = res['price']
        self.assertEqual(self.sale.delivery_price, res['price'])
        self.assertFalse(res['error_message'])
        self.assertFalse(res['warning_message'])
        self.carrier.fixed_price = 5
        self.assertEqual(self.carrier.fixed_price, 5)
        self.sale.assign_cheapest_delivery_carrier()
        prices = []
        available_carriers = carriers.available_carriers(
            self.sale.partner_shipping_id) if (
                self.sale.partner_shipping_id) else carriers
        for carrier in available_carriers:
            res = carrier.rate_shipment(self.sale)
            prices += [res['price']]
        cheapest_carrier_2 = available_carriers[prices.index(min(prices))].id
        self.assertEqual(self.sale.carrier_id.id, cheapest_carrier_2)
        self.assertNotEqual(cheapest_carrier_1, cheapest_carrier_2)
        self.sale.get_delivery_price()
        res = self.sale.carrier_id.rate_shipment(self.sale)
        self.assertTrue(price_1 > res['price'])
        self.assertEqual(self.sale.delivery_price, res['price'])
        self.assertFalse(res['error_message'])
        self.assertFalse(res['warning_message'])

    def test_get_cheapest_delivery_sale_order_error_no_option(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertTrue(self.carrier.include_cheapest_carrier)
        self.assertFalse(self.sale.carrier_id)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 1)
        self.assertEqual(self.carrier.name, carriers[0].name)
        self.carrier.include_cheapest_carrier = False
        self.assertFalse(self.carrier.include_cheapest_carrier)
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.assertFalse(self.normal_delivery.include_cheapest_carrier)
        self.assertFalse(self.carrier_02.include_cheapest_carrier)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 0)
        with self.assertRaises(exceptions.ValidationError) as result:
            self.sale.assign_cheapest_delivery_carrier()
        self.assertEqual(
            result.exception.name,
            'No shipping methods found with the check for calculating the '
            'most economical shipping method activated.')

    def test_get_cheapest_delivery_stock_picking_unique_option(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertTrue(self.carrier.include_cheapest_carrier)
        self.assertFalse(self.sale.carrier_id)
        self.sale.assign_cheapest_delivery_carrier()
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertTrue(picking.carrier_id)
        picking.assign_cheapest_delivery_carrier()
        self.assertTrue(picking.carrier_id)
        self.assertEqual(picking.carrier_id, self.sale.carrier_id)

    def test_get_cheapest_delivery_stock_picking_multiple_option(self):
        self.assertTrue(self.carrier.include_cheapest_carrier)
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 1)
        self.assertEqual(self.carrier.name, carriers[0].name)
        self.sale.assign_cheapest_delivery_carrier()
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertTrue(picking.carrier_id)
        self.normal_delivery.include_cheapest_carrier = True
        self.carrier_02.include_cheapest_carrier = True
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.assertTrue(self.normal_delivery.include_cheapest_carrier)
        self.assertTrue(self.carrier_02.include_cheapest_carrier)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 3)
        picking.assign_cheapest_delivery_carrier()
        prices = []
        available_carriers = carriers.available_carriers(
            picking.sale_id.partner_shipping_id) if (
                picking.sale_id.partner_shipping_id) else carriers
        for carrier in available_carriers:
            res = carrier.rate_shipment(picking.sale_id)
            prices += [res['price']]
        cheapest_carrier_id = available_carriers[prices.index(min(prices))].id
        self.assertEqual(picking.carrier_id.id, cheapest_carrier_id)

    def test_get_cheapest_delivery_stock_picking_change_price(self):
        self.assertTrue(self.carrier.include_cheapest_carrier)
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 1)
        self.assertEqual(self.carrier.name, carriers[0].name)
        self.sale.assign_cheapest_delivery_carrier()
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertTrue(picking.carrier_id)
        self.normal_delivery.include_cheapest_carrier = True
        self.carrier_02.include_cheapest_carrier = True
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.assertTrue(self.normal_delivery.include_cheapest_carrier)
        self.assertTrue(self.carrier_02.include_cheapest_carrier)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 3)
        picking.assign_cheapest_delivery_carrier()
        prices = []
        available_carriers = carriers.available_carriers(
            picking.sale_id.partner_shipping_id) if (
                picking.sale_id.partner_shipping_id) else carriers
        for carrier in available_carriers:
            res = carrier.rate_shipment(picking.sale_id)
            prices += [res['price']]
        cheapest_carrier_1 = available_carriers[prices.index(min(prices))].id
        self.assertEqual(picking.carrier_id.id, cheapest_carrier_1)
        self.carrier.fixed_price = 5
        self.assertEqual(self.carrier.fixed_price, 5)
        picking.assign_cheapest_delivery_carrier()
        prices = []
        available_carriers = carriers.available_carriers(
            picking.sale_id.partner_shipping_id) if (
                picking.sale_id.partner_shipping_id) else carriers
        for carrier in available_carriers:
            res = carrier.rate_shipment(picking.sale_id)
            prices += [res['price']]
        cheapest_carrier_2 = available_carriers[prices.index(min(prices))].id
        self.assertEqual(picking.carrier_id.id, cheapest_carrier_2)
        self.assertNotEqual(cheapest_carrier_1, cheapest_carrier_2)

    def test_get_cheapest_delivery_stock_picking_error_no_option(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertTrue(self.carrier.include_cheapest_carrier)
        self.assertFalse(self.sale.carrier_id)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 1)
        self.assertEqual(self.carrier.name, carriers[0].name)
        self.carrier.include_cheapest_carrier = False
        self.assertFalse(self.carrier.include_cheapest_carrier)
        self.assertFalse(self.free_delivery.include_cheapest_carrier)
        self.assertFalse(self.normal_delivery.include_cheapest_carrier)
        self.assertFalse(self.carrier_02.include_cheapest_carrier)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 0)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertFalse(picking.carrier_id)
        with self.assertRaises(exceptions.ValidationError) as result:
            picking.assign_cheapest_delivery_carrier()
        self.assertEqual(
            result.exception.name,
            'No shipping methods found with the check for calculating the '
            'most economical shipping method activated.')

    def test_carrier_id_false_sale_order(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertTrue(self.carrier.include_cheapest_carrier)
        self.assertFalse(self.sale.carrier_id)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 1)
        self.assertEqual(self.carrier.name, carriers[0].name)
        self.sale.carrier_id = False
        self.assertFalse(self.sale.carrier_id)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertFalse(picking.carrier_id)
        picking.assign_cheapest_delivery_carrier()
        self.assertTrue(picking.carrier_id)

    def test_carrier_no_include_delivery_line_not_delivery_cost_to_so_1(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertTrue(self.carrier.include_cheapest_carrier)
        self.assertFalse(self.sale.carrier_id)
        carriers = self.env['delivery.carrier'].search([
            ('include_cheapest_carrier', '=', True),
        ])
        self.assertEqual(len(carriers), 1)
        self.assertEqual(self.carrier.name, carriers[0].name)
        self.env['sale.order.line'].create({
            'name': 'Delivery line',
            'product_id': self.product_delivery.id,
            'product_uom_qty': 1,
            'price_unit': self.product_delivery.list_price,
            'order_id': self.sale.id,
        })
        self.assertFalse(self.sale.delivery_cost_to_sale_order)
        self.sale.assign_cheapest_delivery_carrier()
        self.assertTrue(self.sale.carrier_id)
        self.assertTrue(self.sale.delivery_price > 0)
        self.assertEqual(len(self.sale.order_line), 2)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertTrue(picking.carrier_id)
        picking.assign_cheapest_delivery_carrier()
        self.assertEqual(picking.carrier_id, self.sale.carrier_id)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(len(self.sale.order_line), 2)

    def test_carrier_no_include_delivery_line_not_delivery_cost_to_so_2(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.delivery_cost_to_sale_order)
        self.sale.assign_cheapest_delivery_carrier()
        self.assertTrue(self.sale.carrier_id)
        self.assertTrue(self.sale.delivery_price > 0)
        self.assertEqual(len(self.sale.order_line), 1)
        self.sale.set_delivery_line()
        self.assertEqual(len(self.sale.order_line), 2)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertTrue(picking.carrier_id)
        picking.assign_cheapest_delivery_carrier()
        self.assertEqual(picking.carrier_id, self.sale.carrier_id)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(len(self.sale.order_line), 2)

    def test_include_delivery_line_true_delivery_cost_to_sale_order(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.delivery_cost_to_sale_order)
        self.sale.delivery_cost_to_sale_order = True
        self.assertTrue(self.sale.delivery_cost_to_sale_order)
        self.sale.assign_cheapest_delivery_carrier()
        self.assertTrue(self.sale.carrier_id)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertTrue(picking.sale_id.delivery_cost_to_sale_order)
        self.assertTrue(picking.carrier_id)
        picking.assign_cheapest_delivery_carrier()
        self.assertEqual(picking.carrier_id, self.sale.carrier_id)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(len(self.sale.order_line), 2)

    def test_check_delivery_price_same_carrier_price_after_confirm_so(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        self.sale.assign_cheapest_delivery_carrier()
        self.assertTrue(self.sale.carrier_id)
        self.assertTrue(self.sale.delivery_price)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertTrue(picking.carrier_id)
        self.assertEqual(self.sale.carrier_id, picking.carrier_id)
        self.assertEqual(self.sale.delivery_price, picking.carrier_price)
        picking.assign_cheapest_delivery_carrier()
        self.assertTrue(picking.carrier_id)
        self.assertEqual(self.sale.carrier_id, picking.carrier_id)
        self.assertEqual(self.sale.delivery_price, picking.carrier_price)
