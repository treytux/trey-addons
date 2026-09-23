###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests import common


class TestSaleCancelExtend(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Test partner 01',
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 1',
            'standard_price': 10,
            'list_price': 30,
        })
        self.stock_wh = self.env.ref('stock.warehouse0')
        self.sale_01 = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 100,
                    'product_uom_qty': 5,
                }),
            ]
        })

    def update_qty_on_hand(self, product, location, new_qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': new_qty,
            'location_id': location.id,
        })
        wizard.change_product_qty()
        self.assertEquals(product.with_context(
            location=location.id).qty_available, new_qty)

    def test_sale_cancel_picking_done_not_invoice_to_return_true_return_ok(
            self):
        self.sale_01.action_confirm()
        self.assertEquals(self.sale_01.state, 'sale')
        self.assertEquals(len(self.sale_01.picking_ids), 1)
        picking = self.sale_01.picking_ids
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        with self.assertRaises(UserError) as result:
            self.sale_01.action_cancel()
        self.assertEqual(
            result.exception.name,
            'You cannot cancel a stock move that has been set to \'Done\' if '
            'not all material has been returned. You must make the complete '
            'return of the move material so that the quantity delivered is 0.')
        done_picking = picking.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_picking.ids,
            active_id=done_picking.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_01).quantity = 1
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_01).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_01).to_refund = True
        return_pick.action_done()
        self.assertEquals(len(self.sale_01.picking_ids), 2)
        self.assertEquals(self.sale_01.order_line.qty_delivered, 4)
        with self.assertRaises(UserError) as result:
            self.sale_01.action_cancel()
        self.assertEqual(
            result.exception.name,
            'You cannot cancel a stock move that has been set to \'Done\' if '
            'not all material has been returned. You must make the complete '
            'return of the move material so that the quantity delivered is 0.')
        done_picking = picking.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_picking.ids,
            active_id=done_picking.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_01).quantity = 4
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_01).quantity_done = 4
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_01).to_refund = True
        return_pick.action_done()
        self.assertEquals(len(self.sale_01.picking_ids), 3)
        self.assertEquals(self.sale_01.order_line.qty_delivered, 0)
        self.sale_01.action_cancel()
        self.assertEquals(self.sale_01.state, 'cancel')
        self.assertEquals(
            list(set(self.sale_01.mapped('picking_ids.state'))),
            ['done'])

    def test_sale_cancel_picking_done_not_invoice_to_return_false_return_fail(
            self):
        self.sale_01.action_confirm()
        self.assertEquals(self.sale_01.state, 'sale')
        self.assertEquals(len(self.sale_01.picking_ids), 1)
        picking = self.sale_01.picking_ids
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        with self.assertRaises(UserError) as result:
            self.sale_01.action_cancel()
        self.assertEqual(
            result.exception.name,
            'You cannot cancel a stock move that has been set to \'Done\' if '
            'not all material has been returned. You must make the complete '
            'return of the move material so that the quantity delivered is 0.')
        done_picking = picking.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_picking.ids,
            active_id=done_picking.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_01).quantity = 1
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_01).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_01).to_refund = False
        return_pick.action_done()
        self.assertEquals(len(self.sale_01.picking_ids), 2)
        self.assertEquals(self.sale_01.order_line.qty_delivered, 5)
        with self.assertRaises(UserError) as result:
            self.sale_01.action_cancel()
        self.assertEqual(
            result.exception.name,
            'You cannot cancel a stock move that has been set to \'Done\' if '
            'not all material has been returned. You must make the complete '
            'return of the move material so that the quantity delivered is 0.')
        self.assertEquals(self.sale_01.state, 'sale')
        self.assertEquals(
            list(set(self.sale_01.mapped('picking_ids.state'))),
            ['done'])

    def test_sale_cancel_with_invoice_fail(self):
        self.sale_01.action_confirm()
        self.assertEquals(self.sale_01.state, 'sale')
        self.assertEquals(len(self.sale_01.picking_ids), 1)
        self.assertEquals(self.sale_01.picking_ids.state, 'confirmed')
        self.sale_01.action_invoice_create()
        self.assertEqual(len(self.sale_01.invoice_ids), 1)
        with self.assertRaises(UserError) as result:
            self.sale_01.action_cancel()
        self.assertEqual(
            result.exception.name,
            'You cannot cancel a sale order that has been invoiced.')

    def test_sale_cancel_with_invoice_skip_check(self):
        self.sale_01.action_confirm()
        self.assertEquals(self.sale_01.state, 'sale')
        self.assertEquals(len(self.sale_01.picking_ids), 1)
        self.assertEquals(self.sale_01.picking_ids.state, 'confirmed')
        self.sale_01.action_invoice_create()
        self.assertEqual(len(self.sale_01.invoice_ids), 1)
        self.sale_01.with_context(skip_check_cancel=True).action_cancel()
        self.assertEquals(self.sale_01.state, 'cancel')

    def test_sale_cancel_with_invoice_picking_done_to_return_true_return_fail(
            self):
        self.sale_01.action_confirm()
        self.assertEquals(self.sale_01.state, 'sale')
        self.assertEquals(len(self.sale_01.picking_ids), 1)
        picking = self.sale_01.picking_ids
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        with self.assertRaises(UserError) as result:
            self.sale_01.action_cancel()
        self.assertEqual(
            result.exception.name,
            'You cannot cancel a stock move that has been set to \'Done\' if '
            'not all material has been returned. You must make the complete '
            'return of the move material so that the quantity delivered is 0.')
        done_picking = picking.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_picking.ids,
            active_id=done_picking.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_01).quantity = 1
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_01).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_01).to_refund = True
        return_pick.action_done()
        self.assertEquals(len(self.sale_01.picking_ids), 2)
        self.assertEquals(self.sale_01.order_line.qty_delivered, 4)
        with self.assertRaises(UserError) as result:
            self.sale_01.action_cancel()
        self.assertEqual(
            result.exception.name,
            'You cannot cancel a stock move that has been set to \'Done\' if '
            'not all material has been returned. You must make the complete '
            'return of the move material so that the quantity delivered is 0.')
        done_picking = picking.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_picking.ids,
            active_id=done_picking.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_01).quantity = 4
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_01).quantity_done = 4
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_01).to_refund = True
        return_pick.action_done()
        self.assertEquals(len(self.sale_01.picking_ids), 3)
        self.assertEquals(self.sale_01.order_line.qty_delivered, 0)
        self.sale_01.action_invoice_create()
        self.assertEqual(len(self.sale_01.invoice_ids), 1)
        with self.assertRaises(UserError) as result:
            self.sale_01.action_cancel()
        self.assertEqual(
            result.exception.name,
            'You cannot cancel a sale order that has been invoiced.')
        self.assertEquals(self.sale_01.state, 'sale')

    def test_sale_cancel_picking_done_not_invoice_confirmed_ok(self):
        self.sale_01.action_confirm()
        self.assertEquals(self.sale_01.state, 'sale')
        self.assertEquals(len(self.sale_01.picking_ids), 1)
        self.assertEquals(self.sale_01.picking_ids.state, 'confirmed')
        self.assertEquals(self.sale_01.order_line.qty_delivered, 0)
        self.sale_01.action_cancel()
        self.assertEquals(self.sale_01.state, 'cancel')
        self.assertEquals(self.sale_01.picking_ids.state, 'cancel')

    def test_sale_cancel_picking_done_not_invoice_assigned_ok(self):
        self.sale_01.action_confirm()
        self.assertEquals(self.sale_01.state, 'sale')
        self.assertEquals(len(self.sale_01.picking_ids), 1)
        picking = self.sale_01.picking_ids
        self.assertEquals(picking.state, 'confirmed')
        self.assertEquals(self.sale_01.order_line.qty_delivered, 0)
        self.update_qty_on_hand(
            self.product_01, self.stock_wh.lot_stock_id, 10)
        picking.action_assign()
        self.assertEquals(picking.state, 'assigned')
        self.assertEquals(self.sale_01.order_line.qty_delivered, 0)
        self.sale_01.action_cancel()
        self.assertEquals(self.sale_01.state, 'cancel')
        self.assertEquals(self.sale_01.picking_ids.state, 'cancel')

    def test_sale_cancel_pickings_backorder_not_invoice_return_ok(self):
        self.sale_01.action_confirm()
        self.assertEquals(self.sale_01.state, 'sale')
        self.assertEquals(len(self.sale_01.picking_ids), 1)
        picking = self.sale_01.picking_ids
        self.assertEqual(len(picking.move_lines), 1)
        picking.move_lines[0].quantity_done = 1
        res = picking.button_validate()
        self.assertEqual(res.get('res_model'), 'stock.backorder.confirmation')
        wizard = self.env[(res.get('res_model'))].browse(res.get('res_id'))
        wizard.process()
        self.assertEqual(len(self.sale_01.picking_ids), 2)
        self.assertEqual(
            self.sale_01.picking_ids.mapped('state'), ['confirmed', 'done'])
        confirmed_picking = self.sale_01.picking_ids.filtered(
            lambda p: p.state == 'confirmed')
        self.assertEquals(len(confirmed_picking), 1)
        done_picking = self.sale_01.picking_ids.filtered(
            lambda p: p.state == 'done')
        self.assertEquals(len(done_picking), 1)
        self.assertEquals(self.sale_01.order_line.qty_delivered, 1)
        with self.assertRaises(UserError) as result:
            self.sale_01.action_cancel()
        self.assertEqual(
            result.exception.name,
            'You cannot cancel a stock move that has been set to \'Done\' if '
            'not all material has been returned. You must make the complete '
            'return of the move material so that the quantity delivered is 0.')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_picking.ids,
            active_id=done_picking.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_01).quantity = 1
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_01).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_01).to_refund = True
        return_pick.action_done()
        self.assertEquals(self.sale_01.order_line.qty_delivered, 0)
        self.assertEquals(len(self.sale_01.picking_ids), 3)
        self.sale_01.with_context(debug=True).action_cancel()
        self.assertEquals(self.sale_01.state, 'cancel')
        self.assertEquals(done_picking.state, 'done')
        self.assertEquals(return_pick.state, 'done')
        self.assertEquals(confirmed_picking.state, 'cancel')
