###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests import common


class TestStockPickingForbiddenCarrier(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 2,
                    'price_unit': 15,
                }),
            ],
        })
        self.product_shipping_cost = self.env['product.product'].create({
            'type': 'service',
            'name': 'Shipping costs',
            'standard_price': 10,
            'list_price': 20,
        })
        self.carrier_01 = self.env['delivery.carrier'].create({
            'name': 'Carrier test 1',
            'delivery_type': 'fixed',
            'product_id': self.product_shipping_cost.id,
            'fixed_price': 3,
        })
        self.carrier_02 = self.env['delivery.carrier'].create({
            'name': 'Carrier test 2',
            'delivery_type': 'fixed',
            'product_id': self.product_shipping_cost.id,
            'fixed_price': 2,
        })

    def test_stock_picking_no_forbidden_carrier(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertFalse(picking.carrier_id)
        self.assertEqual(len(picking.picking_type_id.forbidden_carriers), 0)
        self.assertTrue(
            self.carrier_01.id not in (
                picking.picking_type_id.forbidden_carriers.ids))
        picking.carrier_id = self.carrier_01.id
        self.assertEqual(picking.carrier_id, self.carrier_01)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()
        self.assertEqual(picking.state, 'done')

    def test_stock_picking_forbidden_carrier_error(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertFalse(picking.carrier_id)
        self.assertEqual(len(picking.picking_type_id.forbidden_carriers), 0)
        picking.picking_type_id.forbidden_carriers = [
            (6, 0, [self.carrier_01.id])
        ]
        self.assertEqual(len(picking.picking_type_id.forbidden_carriers), 1)
        self.assertTrue(
            self.carrier_01.id in (
                picking.picking_type_id.forbidden_carriers.ids))
        picking.carrier_id = self.carrier_01.id
        self.assertEqual(picking.carrier_id, self.carrier_01)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        with self.assertRaises(exceptions.ValidationError) as result:
            picking.button_validate()
        self.assertEqual(
            result.exception.name,
            'The selected carrier is on the list of forbidden carriers for '
            'this picking type.')

    def test_stock_picking_forbidden_carrier_no_error(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertFalse(picking.carrier_id)
        self.assertEqual(len(picking.picking_type_id.forbidden_carriers), 0)
        picking.picking_type_id.forbidden_carriers = [
            (6, 0, [self.carrier_01.id])
        ]
        self.assertEqual(len(picking.picking_type_id.forbidden_carriers), 1)
        self.assertTrue(
            self.carrier_01.id in (
                picking.picking_type_id.forbidden_carriers.ids))
        self.assertTrue(
            self.carrier_02.id not in (
                picking.picking_type_id.forbidden_carriers.ids))
        picking.carrier_id = self.carrier_02.id
        self.assertEqual(picking.carrier_id, self.carrier_02)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()
        self.assertEqual(picking.state, 'done')

    def test_stock_picking_forbidden_same_sale_carrier(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        self.sale.carrier_id = self.carrier_01.id
        self.assertEqual(self.sale.carrier_id, self.carrier_01)
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEqual(picking.carrier_id, self.sale.carrier_id)
        self.assertEqual(len(picking.picking_type_id.forbidden_carriers), 0)
        picking.picking_type_id.forbidden_carriers = [
            (6, 0, [self.carrier_01.id])
        ]
        self.assertEqual(len(picking.picking_type_id.forbidden_carriers), 1)
        self.assertTrue(
            self.carrier_01.id in (
                picking.picking_type_id.forbidden_carriers.ids))
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()
        self.assertEqual(picking.state, 'done')

    def test_stock_picking_forbidden_carrier_change_sale_carrier(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        self.sale.carrier_id = self.carrier_01.id
        self.assertEqual(self.sale.carrier_id, self.carrier_01)
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEqual(picking.carrier_id, self.sale.carrier_id)
        self.assertEqual(len(picking.picking_type_id.forbidden_carriers), 0)
        picking.picking_type_id.forbidden_carriers = [
            (6, 0, [self.carrier_01.id, self.carrier_02.id])
        ]
        self.assertEqual(len(picking.picking_type_id.forbidden_carriers), 2)
        picking.carrier_id = self.carrier_02.id
        self.assertEqual(picking.carrier_id, self.carrier_02)
        self.assertTrue(
            self.carrier_01.id in (
                picking.picking_type_id.forbidden_carriers.ids))
        self.assertTrue(
            self.carrier_02.id in (
                picking.picking_type_id.forbidden_carriers.ids))
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        with self.assertRaises(exceptions.ValidationError) as result:
            picking.button_validate()
        self.assertEqual(
            result.exception.name,
            'The selected carrier is on the list of forbidden carriers for '
            'this picking type.')
