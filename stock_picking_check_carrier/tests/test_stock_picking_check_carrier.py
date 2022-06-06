###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests import common


class TestStockPickingCheckCarrier(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 30,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 10,
                }),
            ],
        })
        self.product_shipping_costs = self.env['product.product'].create({
            'type': 'service',
            'name': 'Shipping costs',
            'standard_price': 10,
            'list_price': 100,
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'delivery_type': 'fixed',
            'product_id': self.product_shipping_costs.id,
            'fixed_price': 3,
        })

    def test_check_stock_picking_without_carrier_01(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertTrue(self.sale.picking_ids)
        self.assertEqual(len(self.sale.picking_ids), 1)
        picking = self.sale.picking_ids[0]
        self.assertFalse(picking.carrier_id)
        self.assertFalse(
            picking.picking_type_id.carrier_required)
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()
        self.assertEqual(picking.state, 'done')

    def test_check_stock_picking_without_carrier_02(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertTrue(self.sale.picking_ids)
        self.assertEqual(len(self.sale.picking_ids), 1)
        picking = self.sale.picking_ids[0]
        self.assertFalse(picking.carrier_id)
        self.assertFalse(
            picking.picking_type_id.carrier_required)
        picking.picking_type_id.carrier_required = True
        self.assertTrue(
            picking.picking_type_id.carrier_required)
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        with self.assertRaises(exceptions.ValidationError) as result:
            picking.button_validate()
        self.assertEqual(
            result.exception.name,
            'Picking must have a carrier assigned to it before '
            'being validated.')

    def test_check_stock_picking_with_carrier_01(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        self.sale.carrier_id = self.carrier.id
        self.assertTrue(self.sale.carrier_id)
        self.assertEqual(self.sale.carrier_id, self.carrier)
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertTrue(self.sale.picking_ids)
        self.assertEqual(len(self.sale.picking_ids), 1)
        picking = self.sale.picking_ids[0]
        self.assertTrue(picking.carrier_id)
        self.assertEqual(picking.carrier_id, self.sale.carrier_id)
        self.assertFalse(
            picking.picking_type_id.carrier_required)
        picking.picking_type_id.carrier_required = True
        self.assertTrue(
            picking.picking_type_id.carrier_required)
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()
        self.assertEqual(picking.state, 'done')

    def test_check_stock_picking_with_carrier_02(self):
        self.assertEqual(self.sale.state, 'draft')
        self.assertFalse(self.sale.carrier_id)
        self.sale.carrier_id = self.carrier.id
        self.assertTrue(self.sale.carrier_id)
        self.assertEqual(self.sale.carrier_id, self.carrier)
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertTrue(self.sale.picking_ids)
        self.assertEqual(len(self.sale.picking_ids), 1)
        picking = self.sale.picking_ids[0]
        self.assertTrue(picking.carrier_id)
        self.assertEqual(self.sale.carrier_id, picking.carrier_id)
        self.assertFalse(
            picking.picking_type_id.carrier_required)
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()
        self.assertEqual(picking.state, 'done')
