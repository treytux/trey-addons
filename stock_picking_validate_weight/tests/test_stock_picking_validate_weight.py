###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestStockPickingValidateWeight(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
            'weight': 10,
        })
        self.location = self.env.ref('stock.stock_location_stock')
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.location, 100)
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 20,
            })],
        })

    def test_wizard_01(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEqual(picking.weight, 200)
        self.assertEqual(picking.state, 'assigned')
        self.assertEqual(len(picking.move_ids), 1)
        wizard = self.env[
            'stock.immediate.transfer'
        ].with_context(
            button_validate_picking_ids=picking.ids
        ).create({
            'pick_ids': [(6, 0, picking.ids)],
            'immediate_transfer_line_ids': [(0, 0, {
                'picking_id': picking.id,
                'to_immediate': True,
            })],
        })
        self.assertEqual(wizard.weight, 200)
        wizard.weight = 10
        wizard.process()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(picking.shipping_weight, 10)
        self.assertEqual(
            picking.shipping_weight, picking.shipping_weight_validate)

    def test_wizard_02(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEqual(picking.weight, 200)
        self.assertEqual(picking.state, 'assigned')
        self.assertEqual(len(picking.move_ids), 1)
        picking.move_ids[0].quantity_done = 10
        self.assertEqual(picking.move_ids[0].quantity_done, 10)
        wizard = self.env[
            'stock.backorder.confirmation'
        ].with_context(
            button_validate_picking_ids=picking.ids
        ).create({
            'pick_ids': [(6, 0, picking.ids)],
            'backorder_confirmation_line_ids': [(0, 0, {
                'picking_id': picking.id,
                'to_backorder': True,
            })],
        })
        self.assertEqual(wizard.weight, 100)
        wizard.weight = 15
        self.assertEqual(wizard.weight, 15)
        wizard.process()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(picking.shipping_weight, 15)
        self.assertEqual(len(self.sale.picking_ids), 2)
        self.assertEqual(self.sale.picking_ids[1].weight, 100)
        self.assertEqual(
            picking.shipping_weight, picking.shipping_weight_validate)

    def test_wizard_03(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEqual(picking.weight, 200)
        self.assertEqual(picking.state, 'assigned')
        self.assertEqual(len(picking.move_ids), 1)
        picking.move_ids[0].quantity_done = 10
        self.assertEqual(picking.move_ids[0].quantity_done, 10)
        wizard = self.env[
            'stock.backorder.confirmation'
        ].with_context(
            button_validate_picking_ids=picking.ids
        ).create({
            'pick_ids': [(6, 0, picking.ids)],
            'backorder_confirmation_line_ids': [(0, 0, {
                'picking_id': picking.id,
                'to_backorder': True,
            })],
        })
        self.assertEqual(wizard.weight, 100)
        wizard.weight = 15
        self.assertEqual(wizard.weight, 15)
        wizard.process_cancel_backorder()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(picking.shipping_weight, 15)
        self.assertEqual(
            picking.shipping_weight, picking.shipping_weight_validate)

    def test_wizard_04(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEqual(picking.weight, 200)
        self.assertFalse(picking.carrier_id)
        free_delivery = self.env.ref('delivery.free_delivery_carrier')
        picking.carrier_id = free_delivery.id
        self.assertEqual(picking.carrier_id, free_delivery)
        wizard = self.env[
            'stock.immediate.transfer'
        ].with_context(
            button_validate_picking_ids=picking.ids
        ).create({
            'pick_ids': [(6, 0, picking.ids)],
            'immediate_transfer_line_ids': [(0, 0, {
                'picking_id': picking.id,
                'to_immediate': True,
            })],
        })
        self.assertEqual(wizard.weight, 200)
        wizard.weight = 10
        wizard.process()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(picking.shipping_weight, 10)
        self.assertEqual(
            picking.shipping_weight, picking.shipping_weight_validate)

    def test_wizard_05(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEqual(picking.weight, 200)
        self.assertFalse(picking.carrier_id)
        free_delivery = self.env.ref('delivery.free_delivery_carrier')
        picking.carrier_id = free_delivery.id
        self.assertEqual(picking.carrier_id, free_delivery)
        self.assertEqual(picking.state, 'assigned')
        self.assertEqual(len(picking.move_ids), 1)
        picking.move_ids[0].quantity_done = 10
        self.assertEqual(picking.move_ids[0].quantity_done, 10)
        wizard = self.env[
            'stock.backorder.confirmation'
        ].with_context(
            button_validate_picking_ids=picking.ids
        ).create({
            'pick_ids': [(6, 0, picking.ids)],
            'backorder_confirmation_line_ids': [(0, 0, {
                'picking_id': picking.id,
                'to_backorder': True,
            })],
        })
        self.assertEqual(wizard.weight, 100)
        wizard.weight = 15
        self.assertEqual(wizard.weight, 15)
        wizard.process()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(picking.shipping_weight, 15)
        self.assertEqual(len(self.sale.picking_ids), 2)
        self.assertEqual(self.sale.picking_ids[1].weight, 100)
        self.assertEqual(
            picking.shipping_weight, picking.shipping_weight_validate)
