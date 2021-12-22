###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleStockProductPack(TransactionCase):

    def setUp(self):
        super().setUp()
        product_obj = self.env['product.product']
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.product_1 = product_obj.create({
            'name': 'Component 1',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        self.product_2 = product_obj.create({
            'name': 'Component 2',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 500,
        })
        self.product_3 = product_obj.create({
            'name': 'Component 3',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 300,
        })
        pack_lines = [
            (0, 0, {
                'product_id': self.product_1.id,
                'quantity': 1,
            }),
            (0, 0, {
                'product_id': self.product_2.id,
                'quantity': 2,
            }),
        ]
        self.product_pack_delivery_detail = product_obj.create({
            'name': 'Pack',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 1,
            'pack_ok': True,
            'pack_type': 'detailed',
            'pack_component_price': 'detailed',
            'pack_line_ids': pack_lines,
        })
        self.product_pack_delivery_detail2 = product_obj.create({
            'name': 'Pack2',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 1,
            'pack_ok': True,
            'pack_type': 'detailed',
            'pack_component_price': 'detailed',
            'pack_line_ids': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'quantity': 10,
                }),
                (0, 0, {
                    'product_id': self.product_3.id,
                    'quantity': 30,
                }),
            ],
        })
        self.product_pack_order_detail = product_obj.create({
            'name': 'Pack',
            'type': 'product',
            'invoice_policy': 'order',
            'list_price': 1,
            'pack_ok': True,
            'pack_type': 'detailed',
            'pack_component_price': 'detailed',
            'pack_line_ids': pack_lines,
        })
        self.product_pack_delivery_totalized = product_obj.create({
            'name': 'Pack',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 1,
            'pack_ok': True,
            'pack_type': 'detailed',
            'pack_component_price': 'totalized',
            'pack_line_ids': pack_lines,
        })
        self.product_pack_delivery_totalized2 = product_obj.create({
            'name': 'Pack2',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 1,
            'pack_ok': True,
            'pack_type': 'detailed',
            'pack_component_price': 'totalized',
            'pack_line_ids': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'quantity': 10,
                }),
                (0, 0, {
                    'product_id': self.product_3.id,
                    'quantity': 30,
                }),
            ],
        })
        self.product_pack_order_totalized = product_obj.create({
            'name': 'Pack',
            'type': 'product',
            'invoice_policy': 'order',
            'list_price': 1,
            'pack_ok': True,
            'pack_type': 'detailed',
            'pack_component_price': 'totalized',
            'pack_line_ids': pack_lines,
        })
        self.product_pack_delivery_ignored = product_obj.create({
            'name': 'Pack',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 1,
            'pack_ok': True,
            'pack_type': 'detailed',
            'pack_component_price': 'ignored',
            'pack_line_ids': pack_lines,
        })
        self.product_pack_delivery_ignored2 = product_obj.create({
            'name': 'Pack',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 1,
            'pack_ok': True,
            'pack_type': 'detailed',
            'pack_component_price': 'ignored',
            'pack_line_ids': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'quantity': 10,
                }),
                (0, 0, {
                    'product_id': self.product_3.id,
                    'quantity': 30,
                }),
            ],
        })
        self.product_pack_order_ignored = product_obj.create({
            'name': 'Pack',
            'type': 'product',
            'invoice_policy': 'order',
            'list_price': 1,
            'pack_ok': True,
            'pack_type': 'detailed',
            'pack_component_price': 'ignored',
            'pack_line_ids': pack_lines,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Customer',
            'customer': True,
        })

    def get_stock(self, product, location):
        return product.with_context(location=location.id).qty_available

    def update_stock(self, product, location, qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'location_id': location.id,
            'new_quantity': qty,
        })
        wizard.change_product_qty()
        product_qty = self.get_stock(product, location)
        self.assertEquals(product_qty, qty)

    def test_sale_with_pack_delivery_detail(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_detail, self.stock_location)
        self.assertEquals(product_pack_qty, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_detail.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.price_unit, 1)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.price_unit, 100)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.price_unit, 500)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 2)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 1)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 1)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 1)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 2)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 2)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 1)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 1)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 2)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 1)
        self.assertEquals(line_product_pack.qty_invoiced, 1)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 1)
        self.assertEquals(line_product_1.qty_invoiced, 1)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 2)
        self.assertEquals(line_product_2.qty_invoiced, 2)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = sale.picking_ids.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 0)
        self.assertEquals(line_product_pack.qty_invoiced, 1)
        self.assertEquals(line_product_pack.qty_to_invoice, -1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 0)
        self.assertEquals(line_product_1.qty_invoiced, 1)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 0)
        self.assertEquals(line_product_2.qty_invoiced, 2)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_sale_with_pack_order_detail(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        product_pack_qty = self.get_stock(
            self.product_pack_order_detail, self.stock_location)
        self.assertEquals(product_pack_qty, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_order_detail.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.price_unit, 1)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.price_unit, 100)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.price_unit, 500)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 1)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 1)
        sale.invoice_ids.unlink()
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 2)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 1)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 1)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 1)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 2)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 2)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 1)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 1)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 2)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 1)
        self.assertEquals(line_product_pack.qty_invoiced, 1)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 1)
        self.assertEquals(line_product_1.qty_invoiced, 1)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 2)
        self.assertEquals(line_product_2.qty_invoiced, 2)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = sale.picking_ids.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 0)
        self.assertEquals(line_product_pack.qty_invoiced, 1)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 0)
        self.assertEquals(line_product_1.qty_invoiced, 1)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 0)
        self.assertEquals(line_product_2.qty_invoiced, 2)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_sale_with_packs_delivery_detail(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_detail, self.stock_location)
        self.assertEquals(product_pack_qty, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_detail.id,
                    'product_uom_qty': 4,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 4)
        self.assertEquals(line_product_pack.price_unit, 1)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 4)
        self.assertEquals(line_product_1.price_unit, 100)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 8)
        self.assertEquals(line_product_2.price_unit, 500)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 4)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 8)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(line_product_pack.product_uom_qty, 4)
        self.assertEquals(line_product_pack.qty_delivered, 4)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 4)
        self.assertEquals(line_product_1.product_uom_qty, 4)
        self.assertEquals(line_product_1.qty_delivered, 4)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 4)
        self.assertEquals(line_product_2.product_uom_qty, 8)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 8)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 4)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 4)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 8)
        self.assertEquals(line_product_pack.product_uom_qty, 4)
        self.assertEquals(line_product_pack.qty_delivered, 4)
        self.assertEquals(line_product_pack.qty_invoiced, 4)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 4)
        self.assertEquals(line_product_1.qty_delivered, 4)
        self.assertEquals(line_product_1.qty_invoiced, 4)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 8)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 8)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = sale.picking_ids.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 4)
        self.assertEquals(line_product_pack.qty_delivered, 3)
        self.assertEquals(line_product_pack.qty_invoiced, 4)
        self.assertEquals(line_product_pack.qty_to_invoice, -1)
        self.assertEquals(line_product_1.product_uom_qty, 4)
        self.assertEquals(line_product_1.qty_delivered, 3)
        self.assertEquals(line_product_1.qty_invoiced, 4)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 8)
        self.assertEquals(line_product_2.qty_delivered, 6)
        self.assertEquals(line_product_2.qty_invoiced, 8)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_sale_with_packs_order_detail(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        product_pack_qty = self.get_stock(
            self.product_pack_order_detail, self.stock_location)
        self.assertEquals(product_pack_qty, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_order_detail.id,
                    'product_uom_qty': 4,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 4)
        self.assertEquals(line_product_pack.price_unit, 1)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 4)
        self.assertEquals(line_product_1.price_unit, 100)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 8)
        self.assertEquals(line_product_2.price_unit, 500)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 1)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 4)
        sale.invoice_ids.unlink()
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 4)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 8)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(line_product_pack.product_uom_qty, 4)
        self.assertEquals(line_product_pack.qty_delivered, 4)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 4)
        self.assertEquals(line_product_1.product_uom_qty, 4)
        self.assertEquals(line_product_1.qty_delivered, 4)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 4)
        self.assertEquals(line_product_2.product_uom_qty, 8)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 8)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 4)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 4)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 8)
        self.assertEquals(line_product_pack.product_uom_qty, 4)
        self.assertEquals(line_product_pack.qty_delivered, 4)
        self.assertEquals(line_product_pack.qty_invoiced, 4)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 4)
        self.assertEquals(line_product_1.qty_delivered, 4)
        self.assertEquals(line_product_1.qty_invoiced, 4)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 8)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 8)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = sale.picking_ids.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 4)
        self.assertEquals(line_product_pack.qty_delivered, 3)
        self.assertEquals(line_product_pack.qty_invoiced, 4)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 4)
        self.assertEquals(line_product_1.qty_delivered, 3)
        self.assertEquals(line_product_1.qty_invoiced, 4)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 8)
        self.assertEquals(line_product_2.qty_delivered, 6)
        self.assertEquals(line_product_2.qty_invoiced, 8)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_sale_with_packs_delivery_detail_partial_complete(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_detail, self.stock_location)
        self.assertEquals(product_pack_qty, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_detail.id,
                    'product_uom_qty': 5,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.price_unit, 1)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.price_unit, 100)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.price_unit, 500)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 5)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 10)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 2
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 4
        action = picking.button_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 2)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 2)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 2)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 4)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 2)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 2)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 4)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 2)
        self.assertEquals(line_product_pack.qty_invoiced, 2)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 2)
        self.assertEquals(line_product_1.qty_invoiced, 2)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 4)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        picking2 = sale.picking_ids.filtered(lambda p: p.state == 'assigned')
        self.assertTrue(picking2)
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 3
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 6
        action = picking2.button_validate()
        self.assertEquals(action, None)
        self.assertEquals(
            list(set(sale.picking_ids.mapped('state'))), ['done'])
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 2)
        self.assertEquals(line_product_pack.qty_to_invoice, 3)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 5)
        self.assertEquals(line_product_1.qty_invoiced, 2)
        self.assertEquals(line_product_1.qty_to_invoice, 3)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 4)
        self.assertEquals(line_product_2.qty_to_invoice, 6)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 2)
        invoice2 = sale.invoice_ids - invoice
        self.assertEquals(len(invoice2.invoice_line_ids), 3)
        inv_line_product_pack = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 3)
        inv_line_product_1 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 3)
        inv_line_product_2 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 6)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 5)
        self.assertEquals(line_product_1.qty_invoiced, 5)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = picking2.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 4)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, -1)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 4)
        self.assertEquals(line_product_1.qty_invoiced, 5)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_sale_with_packs_delivery_detail_partial_incomplete(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_detail, self.stock_location)
        self.assertEquals(product_pack_qty, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_detail.id,
                    'product_uom_qty': 5,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.price_unit, 1)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.price_unit, 100)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.price_unit, 500)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 5)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 10)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 2
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 5
        action = picking.button_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 2)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 2)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 2)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 5)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 5)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 2)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 2)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 5)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 2)
        self.assertEquals(line_product_pack.qty_invoiced, 2)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 2)
        self.assertEquals(line_product_1.qty_invoiced, 2)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 5)
        self.assertEquals(line_product_2.qty_invoiced, 5)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        picking2 = sale.picking_ids.filtered(lambda p: p.state == 'assigned')
        self.assertTrue(picking2)
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 3
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 5
        action = picking2.button_validate()
        self.assertEquals(action, None)
        self.assertEquals(
            list(set(sale.picking_ids.mapped('state'))), ['done'])
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 2)
        self.assertEquals(line_product_pack.qty_to_invoice, 3)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 5)
        self.assertEquals(line_product_1.qty_invoiced, 2)
        self.assertEquals(line_product_1.qty_to_invoice, 3)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 5)
        self.assertEquals(line_product_2.qty_to_invoice, 5)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 2)
        invoice2 = sale.invoice_ids - invoice
        self.assertEquals(len(invoice2.invoice_line_ids), 3)
        inv_line_product_pack = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 3)
        inv_line_product_1 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 3)
        inv_line_product_2 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 5)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 5)
        self.assertEquals(line_product_1.qty_invoiced, 5)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = picking2.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 4)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, -1)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 4)
        self.assertEquals(line_product_1.qty_invoiced, 5)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_sale_with_packs_delivery_detail_partial_extra_qty(self):
        self.update_stock(self.product_1, self.stock_location, 100)
        self.update_stock(self.product_2, self.stock_location, 200)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_detail, self.stock_location)
        self.assertEquals(product_pack_qty, 100)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_detail.id,
                    'product_uom_qty': 5,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.price_unit, 1)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.price_unit, 100)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.price_unit, 500)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 5)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 10)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 2
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 4
        action = picking.button_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 2)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 2)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 2)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 4)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 2)
        self.assertEquals(inv_line_product_pack.price_unit, 1)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 2)
        self.assertEquals(inv_line_product_1.price_unit, 100)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 4)
        self.assertEquals(inv_line_product_2.price_unit, 500)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 2)
        self.assertEquals(line_product_pack.qty_invoiced, 2)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 2)
        self.assertEquals(line_product_1.qty_invoiced, 2)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 4)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        picking2 = sale.picking_ids.filtered(lambda p: p.state == 'assigned')
        self.assertTrue(picking2)
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 88
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 6
        action = picking2.button_validate()
        self.assertEqual(action['res_model'], 'stock.overprocessed.transfer')
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(
            list(set(sale.picking_ids.mapped('state'))), ['done'])
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 2)
        self.assertEquals(line_product_pack.qty_to_invoice, 3)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 90)
        self.assertEquals(line_product_1.qty_invoiced, 2)
        self.assertEquals(line_product_1.qty_to_invoice, 88)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 4)
        self.assertEquals(line_product_2.qty_to_invoice, 6)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 2)
        invoice2 = sale.invoice_ids - invoice
        self.assertEquals(len(invoice2.invoice_line_ids), 4)
        inv_line_product_pack = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 3)
        self.assertEquals(inv_line_product_pack.price_unit, 1)
        inv_line_product_1_qty_3 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 3)
        self.assertTrue(inv_line_product_1_qty_3)
        self.assertEquals(inv_line_product_1_qty_3.price_unit, 100)
        inv_line_product_1_qty_85 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 85)
        self.assertTrue(inv_line_product_1_qty_85)
        self.assertEquals(inv_line_product_1_qty_85.price_unit, 100)
        inv_line_product_2 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 6)
        self.assertEquals(inv_line_product_2.price_unit, 500)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 90)
        self.assertEquals(line_product_1.qty_invoiced, 90)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = picking2.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 4)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, -1)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 89)
        self.assertEquals(line_product_1.qty_invoiced, 90)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_sale_with_packs_order_detail_partial_complete(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        product_pack_qty = self.get_stock(
            self.product_pack_order_detail, self.stock_location)
        self.assertEquals(product_pack_qty, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_order_detail.id,
                    'product_uom_qty': 5,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.price_unit, 1)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.price_unit, 100)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.price_unit, 500)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 1)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 5)
        sale.invoice_ids.unlink()
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 5)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 10)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 2
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 4
        action = picking.button_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 2)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 5)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 2)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 4)
        picking2 = sale.picking_ids.filtered(lambda p: p.state == 'assigned')
        self.assertTrue(picking2)
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 3
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 6
        action = picking2.button_validate()
        self.assertEquals(action, None)
        self.assertEquals(
            list(set(sale.picking_ids.mapped('state'))), ['done'])
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 5)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 5)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 5)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 10)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 5)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 5)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 10)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 5)
        self.assertEquals(line_product_1.qty_invoiced, 5)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = picking2.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 4)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 4)
        self.assertEquals(line_product_1.qty_invoiced, 5)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_sale_with_packs_order_detail_partial_incomplete(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        product_pack_qty = self.get_stock(
            self.product_pack_order_detail, self.stock_location)
        self.assertEquals(product_pack_qty, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_order_detail.id,
                    'product_uom_qty': 5,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.price_unit, 1)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.price_unit, 100)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.price_unit, 500)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 1)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 5)
        sale.invoice_ids.unlink()
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 5)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 10)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 2
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 5
        action = picking.button_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 2)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 5)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 2)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 5)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 5)
        picking2 = sale.picking_ids.filtered(lambda p: p.state == 'assigned')
        self.assertTrue(picking2)
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 3
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 5
        action = picking2.button_validate()
        self.assertEquals(action, None)
        self.assertEquals(
            list(set(sale.picking_ids.mapped('state'))), ['done'])
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 5)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 5)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 5)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 10)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 5)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 5)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 10)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 5)
        self.assertEquals(line_product_1.qty_invoiced, 5)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = picking2.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 4)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 4)
        self.assertEquals(line_product_1.qty_invoiced, 5)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_sale_with_packs_order_detail_partial_extra_qty(self):
        self.update_stock(self.product_1, self.stock_location, 100)
        self.update_stock(self.product_2, self.stock_location, 200)
        product_pack_qty = self.get_stock(
            self.product_pack_order_detail, self.stock_location)
        self.assertEquals(product_pack_qty, 100)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_order_detail.id,
                    'product_uom_qty': 5,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.price_unit, 1)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.price_unit, 100)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.price_unit, 500)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 1)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 5)
        self.assertEquals(inv_line_product_pack.price_unit, 1)
        sale.invoice_ids.unlink()
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 5)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 10)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 2
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 4
        action = picking.button_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 2)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 5)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 2)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 4)
        picking2 = sale.picking_ids.filtered(lambda p: p.state == 'assigned')
        self.assertTrue(picking2)
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 88
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 6
        action = picking2.button_validate()
        self.assertEqual(action['res_model'], 'stock.overprocessed.transfer')
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(
            list(set(sale.picking_ids.mapped('state'))), ['done'])
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 5)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 90)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 90)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 10)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEquals(len(invoice.invoice_line_ids), 4)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 5)
        self.assertEquals(inv_line_product_pack.price_unit, 1)
        inv_line_product_1_qty_5 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 5)
        self.assertTrue(inv_line_product_1_qty_5)
        self.assertEquals(inv_line_product_1_qty_5.price_unit, 100)
        inv_line_product_1_qty_85 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 85)
        self.assertTrue(inv_line_product_1_qty_85)
        self.assertEquals(inv_line_product_1_qty_85.price_unit, 100)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 10)
        self.assertEquals(inv_line_product_2.price_unit, 500)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 90)
        self.assertEquals(line_product_1.qty_invoiced, 90)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = picking2.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 4)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 89)
        self.assertEquals(line_product_1.qty_invoiced, 90)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_sale_with_packs_totalized_delivery_partial_extra_qty(self):
        self.update_stock(self.product_1, self.stock_location, 100)
        self.update_stock(self.product_2, self.stock_location, 200)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_totalized, self.stock_location)
        self.assertEquals(product_pack_qty, 100)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_totalized.id,
                    'product_uom_qty': 5,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.price_unit, 1100)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.price_unit, 0)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.price_unit, 0)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 5)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 10)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 2
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 4
        action = picking.button_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 2)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 2)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 2)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 4)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 2)
        self.assertEquals(inv_line_product_pack.price_unit, 1100)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 2)
        self.assertEquals(inv_line_product_1.price_unit, 0)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 4)
        self.assertEquals(inv_line_product_2.price_unit, 0)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 2)
        self.assertEquals(line_product_pack.qty_invoiced, 2)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 2)
        self.assertEquals(line_product_1.qty_invoiced, 2)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 4)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        picking2 = sale.picking_ids.filtered(lambda p: p.state == 'assigned')
        self.assertTrue(picking2)
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 88
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 6
        action = picking2.button_validate()
        self.assertEqual(action['res_model'], 'stock.overprocessed.transfer')
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(
            list(set(sale.picking_ids.mapped('state'))), ['done'])
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 2)
        self.assertEquals(line_product_pack.qty_to_invoice, 3)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 90)
        self.assertEquals(line_product_1.qty_invoiced, 2)
        self.assertEquals(line_product_1.qty_to_invoice, 88)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 4)
        self.assertEquals(line_product_2.qty_to_invoice, 6)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 2)
        invoice2 = sale.invoice_ids - invoice
        self.assertEquals(len(invoice2.invoice_line_ids), 4)
        inv_line_product_pack = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 3)
        self.assertEquals(inv_line_product_pack.price_unit, 1100)
        inv_line_product_1_qty_3 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 3)
        self.assertTrue(inv_line_product_1_qty_3)
        self.assertEquals(inv_line_product_1_qty_3.price_unit, 0)
        inv_line_product_1_qty_85 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 85)
        self.assertTrue(inv_line_product_1_qty_85)
        self.assertEquals(inv_line_product_1_qty_85.price_unit, 100)
        inv_line_product_2 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 6)
        self.assertEquals(inv_line_product_2.price_unit, 0)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 90)
        self.assertEquals(line_product_1.qty_invoiced, 90)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = picking2.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 4)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, -1)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 89)
        self.assertEquals(line_product_1.qty_invoiced, 90)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_sale_with_packs_ignored_delivery_partial_extra_qty(self):
        self.update_stock(self.product_1, self.stock_location, 100)
        self.update_stock(self.product_2, self.stock_location, 200)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_ignored, self.stock_location)
        self.assertEquals(product_pack_qty, 100)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_ignored.id,
                    'product_uom_qty': 5,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.price_unit, 1)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.price_unit, 0)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.price_unit, 0)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 5)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 10)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 2
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 4
        action = picking.button_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 2)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 2)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 2)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 4)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 2)
        self.assertEquals(inv_line_product_pack.price_unit, 1)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 2)
        self.assertEquals(inv_line_product_1.price_unit, 0)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 4)
        self.assertEquals(inv_line_product_2.price_unit, 0)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 2)
        self.assertEquals(line_product_pack.qty_invoiced, 2)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 2)
        self.assertEquals(line_product_1.qty_invoiced, 2)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 4)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        picking2 = sale.picking_ids.filtered(lambda p: p.state == 'assigned')
        self.assertTrue(picking2)
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 88
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 6
        action = picking2.button_validate()
        self.assertEqual(action['res_model'], 'stock.overprocessed.transfer')
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(
            list(set(sale.picking_ids.mapped('state'))), ['done'])
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 2)
        self.assertEquals(line_product_pack.qty_to_invoice, 3)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 90)
        self.assertEquals(line_product_1.qty_invoiced, 2)
        self.assertEquals(line_product_1.qty_to_invoice, 88)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 4)
        self.assertEquals(line_product_2.qty_to_invoice, 6)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 2)
        invoice2 = sale.invoice_ids - invoice
        self.assertEquals(len(invoice2.invoice_line_ids), 4)
        inv_line_product_pack = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 3)
        self.assertEquals(inv_line_product_pack.price_unit, 1)
        inv_line_product_1_qty_3 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 3)
        self.assertTrue(inv_line_product_1_qty_3)
        self.assertEquals(inv_line_product_1_qty_3.price_unit, 0)
        inv_line_product_1_qty_85 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 85)
        self.assertTrue(inv_line_product_1_qty_85)
        self.assertEquals(inv_line_product_1_qty_85.price_unit, 100)
        inv_line_product_2 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 6)
        self.assertEquals(inv_line_product_2.price_unit, 0)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 90)
        self.assertEquals(line_product_1.qty_invoiced, 90)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = picking2.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 4)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, -1)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 89)
        self.assertEquals(line_product_1.qty_invoiced, 90)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_sale_with_packs_totalized_order_partial_extra_qty(self):
        self.update_stock(self.product_1, self.stock_location, 100)
        self.update_stock(self.product_2, self.stock_location, 200)
        product_pack_qty = self.get_stock(
            self.product_pack_order_totalized, self.stock_location)
        self.assertEquals(product_pack_qty, 100)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_order_totalized.id,
                    'product_uom_qty': 5,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_order_totalized)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.price_unit, 1100)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.price_unit, 0)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.price_unit, 0)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 1)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_totalized)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 5)
        self.assertEquals(inv_line_product_pack.price_unit, 1100)
        sale.invoice_ids.unlink()
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_order_totalized)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 5)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 10)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 2
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 4
        action = picking.button_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 2)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 5)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 2)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 4)
        picking2 = sale.picking_ids.filtered(lambda p: p.state == 'assigned')
        self.assertTrue(picking2)
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 88
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 6
        action = picking2.button_validate()
        self.assertEqual(action['res_model'], 'stock.overprocessed.transfer')
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(
            list(set(sale.picking_ids.mapped('state'))), ['done'])
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 5)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 90)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 90)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 10)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEquals(len(invoice.invoice_line_ids), 4)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_totalized)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 5)
        self.assertEquals(inv_line_product_pack.price_unit, 1100)
        inv_line_product_1_qty_5 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 5)
        self.assertTrue(inv_line_product_1_qty_5)
        self.assertEquals(inv_line_product_1_qty_5.price_unit, 0)
        inv_line_product_1_qty_85 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 85)
        self.assertTrue(inv_line_product_1_qty_85)
        self.assertEquals(inv_line_product_1_qty_85.price_unit, 100)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 10)
        self.assertEquals(inv_line_product_2.price_unit, 0)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 90)
        self.assertEquals(line_product_1.qty_invoiced, 90)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = picking2.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 4)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 89)
        self.assertEquals(line_product_1.qty_invoiced, 90)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_sale_with_packs_ignored_order_partial_extra_qty(self):
        self.update_stock(self.product_1, self.stock_location, 100)
        self.update_stock(self.product_2, self.stock_location, 200)
        product_pack_qty = self.get_stock(
            self.product_pack_order_ignored, self.stock_location)
        self.assertEquals(product_pack_qty, 100)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_order_ignored.id,
                    'product_uom_qty': 5,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_order_ignored)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.price_unit, 1)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.price_unit, 0)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.price_unit, 0)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 1)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_ignored)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 5)
        self.assertEquals(inv_line_product_pack.price_unit, 1)
        sale.invoice_ids.unlink()
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_order_ignored)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 5)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 10)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 2
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 4
        action = picking.button_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 2)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 5)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 2)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 4)
        picking2 = sale.picking_ids.filtered(lambda p: p.state == 'assigned')
        self.assertTrue(picking2)
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 88
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 6
        action = picking2.button_validate()
        self.assertEqual(action['res_model'], 'stock.overprocessed.transfer')
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(
            list(set(sale.picking_ids.mapped('state'))), ['done'])
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 5)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 90)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 90)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 10)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEquals(len(invoice.invoice_line_ids), 4)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_ignored)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 5)
        self.assertEquals(inv_line_product_pack.price_unit, 1)
        inv_line_product_1_qty_5 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 5)
        self.assertTrue(inv_line_product_1_qty_5)
        self.assertEquals(inv_line_product_1_qty_5.price_unit, 0)
        inv_line_product_1_qty_85 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 85)
        self.assertTrue(inv_line_product_1_qty_85)
        self.assertEquals(inv_line_product_1_qty_85.price_unit, 100)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 10)
        self.assertEquals(inv_line_product_2.price_unit, 0)
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 5)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 90)
        self.assertEquals(line_product_1.qty_invoiced, 90)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = picking2.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 5)
        self.assertEquals(line_product_pack.qty_delivered, 4)
        self.assertEquals(line_product_pack.qty_invoiced, 5)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 89)
        self.assertEquals(line_product_1.qty_invoiced, 90)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_several_different_packs_detailed_delivery(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        self.update_stock(self.product_3, self.stock_location, 30)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_detail, self.stock_location)
        self.assertEquals(product_pack_qty, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_detail.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_pack_delivery_detail2.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 6)
        line_product_pack1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(line_product_pack1)
        self.assertEquals(line_product_pack1.product_uom_qty, 1)
        self.assertEquals(line_product_pack1.price_unit, 1)
        line_product_1_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 1)
        self.assertTrue(line_product_1_1)
        self.assertEquals(line_product_1_1.price_unit, 100)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.price_unit, 500)
        line_product_pack2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail2)
        self.assertTrue(line_product_pack2)
        self.assertEquals(line_product_pack2.product_uom_qty, 1)
        self.assertEquals(line_product_pack2.price_unit, 1)
        line_product_1_10 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 10)
        self.assertTrue(line_product_1_10)
        self.assertEquals(line_product_1_10.price_unit, 100)
        line_product_3 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_3)
        self.assertTrue(line_product_3)
        self.assertEquals(line_product_3.product_uom_qty, 30)
        self.assertEquals(line_product_3.price_unit, 300)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 4)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertFalse(move_product_pack)
        move_product_1_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 1)
        self.assertTrue(move_product_1_1)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 2)
        move_product_pack2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail2)
        self.assertFalse(move_product_pack2)
        move_product_1_10 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 10)
        self.assertTrue(move_product_1_10)
        move_product_3 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_3)
        self.assertTrue(move_product_3)
        self.assertEquals(move_product_3.product_uom_qty, 30)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(line_product_pack1.product_uom_qty, 1)
        self.assertEquals(line_product_pack1.qty_delivered, 1)
        self.assertEquals(line_product_pack1.qty_invoiced, 0)
        self.assertEquals(line_product_pack1.qty_to_invoice, 1)
        self.assertEquals(line_product_1_1.product_uom_qty, 1)
        self.assertEquals(line_product_1_1.qty_delivered, 1)
        self.assertEquals(line_product_1_1.qty_invoiced, 0)
        self.assertEquals(line_product_1_1.qty_to_invoice, 1)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 2)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 2)
        self.assertEquals(line_product_pack2.product_uom_qty, 1)
        self.assertEquals(line_product_pack2.qty_delivered, 1)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 1)
        self.assertEquals(line_product_1_10.product_uom_qty, 10)
        self.assertEquals(line_product_1_10.qty_delivered, 10)
        self.assertEquals(line_product_1_10.qty_invoiced, 0)
        self.assertEquals(line_product_1_10.qty_to_invoice, 10)
        self.assertEquals(line_product_3.product_uom_qty, 30)
        self.assertEquals(line_product_3.qty_delivered, 30)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 30)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 6)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 1)
        inv_line_product_1_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 1)
        self.assertTrue(inv_line_product_1_1)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 2)
        inv_line_product_pack2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail2)
        self.assertTrue(inv_line_product_pack2)
        self.assertEquals(inv_line_product_pack2.quantity, 1)
        inv_line_product_1_10 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 10)
        self.assertTrue(inv_line_product_1_10)
        inv_line_product_3 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_3)
        self.assertTrue(inv_line_product_3)
        self.assertEquals(inv_line_product_3.quantity, 30)
        self.assertEquals(line_product_pack1.product_uom_qty, 1)
        self.assertEquals(line_product_pack1.qty_delivered, 1)
        self.assertEquals(line_product_pack1.qty_invoiced, 1)
        self.assertEquals(line_product_pack1.qty_to_invoice, 0)
        self.assertEquals(line_product_1_1.product_uom_qty, 1)
        self.assertEquals(line_product_1_1.qty_delivered, 1)
        self.assertEquals(line_product_1_1.qty_invoiced, 1)
        self.assertEquals(line_product_1_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 2)
        self.assertEquals(line_product_2.qty_invoiced, 2)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        self.assertEquals(line_product_pack2.product_uom_qty, 1)
        self.assertEquals(line_product_pack2.qty_delivered, 1)
        self.assertEquals(line_product_pack2.qty_invoiced, 1)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_10.product_uom_qty, 10)
        self.assertEquals(line_product_1_10.qty_delivered, 10)
        self.assertEquals(line_product_1_10.qty_invoiced, 10)
        self.assertEquals(line_product_1_10.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 30)
        self.assertEquals(line_product_3.qty_delivered, 30)
        self.assertEquals(line_product_3.qty_invoiced, 30)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        done_pickings = sale.picking_ids.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1)[0].quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1)[0].quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1)[0].to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack1.product_uom_qty, 1)
        self.assertEquals(line_product_pack1.qty_delivered, 0)
        self.assertEquals(line_product_pack1.qty_invoiced, 1)
        self.assertEquals(line_product_pack1.qty_to_invoice, -1)
        self.assertEquals(line_product_1_1.product_uom_qty, 1)
        self.assertEquals(line_product_1_1.qty_delivered, 0)
        self.assertEquals(line_product_1_1.qty_invoiced, 1)
        self.assertEquals(line_product_1_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 0)
        self.assertEquals(line_product_2.qty_invoiced, 2)
        self.assertEquals(line_product_2.qty_to_invoice, -2)
        self.assertEquals(line_product_pack2.product_uom_qty, 1)
        self.assertEquals(line_product_pack2.qty_delivered, 1)
        self.assertEquals(line_product_pack2.qty_invoiced, 1)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_10.product_uom_qty, 10)
        self.assertEquals(line_product_1_10.qty_delivered, 10)
        self.assertEquals(line_product_1_10.qty_invoiced, 10)
        self.assertEquals(line_product_1_10.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 30)
        self.assertEquals(line_product_3.qty_delivered, 30)
        self.assertEquals(line_product_3.qty_invoiced, 30)
        self.assertEquals(line_product_3.qty_to_invoice, 0)

    def test_several_different_packs_detailed_delivery_partial_complete(self):
        self.update_stock(self.product_1, self.stock_location, 200)
        self.update_stock(self.product_2, self.stock_location, 200)
        self.update_stock(self.product_3, self.stock_location, 300)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_detail, self.stock_location)
        self.assertEquals(product_pack_qty, 100)
        product_pack_qty2 = self.get_stock(
            self.product_pack_delivery_detail2, self.stock_location)
        self.assertEquals(product_pack_qty2, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_detail.id,
                    'product_uom_qty': 5,
                }),
                (0, 0, {
                    'product_id': self.product_pack_delivery_detail2.id,
                    'product_uom_qty': 5,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 6)
        line_product_pack1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(line_product_pack1)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.price_unit, 1)
        line_product_1_5 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 5)
        self.assertTrue(line_product_1_5)
        self.assertEquals(line_product_1_5.price_unit, 100)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.price_unit, 500)
        line_product_pack2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail2)
        self.assertTrue(line_product_pack2)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.price_unit, 1)
        line_product_1_50 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 50)
        self.assertTrue(line_product_1_50)
        self.assertEquals(line_product_1_50.price_unit, 100)
        line_product_3 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_3)
        self.assertTrue(line_product_3)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.price_unit, 300)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 4)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertFalse(move_product_pack)
        move_product_1_5 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 5)
        self.assertTrue(move_product_1_5)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 10)
        move_product_pack2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail2)
        self.assertFalse(move_product_pack2)
        move_product_1_50 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 50)
        self.assertTrue(move_product_1_50)
        move_product_3 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_3)
        self.assertTrue(move_product_3)
        self.assertEquals(move_product_3.product_uom_qty, 150)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.sale_line_id.product_uom_qty == 5).quantity_done = 2
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 4
        action = picking.button_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 2)
        self.assertEquals(line_product_pack1.qty_invoiced, 0)
        self.assertEquals(line_product_pack1.qty_to_invoice, 2)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 2)
        self.assertEquals(line_product_1_5.qty_invoiced, 0)
        self.assertEquals(line_product_1_5.qty_to_invoice, 2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 4)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 0)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 0)
        self.assertEquals(line_product_1_50.qty_invoiced, 0)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 0)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(inv_line_product_pack1)
        self.assertEquals(inv_line_product_pack1.quantity, 2)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 2)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 4)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 2)
        self.assertEquals(line_product_pack1.qty_invoiced, 2)
        self.assertEquals(line_product_pack1.qty_to_invoice, 0)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 2)
        self.assertEquals(line_product_1_5.qty_invoiced, 2)
        self.assertEquals(line_product_1_5.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 4)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 0)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 0)
        self.assertEquals(line_product_1_50.qty_invoiced, 0)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 0)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        picking2 = sale.picking_ids.filtered(lambda p: p.state == 'assigned')
        self.assertTrue(picking2)
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.sale_line_id.product_uom_qty == 5).quantity_done = 3
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 6
        action = picking2.button_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.process()
        self.assertEquals(picking2.state, 'done')
        self.assertEquals(len(sale.picking_ids), 3)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 5)
        self.assertEquals(line_product_pack1.qty_invoiced, 2)
        self.assertEquals(line_product_pack1.qty_to_invoice, 3)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 5)
        self.assertEquals(line_product_1_5.qty_invoiced, 2)
        self.assertEquals(line_product_1_5.qty_to_invoice, 3)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 4)
        self.assertEquals(line_product_2.qty_to_invoice, 6)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 0)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 0)
        self.assertEquals(line_product_1_50.qty_invoiced, 0)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 0)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 2)
        invoice2 = sale.invoice_ids - invoice
        self.assertEquals(len(invoice2.invoice_line_ids), 3)
        inv_line_product_pack1 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(inv_line_product_pack1)
        self.assertEquals(inv_line_product_pack1.quantity, 3)
        inv_line_product_1 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 3)
        inv_line_product_2 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 6)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 5)
        self.assertEquals(line_product_pack1.qty_invoiced, 5)
        self.assertEquals(line_product_pack1.qty_to_invoice, 0)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 5)
        self.assertEquals(line_product_1_5.qty_invoiced, 5)
        self.assertEquals(line_product_1_5.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 0)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 0)
        self.assertEquals(line_product_1_50.qty_invoiced, 0)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 0)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        picking3 = sale.picking_ids.filtered(lambda p: p.state == 'assigned')
        self.assertTrue(picking3)
        picking3.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 50
        picking3.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_3).quantity_done = 150
        action = picking3.button_validate()
        self.assertEquals(action, None)
        self.assertEquals(
            list(set(sale.picking_ids.mapped('state'))), ['done'])
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 5)
        self.assertEquals(line_product_pack1.qty_invoiced, 5)
        self.assertEquals(line_product_pack1.qty_to_invoice, 0)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 5)
        self.assertEquals(line_product_1_5.qty_invoiced, 5)
        self.assertEquals(line_product_1_5.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 5)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 5)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 50)
        self.assertEquals(line_product_1_50.qty_invoiced, 0)
        self.assertEquals(line_product_1_50.qty_to_invoice, 50)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 150)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 150)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 3)
        invoice3 = sale.invoice_ids - invoice - invoice2
        self.assertEquals(len(invoice3.invoice_line_ids), 3)
        inv_line_product_pack2 = invoice3.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail2)
        self.assertTrue(inv_line_product_pack2)
        self.assertEquals(inv_line_product_pack2.quantity, 5)
        inv_line_product_1 = invoice3.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 50)
        inv_line_product_3 = invoice3.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_3)
        self.assertTrue(inv_line_product_3)
        self.assertEquals(inv_line_product_3.quantity, 150)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 5)
        self.assertEquals(line_product_pack1.qty_invoiced, 5)
        self.assertEquals(line_product_pack1.qty_to_invoice, 0)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 5)
        self.assertEquals(line_product_1_5.qty_invoiced, 5)
        self.assertEquals(line_product_1_5.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 5)
        self.assertEquals(line_product_pack2.qty_invoiced, 5)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 50)
        self.assertEquals(line_product_1_50.qty_invoiced, 50)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 150)
        self.assertEquals(line_product_3.qty_invoiced, 150)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        done_pickings = picking2.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 4)
        self.assertEquals(line_product_pack1.qty_invoiced, 5)
        self.assertEquals(line_product_pack1.qty_to_invoice, -1)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 4)
        self.assertEquals(line_product_1_5.qty_invoiced, 5)
        self.assertEquals(line_product_1_5.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 5)
        self.assertEquals(line_product_pack2.qty_invoiced, 5)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 50)
        self.assertEquals(line_product_1_50.qty_invoiced, 50)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 150)
        self.assertEquals(line_product_3.qty_invoiced, 150)
        self.assertEquals(line_product_3.qty_to_invoice, 0)

    def test_several_different_packs_detailed_delivery_partial_incomplete(self):
        self.update_stock(self.product_1, self.stock_location, 200)
        self.update_stock(self.product_2, self.stock_location, 200)
        self.update_stock(self.product_3, self.stock_location, 300)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_detail, self.stock_location)
        self.assertEquals(product_pack_qty, 100)
        product_pack_qty2 = self.get_stock(
            self.product_pack_delivery_detail2, self.stock_location)
        self.assertEquals(product_pack_qty2, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_detail.id,
                    'product_uom_qty': 5,
                }),
                (0, 0, {
                    'product_id': self.product_pack_delivery_detail2.id,
                    'product_uom_qty': 5,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 6)
        line_product_pack1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(line_product_pack1)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.price_unit, 1)
        line_product_1_5 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 5)
        self.assertTrue(line_product_1_5)
        self.assertEquals(line_product_1_5.price_unit, 100)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.price_unit, 500)
        line_product_pack2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail2)
        self.assertTrue(line_product_pack2)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.price_unit, 1)
        line_product_1_50 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 50)
        self.assertTrue(line_product_1_50)
        self.assertEquals(line_product_1_50.price_unit, 100)
        line_product_3 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_3)
        self.assertTrue(line_product_3)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.price_unit, 300)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 4)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertFalse(move_product_pack)
        move_product_1_5 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 5)
        self.assertTrue(move_product_1_5)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 10)
        move_product_pack2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail2)
        self.assertFalse(move_product_pack2)
        move_product_1_50 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 50)
        self.assertTrue(move_product_1_50)
        move_product_3 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_3)
        self.assertTrue(move_product_3)
        self.assertEquals(move_product_3.product_uom_qty, 150)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.sale_line_id.product_uom_qty == 5).quantity_done = 2
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 5
        action = picking.button_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 2)
        self.assertEquals(line_product_pack1.qty_invoiced, 0)
        self.assertEquals(line_product_pack1.qty_to_invoice, 2)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 2)
        self.assertEquals(line_product_1_5.qty_invoiced, 0)
        self.assertEquals(line_product_1_5.qty_to_invoice, 2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 5)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 5)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 0)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 0)
        self.assertEquals(line_product_1_50.qty_invoiced, 0)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 0)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(inv_line_product_pack1)
        self.assertEquals(inv_line_product_pack1.quantity, 2)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 2)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 5)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 2)
        self.assertEquals(line_product_pack1.qty_invoiced, 2)
        self.assertEquals(line_product_pack1.qty_to_invoice, 0)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 2)
        self.assertEquals(line_product_1_5.qty_invoiced, 2)
        self.assertEquals(line_product_1_5.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 5)
        self.assertEquals(line_product_2.qty_invoiced, 5)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 0)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 0)
        self.assertEquals(line_product_1_50.qty_invoiced, 0)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 0)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        picking2 = sale.picking_ids.filtered(lambda p: p.state == 'assigned')
        self.assertTrue(picking2)
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.sale_line_id.product_uom_qty == 5).quantity_done = 3
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 5
        action = picking2.button_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.process()
        self.assertEquals(picking2.state, 'done')
        self.assertEquals(len(sale.picking_ids), 3)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 5)
        self.assertEquals(line_product_pack1.qty_invoiced, 2)
        self.assertEquals(line_product_pack1.qty_to_invoice, 3)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 5)
        self.assertEquals(line_product_1_5.qty_invoiced, 2)
        self.assertEquals(line_product_1_5.qty_to_invoice, 3)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 5)
        self.assertEquals(line_product_2.qty_to_invoice, 5)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 0)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 0)
        self.assertEquals(line_product_1_50.qty_invoiced, 0)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 0)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 2)
        invoice2 = sale.invoice_ids - invoice
        self.assertEquals(len(invoice2.invoice_line_ids), 3)
        inv_line_product_pack1 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(inv_line_product_pack1)
        self.assertEquals(inv_line_product_pack1.quantity, 3)
        inv_line_product_1 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 3)
        inv_line_product_2 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 5)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 5)
        self.assertEquals(line_product_pack1.qty_invoiced, 5)
        self.assertEquals(line_product_pack1.qty_to_invoice, 0)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 5)
        self.assertEquals(line_product_1_5.qty_invoiced, 5)
        self.assertEquals(line_product_1_5.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 0)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 0)
        self.assertEquals(line_product_1_50.qty_invoiced, 0)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 0)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        picking3 = sale.picking_ids.filtered(lambda p: p.state == 'assigned')
        self.assertTrue(picking3)
        picking3.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 50
        picking3.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_3).quantity_done = 150
        action = picking3.button_validate()
        self.assertEquals(action, None)
        self.assertEquals(
            list(set(sale.picking_ids.mapped('state'))), ['done'])
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 5)
        self.assertEquals(line_product_pack1.qty_invoiced, 5)
        self.assertEquals(line_product_pack1.qty_to_invoice, 0)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 5)
        self.assertEquals(line_product_1_5.qty_invoiced, 5)
        self.assertEquals(line_product_1_5.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 5)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 5)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 50)
        self.assertEquals(line_product_1_50.qty_invoiced, 0)
        self.assertEquals(line_product_1_50.qty_to_invoice, 50)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 150)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 150)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 3)
        invoice3 = sale.invoice_ids - invoice - invoice2
        self.assertEquals(len(invoice3.invoice_line_ids), 3)
        inv_line_product_pack2 = invoice3.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail2)
        self.assertTrue(inv_line_product_pack2)
        self.assertEquals(inv_line_product_pack2.quantity, 5)
        inv_line_product_1 = invoice3.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 50)
        inv_line_product_3 = invoice3.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_3)
        self.assertTrue(inv_line_product_3)
        self.assertEquals(inv_line_product_3.quantity, 150)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 5)
        self.assertEquals(line_product_pack1.qty_invoiced, 5)
        self.assertEquals(line_product_pack1.qty_to_invoice, 0)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 5)
        self.assertEquals(line_product_1_5.qty_invoiced, 5)
        self.assertEquals(line_product_1_5.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 5)
        self.assertEquals(line_product_pack2.qty_invoiced, 5)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 50)
        self.assertEquals(line_product_1_50.qty_invoiced, 50)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 150)
        self.assertEquals(line_product_3.qty_invoiced, 150)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        done_pickings = picking2.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 4)
        self.assertEquals(line_product_pack1.qty_invoiced, 5)
        self.assertEquals(line_product_pack1.qty_to_invoice, -1)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 4)
        self.assertEquals(line_product_1_5.qty_invoiced, 5)
        self.assertEquals(line_product_1_5.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 5)
        self.assertEquals(line_product_pack2.qty_invoiced, 5)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 50)
        self.assertEquals(line_product_1_50.qty_invoiced, 50)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 150)
        self.assertEquals(line_product_3.qty_invoiced, 150)
        self.assertEquals(line_product_3.qty_to_invoice, 0)

    def test_several_different_packs_detailed_delivery_partial_extra_qty(self):
        self.update_stock(self.product_1, self.stock_location, 200)
        self.update_stock(self.product_2, self.stock_location, 200)
        self.update_stock(self.product_3, self.stock_location, 300)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_detail, self.stock_location)
        self.assertEquals(product_pack_qty, 100)
        product_pack_qty2 = self.get_stock(
            self.product_pack_delivery_detail2, self.stock_location)
        self.assertEquals(product_pack_qty2, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_detail.id,
                    'product_uom_qty': 5,
                }),
                (0, 0, {
                    'product_id': self.product_pack_delivery_detail2.id,
                    'product_uom_qty': 5,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 6)
        line_product_pack1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(line_product_pack1)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.price_unit, 1)
        line_product_1_5 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 5)
        self.assertTrue(line_product_1_5)
        self.assertEquals(line_product_1_5.price_unit, 100)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.price_unit, 500)
        line_product_pack2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail2)
        self.assertTrue(line_product_pack2)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.price_unit, 1)
        line_product_1_50 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 50)
        self.assertTrue(line_product_1_50)
        self.assertEquals(line_product_1_50.price_unit, 100)
        line_product_3 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_3)
        self.assertTrue(line_product_3)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.price_unit, 300)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 4)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertFalse(move_product_pack)
        move_product_1_5 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 5)
        self.assertTrue(move_product_1_5)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 10)
        move_product_pack2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail2)
        self.assertFalse(move_product_pack2)
        move_product_1_50 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 50)
        self.assertTrue(move_product_1_50)
        move_product_3 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_3)
        self.assertTrue(move_product_3)
        self.assertEquals(move_product_3.product_uom_qty, 150)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.sale_line_id.product_uom_qty == 5).quantity_done = 2
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 4
        action = picking.button_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 2)
        self.assertEquals(line_product_pack1.qty_invoiced, 0)
        self.assertEquals(line_product_pack1.qty_to_invoice, 2)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 2)
        self.assertEquals(line_product_1_5.qty_invoiced, 0)
        self.assertEquals(line_product_1_5.qty_to_invoice, 2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 4)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 0)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 0)
        self.assertEquals(line_product_1_50.qty_invoiced, 0)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 0)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(inv_line_product_pack1)
        self.assertEquals(inv_line_product_pack1.quantity, 2)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 2)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 4)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 2)
        self.assertEquals(line_product_pack1.qty_invoiced, 2)
        self.assertEquals(line_product_pack1.qty_to_invoice, 0)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 2)
        self.assertEquals(line_product_1_5.qty_invoiced, 2)
        self.assertEquals(line_product_1_5.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 4)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 0)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 0)
        self.assertEquals(line_product_1_50.qty_invoiced, 0)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 0)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        picking2 = sale.picking_ids.filtered(lambda p: p.state == 'assigned')
        self.assertTrue(picking2)
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.sale_line_id.product_uom_qty == 5).quantity_done = 88
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 6

        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.sale_line_id.product_uom_qty == 50).quantity_done = 50
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_3).quantity_done = 150
        action = picking2.button_validate()
        self.assertEqual(action['res_model'], 'stock.overprocessed.transfer')
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 5)
        self.assertEquals(line_product_pack1.qty_invoiced, 2)
        self.assertEquals(line_product_pack1.qty_to_invoice, 3)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 90)
        self.assertEquals(line_product_1_5.qty_invoiced, 2)
        self.assertEquals(line_product_1_5.qty_to_invoice, 88)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 4)
        self.assertEquals(line_product_2.qty_to_invoice, 6)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 5)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 5)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 50)
        self.assertEquals(line_product_1_50.qty_invoiced, 0)
        self.assertEquals(line_product_1_50.qty_to_invoice, 50)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 150)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 150)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 2)
        invoice2 = sale.invoice_ids - invoice
        self.assertEquals(len(invoice2.invoice_line_ids), 7)
        inv_line_product_pack1 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(inv_line_product_pack1)
        self.assertEquals(inv_line_product_pack1.quantity, 3)
        inv_line_product_1_3 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 3)
        self.assertTrue(inv_line_product_1_3)
        inv_line_product_1_85 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 85)
        self.assertTrue(inv_line_product_1_85)
        inv_line_product_2 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 6)
        inv_line_product_pack2 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail2)
        self.assertTrue(inv_line_product_pack2)
        self.assertEquals(inv_line_product_pack2.quantity, 5)
        inv_line_product_1_50 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 50)
        self.assertTrue(inv_line_product_1_50)
        inv_line_product_3 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_3)
        self.assertTrue(inv_line_product_3)
        self.assertEquals(inv_line_product_3.quantity, 150)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 5)
        self.assertEquals(line_product_pack1.qty_invoiced, 5)
        self.assertEquals(line_product_pack1.qty_to_invoice, 0)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 90)
        self.assertEquals(line_product_1_5.qty_invoiced, 90)
        self.assertEquals(line_product_1_5.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 5)
        self.assertEquals(line_product_pack2.qty_invoiced, 5)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 50)
        self.assertEquals(line_product_1_50.qty_invoiced, 50)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 150)
        self.assertEquals(line_product_3.qty_invoiced, 150)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(
            list(set(sale.picking_ids.mapped('state'))), ['done'])
        done_pickings = picking2.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1
            and m.quantity == 88).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1
            and m.product_uom_qty == 1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1
            and m.product_uom_qty == 1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2
            and m.product_uom_qty == 2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2
            and m.product_uom_qty == 2).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1
            and m.product_uom_qty == 50).quantity_done = 0
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_3).quantity_done = 0
        return_pick.action_done()
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 4)
        self.assertEquals(line_product_pack1.qty_invoiced, 5)
        self.assertEquals(line_product_pack1.qty_to_invoice, -1)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 89)
        self.assertEquals(line_product_1_5.qty_invoiced, 90)
        self.assertEquals(line_product_1_5.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 5)
        self.assertEquals(line_product_pack2.qty_invoiced, 5)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 50)
        self.assertEquals(line_product_1_50.qty_invoiced, 50)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 150)
        self.assertEquals(line_product_3.qty_invoiced, 150)
        self.assertEquals(line_product_3.qty_to_invoice, 0)

    def test_several_different_packs_totalized_delivery_partial_extra_qty(self):
        self.update_stock(self.product_1, self.stock_location, 200)
        self.update_stock(self.product_2, self.stock_location, 200)
        self.update_stock(self.product_3, self.stock_location, 300)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_totalized, self.stock_location)
        self.assertEquals(product_pack_qty, 100)
        product_pack_qty2 = self.get_stock(
            self.product_pack_delivery_totalized2, self.stock_location)
        self.assertEquals(product_pack_qty2, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_totalized.id,
                    'product_uom_qty': 5,
                }),
                (0, 0, {
                    'product_id': self.product_pack_delivery_totalized2.id,
                    'product_uom_qty': 5,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 6)
        line_product_pack1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized)
        self.assertTrue(line_product_pack1)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.price_unit, 1100)
        line_product_1_5 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 5)
        self.assertTrue(line_product_1_5)
        self.assertEquals(line_product_1_5.price_unit, 0)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.price_unit, 0)
        line_product_pack2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized2)
        self.assertTrue(line_product_pack2)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.price_unit, 10000)
        line_product_1_50 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 50)
        self.assertTrue(line_product_1_50)
        self.assertEquals(line_product_1_50.price_unit, 0)
        line_product_3 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_3)
        self.assertTrue(line_product_3)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.price_unit, 0)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 4)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized)
        self.assertFalse(move_product_pack)
        move_product_1_5 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 5)
        self.assertTrue(move_product_1_5)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 10)
        move_product_pack2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized2)
        self.assertFalse(move_product_pack2)
        move_product_1_50 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 50)
        self.assertTrue(move_product_1_50)
        move_product_3 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_3)
        self.assertTrue(move_product_3)
        self.assertEquals(move_product_3.product_uom_qty, 150)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.sale_line_id.product_uom_qty == 5).quantity_done = 2
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 4
        action = picking.button_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 2)
        self.assertEquals(line_product_pack1.qty_invoiced, 0)
        self.assertEquals(line_product_pack1.qty_to_invoice, 2)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 2)
        self.assertEquals(line_product_1_5.qty_invoiced, 0)
        self.assertEquals(line_product_1_5.qty_to_invoice, 2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 4)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 0)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 0)
        self.assertEquals(line_product_1_50.qty_invoiced, 0)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 0)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized)
        self.assertTrue(inv_line_product_pack1)
        self.assertEquals(inv_line_product_pack1.quantity, 2)
        self.assertEquals(inv_line_product_pack1.price_unit, 1100)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 2)
        self.assertEquals(inv_line_product_1.price_unit, 0)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 4)
        self.assertEquals(inv_line_product_2.price_unit, 0)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 2)
        self.assertEquals(line_product_pack1.qty_invoiced, 2)
        self.assertEquals(line_product_pack1.qty_to_invoice, 0)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 2)
        self.assertEquals(line_product_1_5.qty_invoiced, 2)
        self.assertEquals(line_product_1_5.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 4)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 0)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 0)
        self.assertEquals(line_product_1_50.qty_invoiced, 0)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 0)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        picking2 = sale.picking_ids.filtered(lambda p: p.state == 'assigned')
        self.assertTrue(picking2)
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.sale_line_id.product_uom_qty == 5).quantity_done = 88
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 6
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.sale_line_id.product_uom_qty == 50).quantity_done = 50
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_3).quantity_done = 150
        action = picking2.button_validate()
        self.assertEqual(action['res_model'], 'stock.overprocessed.transfer')
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 5)
        self.assertEquals(line_product_pack1.qty_invoiced, 2)
        self.assertEquals(line_product_pack1.qty_to_invoice, 3)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 90)
        self.assertEquals(line_product_1_5.qty_invoiced, 2)
        self.assertEquals(line_product_1_5.qty_to_invoice, 88)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 4)
        self.assertEquals(line_product_2.qty_to_invoice, 6)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 5)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 5)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 50)
        self.assertEquals(line_product_1_50.qty_invoiced, 0)
        self.assertEquals(line_product_1_50.qty_to_invoice, 50)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 150)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 150)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 2)
        invoice2 = sale.invoice_ids - invoice
        self.assertEquals(len(invoice2.invoice_line_ids), 7)
        inv_line_product_pack1 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized)
        self.assertTrue(inv_line_product_pack1)
        self.assertEquals(inv_line_product_pack1.quantity, 3)
        self.assertEquals(inv_line_product_pack1.price_unit, 1100)
        inv_line_product_1_3 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 3)
        self.assertTrue(inv_line_product_1_3)
        self.assertEquals(inv_line_product_1_3.price_unit, 0)
        inv_line_product_1_85 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 85)
        self.assertTrue(inv_line_product_1_85)
        self.assertEquals(inv_line_product_1_85.price_unit, 100)
        inv_line_product_2 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 6)
        self.assertEquals(inv_line_product_2.price_unit, 0)
        inv_line_product_pack2 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized2)
        self.assertTrue(inv_line_product_pack2)
        self.assertEquals(inv_line_product_pack2.quantity, 5)
        self.assertEquals(inv_line_product_pack2.price_unit, 10000)
        inv_line_product_1_50 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 50)
        self.assertTrue(inv_line_product_1_50)
        self.assertEquals(inv_line_product_1_50.price_unit, 0)
        inv_line_product_3 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_3)
        self.assertTrue(inv_line_product_3)
        self.assertEquals(inv_line_product_3.quantity, 150)
        self.assertEquals(inv_line_product_3.price_unit, 0)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 5)
        self.assertEquals(line_product_pack1.qty_invoiced, 5)
        self.assertEquals(line_product_pack1.qty_to_invoice, 0)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 90)
        self.assertEquals(line_product_1_5.qty_invoiced, 90)
        self.assertEquals(line_product_1_5.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 5)
        self.assertEquals(line_product_pack2.qty_invoiced, 5)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 50)
        self.assertEquals(line_product_1_50.qty_invoiced, 50)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 150)
        self.assertEquals(line_product_3.qty_invoiced, 150)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(
            list(set(sale.picking_ids.mapped('state'))), ['done'])
        done_pickings = picking2.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1
            and m.quantity == 88).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1
            and m.product_uom_qty == 1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1
            and m.product_uom_qty == 1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2
            and m.product_uom_qty == 2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2
            and m.product_uom_qty == 2).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1
            and m.product_uom_qty == 50).quantity_done = 0
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_3).quantity_done = 0
        return_pick.action_done()
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 4)
        self.assertEquals(line_product_pack1.qty_invoiced, 5)
        self.assertEquals(line_product_pack1.qty_to_invoice, -1)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 89)
        self.assertEquals(line_product_1_5.qty_invoiced, 90)
        self.assertEquals(line_product_1_5.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 5)
        self.assertEquals(line_product_pack2.qty_invoiced, 5)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 50)
        self.assertEquals(line_product_1_50.qty_invoiced, 50)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 150)
        self.assertEquals(line_product_3.qty_invoiced, 150)
        self.assertEquals(line_product_3.qty_to_invoice, 0)

    def test_several_different_packs_ignored_delivery_partial_extra_qty(self):
        self.update_stock(self.product_1, self.stock_location, 200)
        self.update_stock(self.product_2, self.stock_location, 200)
        self.update_stock(self.product_3, self.stock_location, 300)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_ignored, self.stock_location)
        self.assertEquals(product_pack_qty, 100)
        product_pack_qty2 = self.get_stock(
            self.product_pack_delivery_ignored2, self.stock_location)
        self.assertEquals(product_pack_qty2, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_ignored.id,
                    'product_uom_qty': 5,
                }),
                (0, 0, {
                    'product_id': self.product_pack_delivery_ignored2.id,
                    'product_uom_qty': 5,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 6)
        line_product_pack1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored)
        self.assertTrue(line_product_pack1)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.price_unit, 1)
        line_product_1_5 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 5)
        self.assertTrue(line_product_1_5)
        self.assertEquals(line_product_1_5.price_unit, 0)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.price_unit, 0)
        line_product_pack2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored2)
        self.assertTrue(line_product_pack2)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.price_unit, 1)
        line_product_1_50 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 50)
        self.assertTrue(line_product_1_50)
        self.assertEquals(line_product_1_50.price_unit, 0)
        line_product_3 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_3)
        self.assertTrue(line_product_3)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.price_unit, 0)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 4)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored)
        self.assertFalse(move_product_pack)
        move_product_1_5 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 5)
        self.assertTrue(move_product_1_5)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 10)
        move_product_pack2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored2)
        self.assertFalse(move_product_pack2)
        move_product_1_50 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.product_uom_qty == 50)
        self.assertTrue(move_product_1_50)
        move_product_3 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_3)
        self.assertTrue(move_product_3)
        self.assertEquals(move_product_3.product_uom_qty, 150)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.sale_line_id.product_uom_qty == 5).quantity_done = 2
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 4
        action = picking.button_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 2)
        self.assertEquals(line_product_pack1.qty_invoiced, 0)
        self.assertEquals(line_product_pack1.qty_to_invoice, 2)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 2)
        self.assertEquals(line_product_1_5.qty_invoiced, 0)
        self.assertEquals(line_product_1_5.qty_to_invoice, 2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 4)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 0)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 0)
        self.assertEquals(line_product_1_50.qty_invoiced, 0)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 0)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored)
        self.assertTrue(inv_line_product_pack1)
        self.assertEquals(inv_line_product_pack1.quantity, 2)
        self.assertEquals(inv_line_product_pack1.price_unit, 1)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 2)
        self.assertEquals(inv_line_product_1.price_unit, 0)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 4)
        self.assertEquals(inv_line_product_2.price_unit, 0)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 2)
        self.assertEquals(line_product_pack1.qty_invoiced, 2)
        self.assertEquals(line_product_pack1.qty_to_invoice, 0)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 2)
        self.assertEquals(line_product_1_5.qty_invoiced, 2)
        self.assertEquals(line_product_1_5.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 4)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 0)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 0)
        self.assertEquals(line_product_1_50.qty_invoiced, 0)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 0)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        picking2 = sale.picking_ids.filtered(lambda p: p.state == 'assigned')
        self.assertTrue(picking2)
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.sale_line_id.product_uom_qty == 5).quantity_done = 88
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 6
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.sale_line_id.product_uom_qty == 50).quantity_done = 50
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_3).quantity_done = 150
        action = picking2.button_validate()
        self.assertEqual(action['res_model'], 'stock.overprocessed.transfer')
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 5)
        self.assertEquals(line_product_pack1.qty_invoiced, 2)
        self.assertEquals(line_product_pack1.qty_to_invoice, 3)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 90)
        self.assertEquals(line_product_1_5.qty_invoiced, 2)
        self.assertEquals(line_product_1_5.qty_to_invoice, 88)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 4)
        self.assertEquals(line_product_2.qty_to_invoice, 6)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 5)
        self.assertEquals(line_product_pack2.qty_invoiced, 0)
        self.assertEquals(line_product_pack2.qty_to_invoice, 5)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 50)
        self.assertEquals(line_product_1_50.qty_invoiced, 0)
        self.assertEquals(line_product_1_50.qty_to_invoice, 50)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 150)
        self.assertEquals(line_product_3.qty_invoiced, 0)
        self.assertEquals(line_product_3.qty_to_invoice, 150)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 2)
        invoice2 = sale.invoice_ids - invoice
        self.assertEquals(len(invoice2.invoice_line_ids), 7)
        inv_line_product_pack1 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored)
        self.assertTrue(inv_line_product_pack1)
        self.assertEquals(inv_line_product_pack1.quantity, 3)
        self.assertEquals(inv_line_product_pack1.price_unit, 1)
        inv_line_product_1_3 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 3)
        self.assertTrue(inv_line_product_1_3)
        self.assertEquals(inv_line_product_1_3.price_unit, 0)
        inv_line_product_1_85 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 85)
        self.assertTrue(inv_line_product_1_85)
        self.assertEquals(inv_line_product_1_85.price_unit, 100)
        inv_line_product_2 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 6)
        self.assertEquals(inv_line_product_2.price_unit, 0)
        inv_line_product_pack2 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored2)
        self.assertTrue(inv_line_product_pack2)
        self.assertEquals(inv_line_product_pack2.quantity, 5)
        self.assertEquals(inv_line_product_pack2.price_unit, 1)
        inv_line_product_1_50 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 50)
        self.assertTrue(inv_line_product_1_50)
        self.assertEquals(inv_line_product_1_50.price_unit, 0)
        inv_line_product_3 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_3)
        self.assertTrue(inv_line_product_3)
        self.assertEquals(inv_line_product_3.quantity, 150)
        self.assertEquals(inv_line_product_3.price_unit, 0)
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 5)
        self.assertEquals(line_product_pack1.qty_invoiced, 5)
        self.assertEquals(line_product_pack1.qty_to_invoice, 0)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 90)
        self.assertEquals(line_product_1_5.qty_invoiced, 90)
        self.assertEquals(line_product_1_5.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 5)
        self.assertEquals(line_product_pack2.qty_invoiced, 5)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 50)
        self.assertEquals(line_product_1_50.qty_invoiced, 50)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 150)
        self.assertEquals(line_product_3.qty_invoiced, 150)
        self.assertEquals(line_product_3.qty_to_invoice, 0)
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(
            list(set(sale.picking_ids.mapped('state'))), ['done'])
        done_pickings = picking2.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1
            and m.quantity == 88).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1
            and m.product_uom_qty == 1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1
            and m.product_uom_qty == 1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2
            and m.product_uom_qty == 2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2
            and m.product_uom_qty == 2).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1
            and m.product_uom_qty == 50).quantity_done = 0
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_3).quantity_done = 0
        return_pick.action_done()
        self.assertEquals(line_product_pack1.product_uom_qty, 5)
        self.assertEquals(line_product_pack1.qty_delivered, 4)
        self.assertEquals(line_product_pack1.qty_invoiced, 5)
        self.assertEquals(line_product_pack1.qty_to_invoice, -1)
        self.assertEquals(line_product_1_5.product_uom_qty, 5)
        self.assertEquals(line_product_1_5.qty_delivered, 89)
        self.assertEquals(line_product_1_5.qty_invoiced, 90)
        self.assertEquals(line_product_1_5.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)
        self.assertEquals(line_product_pack2.product_uom_qty, 5)
        self.assertEquals(line_product_pack2.qty_delivered, 5)
        self.assertEquals(line_product_pack2.qty_invoiced, 5)
        self.assertEquals(line_product_pack2.qty_to_invoice, 0)
        self.assertEquals(line_product_1_50.product_uom_qty, 50)
        self.assertEquals(line_product_1_50.qty_delivered, 50)
        self.assertEquals(line_product_1_50.qty_invoiced, 50)
        self.assertEquals(line_product_1_50.qty_to_invoice, 0)
        self.assertEquals(line_product_3.product_uom_qty, 150)
        self.assertEquals(line_product_3.qty_delivered, 150)
        self.assertEquals(line_product_3.qty_invoiced, 150)
        self.assertEquals(line_product_3.qty_to_invoice, 0)

    def test_no_packs(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 5,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 10,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 2)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.price_unit, 100)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.price_unit, 500)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 5)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 10)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 5)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 5)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 10)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 2)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 5)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 10)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 5)
        self.assertEquals(line_product_1.qty_invoiced, 5)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = sale.picking_ids.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 4)
        self.assertEquals(line_product_1.qty_invoiced, 5)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10 - 2)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_no_packs_partial(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_detail, self.stock_location)
        self.assertEquals(product_pack_qty, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 5,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 10,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 2)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.price_unit, 100)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.price_unit, 500)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 5)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 10)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 2
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 4
        action = picking.button_validate()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.process()
        self.assertEquals(picking.state, 'done')
        self.assertEquals(len(sale.picking_ids), 2)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 2)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 2)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 4)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 2)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 2)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 4)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 2)
        self.assertEquals(line_product_1.qty_invoiced, 2)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 4)
        self.assertEquals(line_product_2.qty_invoiced, 4)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        picking2 = sale.picking_ids.filtered(lambda p: p.state == 'assigned')
        self.assertTrue(picking2)
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 3
        picking2.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 6
        action = picking2.button_validate()
        self.assertEquals(action, None)
        self.assertEquals(
            list(set(sale.picking_ids.mapped('state'))), ['done'])
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 5)
        self.assertEquals(line_product_1.qty_invoiced, 2)
        self.assertEquals(line_product_1.qty_to_invoice, 3)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 4)
        self.assertEquals(line_product_2.qty_to_invoice, 6)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 2)
        invoice2 = sale.invoice_ids - invoice
        self.assertEquals(len(invoice2.invoice_line_ids), 2)
        inv_line_product_1 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 3)
        inv_line_product_2 = invoice2.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 6)
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 5)
        self.assertEquals(line_product_1.qty_invoiced, 5)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = picking2.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_1.product_uom_qty, 5)
        self.assertEquals(line_product_1.qty_delivered, 4)
        self.assertEquals(line_product_1.qty_invoiced, 5)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 10)
        self.assertEquals(line_product_2.qty_delivered, 10 - 2)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_sale_with_pack_delivery_detail_discount(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_detail, self.stock_location)
        self.assertEquals(product_pack_qty, 10)
        pack_lines = self.product_pack_delivery_detail.pack_line_ids
        pack_line_product_1 = pack_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        pack_line_product_1.sale_discount = 5
        pack_line_product_2 = pack_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        pack_line_product_2.sale_discount = 10
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_detail.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.price_unit, 1)
        self.assertEquals(line_product_pack.discount, 0)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.price_unit, 100)
        self.assertEquals(line_product_1.discount, 5)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.price_unit, 500)
        self.assertEquals(line_product_2.discount, 10)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 2)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 1)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 1)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 1)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 2)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 2)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 1)
        self.assertEquals(inv_line_product_pack.price_unit, 1)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 1)
        self.assertEquals(inv_line_product_1.price_unit, 100)
        self.assertEquals(inv_line_product_1.discount, 5)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 2)
        self.assertEquals(inv_line_product_2.price_unit, 500)
        self.assertEquals(inv_line_product_2.discount, 10)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 1)
        self.assertEquals(line_product_pack.qty_invoiced, 1)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 1)
        self.assertEquals(line_product_1.qty_invoiced, 1)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 2)
        self.assertEquals(line_product_2.qty_invoiced, 2)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = sale.picking_ids.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 0)
        self.assertEquals(line_product_pack.qty_invoiced, 1)
        self.assertEquals(line_product_pack.qty_to_invoice, -1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 0)
        self.assertEquals(line_product_1.qty_invoiced, 1)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 0)
        self.assertEquals(line_product_2.qty_invoiced, 2)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_sale_with_pack_delivery_detail_discount_extra_qty(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_detail, self.stock_location)
        self.assertEquals(product_pack_qty, 10)
        pack_lines = self.product_pack_delivery_detail.pack_line_ids
        pack_line_product_1 = pack_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        pack_line_product_1.sale_discount = 5
        pack_line_product_2 = pack_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        pack_line_product_2.sale_discount = 10
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_detail.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.price_unit, 1)
        self.assertEquals(line_product_pack.discount, 0)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.price_unit, 100)
        self.assertEquals(line_product_1.discount, 5)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.price_unit, 500)
        self.assertEquals(line_product_2.discount, 10)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 2)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 1
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 10
        action = picking.button_validate()
        self.assertEqual(action['res_model'], 'stock.overprocessed.transfer')
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(
            list(set(sale.picking_ids.mapped('state'))), ['done'])
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 1)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 1)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 1)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 10)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 4)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 1)
        self.assertEquals(inv_line_product_pack.price_unit, 1)
        self.assertEquals(inv_line_product_pack.discount, 0)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 1)
        self.assertEquals(inv_line_product_1.price_unit, 100)
        self.assertEquals(inv_line_product_1.discount, 5)
        inv_line_product_2_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2 and ln.discount == 10)
        self.assertTrue(inv_line_product_2_pack)
        self.assertEquals(inv_line_product_2_pack.quantity, 2)
        self.assertEquals(inv_line_product_2_pack.price_unit, 500)
        self.assertEquals(inv_line_product_2_pack.discount, 10)
        inv_line_product_2_extra_qty = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2 and ln.discount == 0)
        self.assertTrue(inv_line_product_2_extra_qty)
        self.assertEquals(inv_line_product_2_extra_qty.quantity, 8)
        self.assertEquals(inv_line_product_2_extra_qty.price_unit, 500)
        self.assertEquals(inv_line_product_2_extra_qty.discount, 0)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 1)
        self.assertEquals(line_product_pack.qty_invoiced, 1)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 1)
        self.assertEquals(line_product_1.qty_invoiced, 1)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = sale.picking_ids.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 0)
        self.assertEquals(line_product_pack.qty_invoiced, 1)
        self.assertEquals(line_product_pack.qty_to_invoice, -1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 0)
        self.assertEquals(line_product_1.qty_invoiced, 1)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_sale_with_pack_delivery_totalized_discount(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_totalized, self.stock_location)
        self.assertEquals(product_pack_qty, 10)
        pack_lines = self.product_pack_delivery_totalized.pack_line_ids
        pack_line_product_1 = pack_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        pack_line_product_1.sale_discount = 5
        pack_line_product_2 = pack_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        pack_line_product_2.sale_discount = 10
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_totalized.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        price_pack = 1 * 100 * (1 - 5 / 100) + 2 * 500 * (1 - 10 / 100)
        self.assertEquals(line_product_pack.price_unit, price_pack)
        self.assertEquals(line_product_pack.discount, 0)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.price_unit, 0)
        self.assertEquals(line_product_1.discount, 0)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.price_unit, 0)
        self.assertEquals(line_product_2.discount, 0)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 2)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 1)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 1)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 1)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 2)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 2)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 1)
        self.assertEquals(inv_line_product_pack.discount, 0)
        self.assertEquals(inv_line_product_pack.price_unit, price_pack)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 1)
        self.assertEquals(inv_line_product_1.discount, 0)
        self.assertEquals(inv_line_product_1.price_unit, 0)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 2)
        self.assertEquals(inv_line_product_2.discount, 0)
        self.assertEquals(inv_line_product_2.price_unit, 0)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 1)
        self.assertEquals(line_product_pack.qty_invoiced, 1)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 1)
        self.assertEquals(line_product_1.qty_invoiced, 1)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 2)
        self.assertEquals(line_product_2.qty_invoiced, 2)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = sale.picking_ids.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 0)
        self.assertEquals(line_product_pack.qty_invoiced, 1)
        self.assertEquals(line_product_pack.qty_to_invoice, -1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 0)
        self.assertEquals(line_product_1.qty_invoiced, 1)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 0)
        self.assertEquals(line_product_2.qty_invoiced, 2)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_sale_with_pack_delivery_totalized_discount_extra_qty(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_totalized, self.stock_location)
        self.assertEquals(product_pack_qty, 10)
        pack_lines = self.product_pack_delivery_totalized.pack_line_ids
        pack_line_product_1 = pack_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        pack_line_product_1.sale_discount = 5
        pack_line_product_2 = pack_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        pack_line_product_2.sale_discount = 10
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_totalized.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        price_pack = 1 * 100 * (1 - 5 / 100) + 2 * 500 * (1 - 10 / 100)
        self.assertEquals(line_product_pack.price_unit, price_pack)
        self.assertEquals(line_product_pack.discount, 0)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.price_unit, 0)
        self.assertEquals(line_product_1.discount, 0)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.price_unit, 0)
        self.assertEquals(line_product_2.discount, 0)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 2)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 1
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 10
        action = picking.button_validate()
        self.assertEqual(action['res_model'], 'stock.overprocessed.transfer')
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(
            list(set(sale.picking_ids.mapped('state'))), ['done'])
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 1)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 1)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 1)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 10)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 4)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 1)
        self.assertEquals(inv_line_product_pack.price_unit, price_pack)
        self.assertEquals(inv_line_product_pack.discount, 0)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 1)
        self.assertEquals(inv_line_product_1.price_unit, 0)
        self.assertEquals(inv_line_product_1.discount, 0)
        inv_line_product_2_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2 and ln.price_unit == 0)
        self.assertTrue(inv_line_product_2_pack)
        self.assertEquals(inv_line_product_2_pack.quantity, 2)
        self.assertEquals(inv_line_product_2_pack.discount, 0)
        inv_line_product_2_extra_qty = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2
            and ln.price_unit == 500)
        self.assertTrue(inv_line_product_2_extra_qty)
        self.assertEquals(inv_line_product_2_extra_qty.quantity, 8)
        self.assertEquals(inv_line_product_2_extra_qty.discount, 0)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 1)
        self.assertEquals(line_product_pack.qty_invoiced, 1)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 1)
        self.assertEquals(line_product_1.qty_invoiced, 1)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = sale.picking_ids.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 0)
        self.assertEquals(line_product_pack.qty_invoiced, 1)
        self.assertEquals(line_product_pack.qty_to_invoice, -1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 0)
        self.assertEquals(line_product_1.qty_invoiced, 1)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_sale_with_pack_delivery_ignored_discount(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_ignored, self.stock_location)
        self.assertEquals(product_pack_qty, 10)
        pack_lines = self.product_pack_delivery_ignored.pack_line_ids
        pack_line_product_1 = pack_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        pack_line_product_1.sale_discount = 5
        pack_line_product_2 = pack_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        pack_line_product_2.sale_discount = 10
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_ignored.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.price_unit, 1)
        self.assertEquals(line_product_pack.discount, 0)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.price_unit, 0)
        self.assertEquals(line_product_1.discount, 0)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.price_unit, 0)
        self.assertEquals(line_product_2.discount, 0)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 2)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 1)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 1)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 1)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 2)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 2)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 1)
        self.assertEquals(inv_line_product_pack.discount, 0)
        self.assertEquals(inv_line_product_pack.price_unit, 1)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 1)
        self.assertEquals(inv_line_product_1.discount, 0)
        self.assertEquals(inv_line_product_1.price_unit, 0)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 2)
        self.assertEquals(inv_line_product_2.discount, 0)
        self.assertEquals(inv_line_product_2.price_unit, 0)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 1)
        self.assertEquals(line_product_pack.qty_invoiced, 1)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 1)
        self.assertEquals(line_product_1.qty_invoiced, 1)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 2)
        self.assertEquals(line_product_2.qty_invoiced, 2)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = sale.picking_ids.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 0)
        self.assertEquals(line_product_pack.qty_invoiced, 1)
        self.assertEquals(line_product_pack.qty_to_invoice, -1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 0)
        self.assertEquals(line_product_1.qty_invoiced, 1)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 0)
        self.assertEquals(line_product_2.qty_invoiced, 2)
        self.assertEquals(line_product_2.qty_to_invoice, -2)

    def test_sale_with_pack_delivery_ignored_discount_extra_qty(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_ignored, self.stock_location)
        self.assertEquals(product_pack_qty, 10)
        pack_lines = self.product_pack_delivery_ignored.pack_line_ids
        pack_line_product_1 = pack_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        pack_line_product_1.sale_discount = 5
        pack_line_product_2 = pack_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        pack_line_product_2.sale_discount = 10
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_ignored.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored)
        self.assertTrue(line_product_pack)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.price_unit, 1)
        self.assertEquals(line_product_pack.discount, 0)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.price_unit, 0)
        self.assertEquals(line_product_1.discount, 0)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.price_unit, 0)
        self.assertEquals(line_product_2.discount, 0)
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 2)
        move_product_pack = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = picking.move_lines.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 2)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 1
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 10
        action = picking.button_validate()
        self.assertEqual(action['res_model'], 'stock.overprocessed.transfer')
        wizard = self.env[action['res_model']].browse(action['res_id'])
        wizard.action_confirm()
        self.assertEquals(
            list(set(sale.picking_ids.mapped('state'))), ['done'])
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 1)
        self.assertEquals(line_product_pack.qty_invoiced, 0)
        self.assertEquals(line_product_pack.qty_to_invoice, 1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 1)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        self.assertEquals(line_product_1.qty_to_invoice, 1)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEquals(line_product_2.qty_to_invoice, 10)
        sale.action_invoice_create()
        self.assertEquals(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEquals(len(invoice.invoice_line_ids), 4)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored)
        self.assertTrue(inv_line_product_pack)
        self.assertEquals(inv_line_product_pack.quantity, 1)
        self.assertEquals(inv_line_product_pack.price_unit, 1)
        self.assertEquals(inv_line_product_pack.discount, 0)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 1)
        self.assertEquals(inv_line_product_1.price_unit, 0)
        self.assertEquals(inv_line_product_1.discount, 0)
        inv_line_product_2_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2 and ln.price_unit == 0)
        self.assertTrue(inv_line_product_2_pack)
        self.assertEquals(inv_line_product_2_pack.quantity, 2)
        self.assertEquals(inv_line_product_2_pack.discount, 0)
        inv_line_product_2_extra_qty = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2
            and ln.price_unit == 500)
        self.assertTrue(inv_line_product_2_extra_qty)
        self.assertEquals(inv_line_product_2_extra_qty.quantity, 8)
        self.assertEquals(inv_line_product_2_extra_qty.discount, 0)
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 1)
        self.assertEquals(line_product_pack.qty_invoiced, 1)
        self.assertEquals(line_product_pack.qty_to_invoice, 0)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 1)
        self.assertEquals(line_product_1.qty_invoiced, 1)
        self.assertEquals(line_product_1.qty_to_invoice, 0)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 10)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, 0)
        done_pickings = sale.picking_ids.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_pickings.ids,
            active_id=done_pickings.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).quantity_done = 2
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_2).to_refund = True
        return_pick.action_done()
        self.assertEquals(line_product_pack.product_uom_qty, 1)
        self.assertEquals(line_product_pack.qty_delivered, 0)
        self.assertEquals(line_product_pack.qty_invoiced, 1)
        self.assertEquals(line_product_pack.qty_to_invoice, -1)
        self.assertEquals(line_product_1.product_uom_qty, 1)
        self.assertEquals(line_product_1.qty_delivered, 0)
        self.assertEquals(line_product_1.qty_invoiced, 1)
        self.assertEquals(line_product_1.qty_to_invoice, -1)
        self.assertEquals(line_product_2.product_uom_qty, 2)
        self.assertEquals(line_product_2.qty_delivered, 8)
        self.assertEquals(line_product_2.qty_invoiced, 10)
        self.assertEquals(line_product_2.qty_to_invoice, -2)
