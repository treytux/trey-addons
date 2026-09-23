###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import Form, TransactionCase


class TestPurchaseOrderRecreatePicking(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner_18 = self.env.ref('base.res_partner_18')
        self.product_4 = self.env.ref('product.product_product_4')
        self.product_5 = self.env.ref('product.product_product_5')

    def create_purchase(self, qty):
        return self.env['purchase.order'].create({
            'partner_id': self.partner_18.id,
            'order_line': [(0, 0, {
                'name': self.product_4.name,
                'product_id': self.product_4.id,
                'product_qty': qty,
                'product_uom': self.product_4.uom_id.id,
                'price_unit': 750.00,
                'date_planned': fields.Date.today(),
            })],
        })

    def validate_picking(self, picking):
        action = picking.button_validate()
        if isinstance(action, dict):
            wizard = Form(
                self.env[action['res_model']].with_context(action['context'])
            ).save()
            wizard.process()
        return picking

    def create_return_picking(self, picking):
        return_picking = Form(
            self.env['stock.return.picking'].with_context(
                active_ids=picking.ids,
                active_id=picking.id,
                active_model='stock.picking',
            )
        ).save()
        return_picking._onchange_picking_id()
        return return_picking

    def test_return_partial_and_recreate_picking(self):
        purchase_order = self.create_purchase(5)
        purchase_order.button_confirm()
        self.assertTrue(purchase_order.picking_ids)
        picking = purchase_order.picking_ids
        picking.move_ids.quantity_done = 5
        self.validate_picking(picking)
        qty_delivery_lines = purchase_order.mapped('order_line').filtered(
            lambda ln: ln.qty_received != ln.product_uom_qty)
        self.assertFalse(qty_delivery_lines)
        picking_wizard = self.create_return_picking(picking)
        picking_wizard.product_return_moves.quantity = 3.0
        picking_wizard.product_return_moves.to_refund = True
        picking_return_action = picking_wizard.create_returns()
        picking_return = self.env['stock.picking'].browse(
            picking_return_action['res_id'])
        picking_return.move_ids.quantity_done = 3.0
        self.validate_picking(picking_return)
        self.assertEqual(purchase_order.state, 'purchase')
        self.assertIsNone(purchase_order.action_recreate_picking())
        self.assertEqual(len(purchase_order.picking_ids), 3)
        last_picking = self.env['stock.picking'].search([
            ('purchase_id', '=', purchase_order.id),
        ], order='id desc', limit=1)
        self.assertEqual(last_picking.move_ids[0].product_uom_qty, 3)
        self.assertTrue(last_picking.partner_id)
        last_picking.move_ids.quantity_done = 3
        self.validate_picking(last_picking)
        self.assertEqual(last_picking.state, 'done')

    def test_return_more_qty_and_recreate_picking(self):
        purchase_order = self.create_purchase(5)
        purchase_order.button_confirm()
        self.assertTrue(purchase_order.picking_ids)
        picking = purchase_order.picking_ids
        picking.move_ids.quantity_done = 5
        self.validate_picking(picking)
        qty_delivery_lines = purchase_order.mapped('order_line').filtered(
            lambda ln: ln.qty_received != ln.product_uom_qty)
        self.assertFalse(qty_delivery_lines)
        picking_wizard = self.create_return_picking(picking)
        picking_wizard.product_return_moves.quantity = 6.0
        picking_wizard.product_return_moves.to_refund = True
        picking_return_action = picking_wizard.create_returns()
        picking_return = self.env['stock.picking'].browse(
            picking_return_action['res_id'])
        picking_return.move_ids.quantity_done = 6.0
        self.validate_picking(picking_return)
        self.assertEqual(purchase_order.state, 'purchase')
        with self.assertRaises(UserError):
            purchase_order.action_recreate_picking()
        self.assertEqual(len(purchase_order.picking_ids), 2)

    def test_partial_in_cancel_and_recreate_picking_several_lines(self):
        purchase_order = self.create_purchase(5)
        self.env['purchase.order.line'].create({
            'order_id': purchase_order.id,
            'name': self.product_5.name,
            'product_id': self.product_5.id,
            'product_qty': 10,
            'product_uom': self.product_5.uom_id.id,
            'price_unit': 100.00,
            'date_planned': fields.Date.today(),
        })
        self.assertEqual(len(purchase_order.order_line), 2)
        purchase_order.button_confirm()
        self.assertTrue(purchase_order.picking_ids)
        picking_in_1 = purchase_order.picking_ids
        line_product_4 = picking_in_1.move_ids.filtered(
            lambda ln: ln.product_id == self.product_4)
        self.assertEqual(len(line_product_4), 1)
        self.assertEqual(line_product_4.product_qty, 5)
        line_product_5 = picking_in_1.move_ids.filtered(
            lambda ln: ln.product_id == self.product_5)
        self.assertEqual(len(line_product_5), 1)
        self.assertEqual(line_product_5.product_qty, 10)
        line_product_4.quantity_done = 5
        line_product_5.quantity_done = 7
        self.validate_picking(picking_in_1)
        po_line_product_4 = purchase_order.order_line.filtered(
            lambda ln: ln.product_id == self.product_4)
        self.assertEqual(len(po_line_product_4), 1)
        self.assertEqual(po_line_product_4.product_qty, 5)
        self.assertEqual(po_line_product_4.qty_received, 5)
        po_line_product_5 = purchase_order.order_line.filtered(
            lambda ln: ln.product_id == self.product_5)
        self.assertEqual(len(po_line_product_5), 1)
        self.assertEqual(po_line_product_5.product_qty, 10)
        self.assertEqual(po_line_product_5.qty_received, 7)
        picking_in_2 = purchase_order.picking_ids.filtered(
            lambda p: p.backorder_id)
        self.assertEqual(len(picking_in_2.move_ids), 1)
        line_product_4 = picking_in_2.move_ids.filtered(
            lambda ln: ln.product_id == self.product_4)
        self.assertEqual(len(line_product_4), 0)
        line_product_5 = picking_in_2.move_ids.filtered(
            lambda ln: ln.product_id == self.product_5)
        self.assertEqual(len(line_product_5), 1)
        self.assertEqual(line_product_5.product_qty, 3)
        self.assertTrue(picking_in_2.action_cancel())
        self.assertEqual(picking_in_2.state, 'cancel')
        po_line_product_4 = purchase_order.order_line.filtered(
            lambda ln: ln.product_id == self.product_4)
        self.assertEqual(len(po_line_product_4), 1)
        self.assertEqual(po_line_product_4.product_qty, 5)
        self.assertEqual(po_line_product_4.qty_received, 5)
        po_line_product_5 = purchase_order.order_line.filtered(
            lambda ln: ln.product_id == self.product_5)
        self.assertEqual(len(po_line_product_5), 1)
        self.assertEqual(po_line_product_5.product_qty, 10)
        self.assertEqual(po_line_product_5.qty_received, 7)
        self.assertIsNone(purchase_order.action_recreate_picking())
        self.assertEqual(len(purchase_order.picking_ids), 3)
        last_picking = self.env['stock.picking'].search([
            ('purchase_id', '=', purchase_order.id),
        ], order='id desc', limit=1)
        last_pick_line_product_4 = last_picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_4)
        self.assertEqual(last_pick_line_product_4.product_uom_qty, 0)
        last_pick_line_product_5 = last_picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_5)
        self.assertEqual(last_pick_line_product_5.product_uom_qty, 3)
        self.assertTrue(last_picking.partner_id)
        last_pick_line_product_5.quantity_done = 3
        last_picking.move_ids.quantity_done = 3
        self.validate_picking(last_picking)
        self.assertEqual(last_picking.state, 'done')
        self.assertEqual(po_line_product_4.product_qty, 5)
        self.assertEqual(po_line_product_4.qty_received, 5)
        self.assertEqual(po_line_product_5.product_qty, 10)
        self.assertEqual(po_line_product_5.qty_received, 10)
