###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


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

    def test_return_and_recreate_picking(self):
        purchase_order = self.create_purchase(1)
        purchase_order.button_confirm()
        self.assertTrue(purchase_order.picking_ids)
        picking = purchase_order.picking_ids
        picking.move_lines.write({
            'quantity_done': 1,
        })
        self.assertTrue(picking.action_confirm())
        self.assertTrue(picking.action_assign())
        self.assertTrue(picking.action_done())
        qty_delivery_lines = purchase_order.mapped('order_line').filtered(
            lambda l: l.qty_received != l.product_uom_qty)
        self.assertFalse(qty_delivery_lines)
        picking_wizard = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids, active_id=picking.id).create({})
        picking_wizard.product_return_moves.quantity = 1.0
        picking_wizard.product_return_moves.to_refund = True
        picking_return_action = picking_wizard.create_returns()
        picking_return = self.env['stock.picking'].browse(
            picking_return_action['res_id'])
        picking_return.move_lines[0].move_line_ids[0].qty_done = 1.0
        self.assertTrue(picking_return.action_done())
        self.assertEquals(purchase_order.state, 'purchase')
        self.assertIsNone(purchase_order.action_recreate_picking())
        self.assertEquals(len(purchase_order.picking_ids), 3)
        last_picking = self.env['stock.picking'].search([
            ('purchase_id', '=', purchase_order.id),
        ], order='id desc', limit=1)
        self.assertEquals(last_picking.move_lines[0].product_uom_qty, 1)
        self.assertTrue(last_picking.partner_id)
        last_picking.move_lines.write({
            'quantity_done': 1,
        })
        self.assertTrue(last_picking.action_done())
        self.assertEquals(last_picking.state, 'done')

    def test_return_partial_and_recreate_picking(self):
        purchase_order = self.create_purchase(5)
        purchase_order.button_confirm()
        self.assertTrue(purchase_order.picking_ids)
        picking = purchase_order.picking_ids
        picking.move_lines.write({
            'quantity_done': 5,
        })
        self.assertTrue(picking.action_confirm())
        self.assertTrue(picking.action_assign())
        self.assertTrue(picking.action_done())
        qty_delivery_lines = purchase_order.mapped('order_line').filtered(
            lambda l: l.qty_received != l.product_uom_qty)
        self.assertFalse(qty_delivery_lines)
        picking_wizard = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids, active_id=picking.id).create({})
        picking_wizard.product_return_moves.quantity = 3.0
        picking_wizard.product_return_moves.to_refund = True
        picking_return_action = picking_wizard.create_returns()
        picking_return = self.env['stock.picking'].browse(
            picking_return_action['res_id'])
        picking_return.move_lines[0].move_line_ids[0].qty_done = 3.0
        self.assertTrue(picking_return.action_done())
        self.assertEquals(purchase_order.state, 'purchase')
        self.assertIsNone(purchase_order.action_recreate_picking())
        self.assertEquals(len(purchase_order.picking_ids), 3)
        last_picking = self.env['stock.picking'].search([
            ('purchase_id', '=', purchase_order.id),
        ], order='id desc', limit=1)
        self.assertEquals(last_picking.move_lines[0].product_uom_qty, 3)
        self.assertTrue(last_picking.partner_id)
        last_picking.move_lines.write({
            'quantity_done': 3,
        })
        self.assertTrue(last_picking.action_done())
        self.assertEquals(last_picking.state, 'done')

    def test_return_more_qty_and_recreate_picking(self):
        purchase_order = self.create_purchase(5)
        purchase_order.button_confirm()
        self.assertTrue(purchase_order.picking_ids)
        picking = purchase_order.picking_ids
        picking.move_lines.write({
            'quantity_done': 5,
        })
        self.assertTrue(picking.action_confirm())
        self.assertTrue(picking.action_assign())
        self.assertTrue(picking.action_done())
        qty_delivery_lines = purchase_order.mapped('order_line').filtered(
            lambda l: l.qty_received != l.product_uom_qty)
        self.assertFalse(qty_delivery_lines)
        picking_wizard = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids, active_id=picking.id).create({})
        picking_wizard.product_return_moves.quantity = 6.0
        picking_wizard.product_return_moves.to_refund = True
        picking_return_action = picking_wizard.create_returns()
        picking_return = self.env['stock.picking'].browse(
            picking_return_action['res_id'])
        picking_return.move_lines[0].move_line_ids[0].qty_done = 6.0
        self.assertTrue(picking_return.action_done())
        self.assertEquals(purchase_order.state, 'purchase')
        with self.assertRaises(UserError):
            purchase_order.action_recreate_picking()
        self.assertEquals(len(purchase_order.picking_ids), 2)

    def test_return_and_recreate_picking_several_lines(self):
        purchase_order = self.create_purchase(1)
        self.env['purchase.order.line'].create({
            'order_id': purchase_order.id,
            'name': self.product_5.name,
            'product_id': self.product_5.id,
            'product_qty': 10,
            'product_uom': self.product_5.uom_id.id,
            'price_unit': 100.00,
            'date_planned': fields.Date.today(),
        })
        self.assertEquals(len(purchase_order.order_line), 2)
        purchase_order.button_confirm()
        self.assertTrue(purchase_order.picking_ids)
        picking = purchase_order.picking_ids
        for move in picking.move_lines:
            move.write({
                'quantity_done': move.product_qty,
            })
        self.assertTrue(picking.action_confirm())
        self.assertTrue(picking.action_assign())
        self.assertTrue(picking.action_done())
        qty_delivery_lines = purchase_order.mapped('order_line').filtered(
            lambda l: l.qty_received != l.product_uom_qty)
        self.assertFalse(qty_delivery_lines)
        picking_wizard = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids, active_id=picking.id).create({})
        picking_wizard.product_return_moves[0].quantity = 1.0
        picking_wizard.product_return_moves[0].to_refund = True
        picking_wizard.product_return_moves[1].quantity = 10.0
        picking_wizard.product_return_moves[1].to_refund = True
        picking_return_action = picking_wizard.create_returns()
        picking_return = self.env['stock.picking'].browse(
            picking_return_action['res_id'])
        picking_return.move_lines[0].move_line_ids[0].qty_done = 1.0
        picking_return.move_lines[1].move_line_ids[0].qty_done = 10.0
        self.assertTrue(picking_return.action_done())
        self.assertEquals(purchase_order.state, 'purchase')
        self.assertIsNone(purchase_order.action_recreate_picking())
        self.assertEquals(len(purchase_order.picking_ids), 3)
        last_picking = self.env['stock.picking'].search([
            ('purchase_id', '=', purchase_order.id),
        ], order='id desc', limit=1)
        self.assertEquals(last_picking.move_lines[0].product_uom_qty, 1)
        self.assertEquals(last_picking.move_lines[1].product_uom_qty, 10)
        self.assertTrue(last_picking.partner_id)
        for move in last_picking.move_lines:
            move.write({
                'quantity_done': move.product_qty,
            })
        self.assertTrue(last_picking.action_done())
        self.assertEquals(last_picking.state, 'done')

    def test_return_partial_and_recreate_picking_several_lines(self):
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
        self.assertEquals(len(purchase_order.order_line), 2)
        purchase_order.button_confirm()
        self.assertTrue(purchase_order.picking_ids)
        picking = purchase_order.picking_ids
        picking.move_lines[0].write({
            'quantity_done': 5,
        })
        picking.move_lines[1].write({
            'quantity_done': 10,
        })
        self.assertTrue(picking.action_confirm())
        self.assertTrue(picking.action_assign())
        self.assertTrue(picking.action_done())
        qty_delivery_lines = purchase_order.mapped('order_line').filtered(
            lambda l: l.qty_received != l.product_uom_qty)
        self.assertFalse(qty_delivery_lines)
        picking_wizard = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids, active_id=picking.id).create({})
        picking_wizard.product_return_moves[0].quantity = 3.0
        picking_wizard.product_return_moves[0].to_refund = True
        picking_wizard.product_return_moves[1].quantity = 1.0
        picking_wizard.product_return_moves[1].to_refund = True
        picking_return_action = picking_wizard.create_returns()
        picking_return = self.env['stock.picking'].browse(
            picking_return_action['res_id'])
        picking_return.move_lines[0].move_line_ids[0].qty_done = 3.0
        picking_return.move_lines[1].move_line_ids[0].qty_done = 1.0
        self.assertTrue(picking_return.action_done())
        self.assertEquals(purchase_order.state, 'purchase')
        self.assertIsNone(purchase_order.action_recreate_picking())
        self.assertEquals(len(purchase_order.picking_ids), 3)
        last_picking = self.env['stock.picking'].search([
            ('purchase_id', '=', purchase_order.id),
        ], order='id desc', limit=1)
        self.assertEquals(last_picking.move_lines[0].product_uom_qty, 3)
        self.assertEquals(last_picking.move_lines[1].product_uom_qty, 1)
        self.assertTrue(last_picking.partner_id)
        last_picking.move_lines[0].write({
            'quantity_done': 3,
        })
        last_picking.move_lines[1].write({
            'quantity_done': 1,
        })
        self.assertTrue(last_picking.action_done())
        self.assertEquals(last_picking.state, 'done')

    def test_partial_in_return_and_recreate_picking_several_lines(self):
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
        self.assertEquals(len(purchase_order.order_line), 2)
        purchase_order.button_confirm()
        self.assertTrue(purchase_order.picking_ids)
        picking_in_1 = purchase_order.picking_ids
        line_product_4 = picking_in_1.move_lines.filtered(
            lambda ln: ln.product_id == self.product_4)
        self.assertEquals(len(line_product_4), 1)
        self.assertEquals(line_product_4.product_qty, 5)
        line_product_5 = picking_in_1.move_lines.filtered(
            lambda ln: ln.product_id == self.product_5)
        self.assertEquals(len(line_product_5), 1)
        self.assertEquals(line_product_5.product_qty, 10)
        line_product_4.quantity_done = 4
        line_product_5.quantity_done = 7
        res = picking_in_1.button_validate()
        self.assertEqual(res['res_model'], 'stock.backorder.confirmation')
        wizard = self.env[(res.get('res_model'))].browse(res.get('res_id'))
        wizard.process()
        self.assertEquals(picking_in_1.state, 'done')
        po_line_product_4 = purchase_order.order_line.filtered(
            lambda ln: ln.product_id == self.product_4)
        self.assertEquals(len(po_line_product_4), 1)
        self.assertEquals(po_line_product_4.product_qty, 5)
        self.assertEquals(po_line_product_4.qty_received, 4)
        po_line_product_5 = purchase_order.order_line.filtered(
            lambda ln: ln.product_id == self.product_5)
        self.assertEquals(len(po_line_product_5), 1)
        self.assertEquals(po_line_product_5.product_qty, 10)
        self.assertEquals(po_line_product_5.qty_received, 7)
        picking_in_2 = purchase_order.picking_ids.filtered(
            lambda p: p.backorder_id)
        self.assertEqual(len(picking_in_2.move_lines), 2)
        line_product_4 = picking_in_2.move_lines.filtered(
            lambda ln: ln.product_id == self.product_4)
        self.assertEquals(len(line_product_4), 1)
        self.assertEquals(line_product_4.product_qty, 1)
        line_product_5 = picking_in_2.move_lines.filtered(
            lambda ln: ln.product_id == self.product_5)
        self.assertEquals(len(line_product_5), 1)
        self.assertEquals(line_product_5.product_qty, 3)
        line_product_4.quantity_done = 1
        line_product_5.quantity_done = 3
        self.assertTrue(picking_in_2.action_confirm())
        self.assertTrue(picking_in_2.action_assign())
        self.assertTrue(picking_in_2.action_done())
        self.assertEquals(picking_in_2.state, 'done')
        po_line_product_4 = purchase_order.order_line.filtered(
            lambda ln: ln.product_id == self.product_4)
        self.assertEquals(len(po_line_product_4), 1)
        self.assertEquals(po_line_product_4.product_qty, 5)
        self.assertEquals(po_line_product_4.qty_received, 5)
        po_line_product_5 = purchase_order.order_line.filtered(
            lambda ln: ln.product_id == self.product_5)
        self.assertEquals(len(po_line_product_5), 1)
        self.assertEquals(po_line_product_5.product_qty, 10)
        self.assertEquals(po_line_product_5.qty_received, 10)
        picking_wizard = self.env['stock.return.picking'].with_context(
            active_ids=picking_in_1.ids, active_id=picking_in_1.id).create({})
        ret_line_product_4 = picking_wizard.product_return_moves.filtered(
            lambda ln: ln.product_id == self.product_4)
        self.assertEquals(len(ret_line_product_4), 1)
        ret_line_product_4.quantity = 2.0
        ret_line_product_4.to_refund = True
        ret_line_product_5 = picking_wizard.product_return_moves.filtered(
            lambda ln: ln.product_id == self.product_5)
        self.assertEquals(len(ret_line_product_5), 1)
        ret_line_product_5.quantity = 6.0
        ret_line_product_5.to_refund = True
        picking_return_action = picking_wizard.create_returns()
        picking_return = self.env['stock.picking'].browse(
            picking_return_action['res_id'])
        return_line_product_4 = picking_return.move_lines.filtered(
            lambda ln: ln.product_id == self.product_4)
        return_line_product_4.move_line_ids.qty_done = 2.0
        return_line_product_5 = picking_return.move_lines.filtered(
            lambda ln: ln.product_id == self.product_5)
        return_line_product_5.move_line_ids.qty_done = 6.0
        self.assertTrue(picking_return.action_done())
        self.assertEquals(picking_return.state, 'done')
        self.assertEquals(purchase_order.state, 'purchase')
        self.assertEquals(po_line_product_4.product_qty, 5)
        self.assertEquals(po_line_product_4.qty_received, 3)
        self.assertEquals(po_line_product_5.product_qty, 10)
        self.assertEquals(po_line_product_5.qty_received, 4)
        self.assertIsNone(purchase_order.action_recreate_picking())
        self.assertEquals(len(purchase_order.picking_ids), 4)
        last_picking = self.env['stock.picking'].search([
            ('purchase_id', '=', purchase_order.id),
        ], order='id desc', limit=1)
        last_pick_line_product_4 = last_picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_4)
        self.assertEquals(last_pick_line_product_4.product_uom_qty, 2)
        last_pick_line_product_5 = last_picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_5)
        self.assertEquals(last_pick_line_product_5.product_uom_qty, 6)
        self.assertTrue(last_picking.partner_id)
        last_pick_line_product_4.quantity_done = 2
        last_pick_line_product_5.quantity_done = 6
        last_picking.move_lines[0].quantity_done = 2
        last_picking.move_lines[1].quantity_done = 6
        self.assertTrue(last_picking.action_confirm())
        self.assertTrue(last_picking.action_assign())
        self.assertTrue(last_picking.action_done())
        self.assertEquals(last_picking.state, 'done')
        self.assertEquals(po_line_product_4.product_qty, 5)
        self.assertEquals(po_line_product_4.qty_received, 5)
        self.assertEquals(po_line_product_5.product_qty, 10)
        self.assertEquals(po_line_product_5.qty_received, 10)

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
        self.assertEquals(len(purchase_order.order_line), 2)
        purchase_order.button_confirm()
        self.assertTrue(purchase_order.picking_ids)
        picking_in_1 = purchase_order.picking_ids
        line_product_4 = picking_in_1.move_lines.filtered(
            lambda ln: ln.product_id == self.product_4)
        self.assertEquals(len(line_product_4), 1)
        self.assertEquals(line_product_4.product_qty, 5)
        line_product_5 = picking_in_1.move_lines.filtered(
            lambda ln: ln.product_id == self.product_5)
        self.assertEquals(len(line_product_5), 1)
        self.assertEquals(line_product_5.product_qty, 10)
        line_product_4.quantity_done = 5
        line_product_5.quantity_done = 7
        res = picking_in_1.button_validate()
        self.assertEqual(res['res_model'], 'stock.backorder.confirmation')
        wizard = self.env[(res.get('res_model'))].browse(res.get('res_id'))
        wizard.process()
        self.assertEquals(picking_in_1.state, 'done')
        po_line_product_4 = purchase_order.order_line.filtered(
            lambda ln: ln.product_id == self.product_4)
        self.assertEquals(len(po_line_product_4), 1)
        self.assertEquals(po_line_product_4.product_qty, 5)
        self.assertEquals(po_line_product_4.qty_received, 5)
        po_line_product_5 = purchase_order.order_line.filtered(
            lambda ln: ln.product_id == self.product_5)
        self.assertEquals(len(po_line_product_5), 1)
        self.assertEquals(po_line_product_5.product_qty, 10)
        self.assertEquals(po_line_product_5.qty_received, 7)
        picking_in_2 = purchase_order.picking_ids.filtered(
            lambda p: p.backorder_id)
        self.assertEqual(len(picking_in_2.move_lines), 1)
        line_product_4 = picking_in_2.move_lines.filtered(
            lambda ln: ln.product_id == self.product_4)
        self.assertEquals(len(line_product_4), 0)
        line_product_5 = picking_in_2.move_lines.filtered(
            lambda ln: ln.product_id == self.product_5)
        self.assertEquals(len(line_product_5), 1)
        self.assertEquals(line_product_5.product_qty, 3)
        self.assertTrue(picking_in_2.action_cancel())
        self.assertEquals(picking_in_2.state, 'cancel')
        po_line_product_4 = purchase_order.order_line.filtered(
            lambda ln: ln.product_id == self.product_4)
        self.assertEquals(len(po_line_product_4), 1)
        self.assertEquals(po_line_product_4.product_qty, 5)
        self.assertEquals(po_line_product_4.qty_received, 5)
        po_line_product_5 = purchase_order.order_line.filtered(
            lambda ln: ln.product_id == self.product_5)
        self.assertEquals(len(po_line_product_5), 1)
        self.assertEquals(po_line_product_5.product_qty, 10)
        self.assertEquals(po_line_product_5.qty_received, 7)
        self.assertIsNone(purchase_order.action_recreate_picking())
        self.assertEquals(len(purchase_order.picking_ids), 3)
        last_picking = self.env['stock.picking'].search([
            ('purchase_id', '=', purchase_order.id),
        ], order='id desc', limit=1)
        last_pick_line_product_4 = last_picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_4)
        self.assertEquals(last_pick_line_product_4.product_uom_qty, 0)
        last_pick_line_product_5 = last_picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_5)
        self.assertEquals(last_pick_line_product_5.product_uom_qty, 3)
        self.assertTrue(last_picking.partner_id)
        last_pick_line_product_5.quantity_done = 3
        last_picking.move_lines.quantity_done = 3
        self.assertTrue(last_picking.action_confirm())
        self.assertTrue(last_picking.action_assign())
        self.assertTrue(last_picking.action_done())
        self.assertEquals(last_picking.state, 'done')
        self.assertEquals(po_line_product_4.product_qty, 5)
        self.assertEquals(po_line_product_4.qty_received, 5)
        self.assertEquals(po_line_product_5.product_qty, 10)
        self.assertEquals(po_line_product_5.qty_received, 10)
