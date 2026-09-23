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
        })
        self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
        })

    def get_stock(self, product, location):
        return product.with_context(location=location.id).qty_available

    def update_stock(self, product, location, qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'product_tmpl_id': product.product_tmpl_id.id,
            'new_quantity': qty,
        })
        wizard.change_product_qty()
        product_qty = self.get_stock(product, location)
        self.assertEqual(product_qty, qty)

    def test_sale_with_pack_delivery_detail(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_detail, self.stock_location)
        self.assertEqual(product_pack_qty, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_detail.id,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.assertEqual(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(line_product_pack)
        self.assertEqual(line_product_pack.product_uom_qty, 1)
        self.assertEqual(line_product_pack.price_unit, 1)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEqual(line_product_1.product_uom_qty, 1)
        self.assertEqual(line_product_1.price_unit, 100)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEqual(line_product_2.product_uom_qty, 2)
        self.assertEqual(line_product_2.price_unit, 500)
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEqual(len(picking.move_ids), 2)
        move_product_pack = picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEqual(move_product_1.product_uom_qty, 1)
        move_product_2 = picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEqual(move_product_2.product_uom_qty, 2)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity_done = move.product_uom_qty
        picking._action_done()
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(line_product_pack.product_uom_qty, 1)
        self.assertEqual(line_product_pack.qty_delivered, 0)
        self.assertEqual(line_product_pack.qty_invoiced, 0)
        self.assertEqual(line_product_pack.qty_to_invoice, 0)
        self.assertEqual(line_product_1.product_uom_qty, 1)
        self.assertEqual(line_product_1.qty_delivered, 1)
        self.assertEqual(line_product_1.qty_invoiced, 0)
        self.assertEqual(line_product_1.qty_to_invoice, 1)
        self.assertEqual(line_product_2.product_uom_qty, 2)
        self.assertEqual(line_product_2.qty_delivered, 2)
        self.assertEqual(line_product_2.qty_invoiced, 0)
        self.assertEqual(line_product_2.qty_to_invoice, 2)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(sale)
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEqual(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEqual(inv_line_product_pack.quantity, 1)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEqual(inv_line_product_1.quantity, 1)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEqual(inv_line_product_2.quantity, 2)
        self.assertEqual(line_product_pack.product_uom_qty, 1)
        self.assertEqual(line_product_pack.qty_delivered, 1)
        self.assertEqual(line_product_pack.qty_invoiced, 1)
        self.assertEqual(line_product_pack.qty_to_invoice, 0)
        self.assertEqual(line_product_1.product_uom_qty, 1)
        self.assertEqual(line_product_1.qty_delivered, 1)
        self.assertEqual(line_product_1.qty_invoiced, 1)
        self.assertEqual(line_product_1.qty_to_invoice, 0)
        self.assertEqual(line_product_2.product_uom_qty, 2)
        self.assertEqual(line_product_2.qty_delivered, 2)
        self.assertEqual(line_product_2.qty_invoiced, 2)
        self.assertEqual(line_product_2.qty_to_invoice, 0)
        done_pickings = sale.picking_ids.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_model='stock.picking',
            active_ids=done_pickings.ids,
            active_id=done_pickings.id,
        )
        return_picking = return_picking.create({})
        return_picking._onchange_picking_id()
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        return_picking.create_returns()
        picking_ret = sale.picking_ids.filtered(lambda p: p.state != 'done')
        picking_ret.action_confirm()
        picking_ret.move_line_ids.filtered(
            lambda m: m.product_id == self.product_1).qty_done = 1.0
        picking_ret.move_line_ids.filtered(
            lambda m: m.product_id == self.product_2).qty_done = 2.0
        picking_ret.button_validate()
        self.assertEqual(picking_ret.state, 'done')
        self.assertEqual(line_product_pack.product_uom_qty, 1)
        self.assertEqual(line_product_pack.qty_delivered, 1)
        self.assertEqual(line_product_pack.qty_invoiced, 1)
        self.assertEqual(line_product_pack.qty_to_invoice, 0)
        self.assertEqual(line_product_1.product_uom_qty, 1)
        self.assertEqual(line_product_1.qty_delivered, 0)
        self.assertEqual(line_product_1.qty_invoiced, 1)
        self.assertEqual(line_product_1.qty_to_invoice, -1)
        self.assertEqual(line_product_2.product_uom_qty, 2)
        self.assertEqual(line_product_2.qty_delivered, 0)
        self.assertEqual(line_product_2.qty_invoiced, 2)
        self.assertEqual(line_product_2.qty_to_invoice, -2)

    def test_sale_with_pack_order_detail(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        product_pack_qty = self.get_stock(
            self.product_pack_order_detail, self.stock_location)
        self.assertEqual(product_pack_qty, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_order_detail.id,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.assertEqual(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertTrue(line_product_pack)
        self.assertEqual(line_product_pack.product_uom_qty, 1)
        self.assertEqual(line_product_pack.price_unit, 1)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEqual(line_product_1.product_uom_qty, 1)
        self.assertEqual(line_product_1.price_unit, 100)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEqual(line_product_2.product_uom_qty, 2)
        self.assertEqual(line_product_2.price_unit, 500)
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(sale)
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEqual(inv_line_product_pack.quantity, 1)
        sale.invoice_ids.unlink()
        picking = sale.picking_ids[0]
        self.assertEqual(len(picking.move_ids), 2)
        move_product_pack = picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEqual(move_product_1.product_uom_qty, 1)
        move_product_2 = picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEqual(move_product_2.product_uom_qty, 2)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity_done = move.product_uom_qty
        picking._action_done()
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(line_product_pack.product_uom_qty, 1)
        self.assertEqual(line_product_pack.qty_delivered, 0)
        self.assertEqual(line_product_pack.qty_invoiced, 0)
        self.assertEqual(line_product_pack.qty_to_invoice, 1)
        self.assertEqual(line_product_1.product_uom_qty, 1)
        self.assertEqual(line_product_1.qty_delivered, 1)
        self.assertEqual(line_product_1.qty_invoiced, 0)
        self.assertEqual(line_product_1.qty_to_invoice, 1)
        self.assertEqual(line_product_2.product_uom_qty, 2)
        self.assertEqual(line_product_2.qty_delivered, 2)
        self.assertEqual(line_product_2.qty_invoiced, 0)
        self.assertEqual(line_product_2.qty_to_invoice, 2)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(sale)
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEqual(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_detail)
        self.assertTrue(inv_line_product_pack)
        self.assertEqual(inv_line_product_pack.quantity, 1)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEqual(inv_line_product_1.quantity, 1)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEqual(inv_line_product_2.quantity, 2)
        self.assertEqual(line_product_pack.product_uom_qty, 1)
        self.assertEqual(line_product_pack.qty_delivered, 1)
        self.assertEqual(line_product_pack.qty_invoiced, 1)
        self.assertEqual(line_product_pack.qty_to_invoice, 0)
        self.assertEqual(line_product_1.product_uom_qty, 1)
        self.assertEqual(line_product_1.qty_delivered, 1)
        self.assertEqual(line_product_1.qty_invoiced, 1)
        self.assertEqual(line_product_1.qty_to_invoice, 0)
        self.assertEqual(line_product_2.product_uom_qty, 2)
        self.assertEqual(line_product_2.qty_delivered, 2)
        self.assertEqual(line_product_2.qty_invoiced, 2)
        self.assertEqual(line_product_2.qty_to_invoice, 0)
        done_pickings = sale.picking_ids.filtered(lambda p: p.state == 'done')
        self.assertEqual(len(done_pickings), 1)
        return_picking = self.env['stock.return.picking'].with_context(
            active_model='stock.picking',
            active_ids=done_pickings.ids,
            active_id=done_pickings.id,
        )
        return_picking = return_picking.create({})
        return_picking._onchange_picking_id()
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        return_picking.create_returns()
        picking_ret = sale.picking_ids.filtered(lambda p: p.state != 'done')
        picking_ret.action_confirm()
        picking_ret.move_line_ids.filtered(
            lambda m: m.product_id == self.product_1).qty_done = 1.0
        picking_ret.move_line_ids.filtered(
            lambda m: m.product_id == self.product_2).qty_done = 2.0
        picking_ret.button_validate()
        self.assertEqual(picking_ret.state, 'done')
        self.assertEqual(line_product_pack.product_uom_qty, 1)
        self.assertEqual(line_product_pack.qty_delivered, 1)
        self.assertEqual(line_product_pack.qty_invoiced, 1)
        self.assertEqual(line_product_pack.qty_to_invoice, 0)
        self.assertEqual(line_product_1.product_uom_qty, 1)
        self.assertEqual(line_product_1.qty_delivered, 0)
        self.assertEqual(line_product_1.qty_invoiced, 1)
        self.assertEqual(line_product_1.qty_to_invoice, -1)
        self.assertEqual(line_product_2.product_uom_qty, 2)
        self.assertEqual(line_product_2.qty_delivered, 0)
        self.assertEqual(line_product_2.qty_invoiced, 2)
        self.assertEqual(line_product_2.qty_to_invoice, -2)

    def test_sale_with_pack_delivery_totalized(self):
        self.update_stock(self.product_1, self.stock_location, 10)
        self.update_stock(self.product_2, self.stock_location, 20)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_totalized, self.stock_location)
        self.assertEqual(product_pack_qty, 10)
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
            ],
        })
        self.assertEqual(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized)
        self.assertTrue(line_product_pack)
        self.assertEqual(line_product_pack.product_uom_qty, 1)
        price_pack = 1 * 100 * (1 - 5 / 100) + 2 * 500 * (1 - 10 / 100)
        self.assertEqual(line_product_pack.price_unit, price_pack)
        self.assertEqual(line_product_pack.discount, 0)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEqual(line_product_1.product_uom_qty, 1)
        self.assertEqual(line_product_1.price_unit, 0)
        self.assertEqual(line_product_1.discount, 0)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEqual(line_product_2.product_uom_qty, 2)
        self.assertEqual(line_product_2.price_unit, 0)
        self.assertEqual(line_product_2.discount, 0)
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEqual(len(picking.move_ids), 2)
        move_product_pack = picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEqual(move_product_1.product_uom_qty, 1)
        move_product_2 = picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEqual(move_product_2.product_uom_qty, 2)
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity_done = move.product_uom_qty
        picking._action_done()
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(line_product_pack.product_uom_qty, 1)
        self.assertEqual(line_product_pack.qty_delivered, 0)
        self.assertEqual(line_product_pack.qty_invoiced, 0)
        self.assertEqual(line_product_pack.qty_to_invoice, 0)
        self.assertEqual(line_product_1.product_uom_qty, 1)
        self.assertEqual(line_product_1.qty_delivered, 1)
        self.assertEqual(line_product_1.qty_invoiced, 0)
        self.assertEqual(line_product_1.qty_to_invoice, 1)
        self.assertEqual(line_product_2.product_uom_qty, 2)
        self.assertEqual(line_product_2.qty_delivered, 2)
        self.assertEqual(line_product_2.qty_invoiced, 0)
        self.assertEqual(line_product_2.qty_to_invoice, 2)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(sale)
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEqual(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_totalized)
        self.assertTrue(inv_line_product_pack)
        self.assertEqual(inv_line_product_pack.quantity, 1)
        self.assertEqual(inv_line_product_pack.discount, 0)
        self.assertEqual(inv_line_product_pack.price_unit, price_pack)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEqual(inv_line_product_1.quantity, 1)
        self.assertEqual(inv_line_product_1.discount, 0)
        self.assertEqual(inv_line_product_1.price_unit, 0)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEqual(inv_line_product_2.quantity, 2)
        self.assertEqual(inv_line_product_2.discount, 0)
        self.assertEqual(inv_line_product_2.price_unit, 0)
        self.assertEqual(line_product_pack.product_uom_qty, 1)
        self.assertEqual(line_product_pack.qty_delivered, 1)
        self.assertEqual(line_product_pack.qty_invoiced, 1)
        self.assertEqual(line_product_pack.qty_to_invoice, 0)
        self.assertEqual(line_product_1.product_uom_qty, 1)
        self.assertEqual(line_product_1.qty_delivered, 1)
        self.assertEqual(line_product_1.qty_invoiced, 1)
        self.assertEqual(line_product_1.qty_to_invoice, 0)
        self.assertEqual(line_product_2.product_uom_qty, 2)
        self.assertEqual(line_product_2.qty_delivered, 2)
        self.assertEqual(line_product_2.qty_invoiced, 2)
        self.assertEqual(line_product_2.qty_to_invoice, 0)
        done_pickings = sale.picking_ids.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_model='stock.picking',
            active_ids=done_pickings.ids,
            active_id=done_pickings.id,
        )
        return_picking = return_picking.create({})
        return_picking._onchange_picking_id()
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_2).quantity = 2.0
        return_picking.create_returns()
        picking_ret = sale.picking_ids.filtered(lambda p: p.state != 'done')
        picking_ret.action_confirm()
        picking_ret.move_line_ids.filtered(
            lambda m: m.product_id == self.product_1).qty_done = 1.0
        picking_ret.move_line_ids.filtered(
            lambda m: m.product_id == self.product_2).qty_done = 2.0
        picking_ret.button_validate()
        self.assertEqual(picking_ret.state, 'done')
        self.assertEqual(line_product_pack.product_uom_qty, 1)
        self.assertEqual(line_product_pack.qty_delivered, 1)
        self.assertEqual(line_product_pack.qty_invoiced, 1)
        self.assertEqual(line_product_pack.qty_to_invoice, 0)
        self.assertEqual(line_product_1.product_uom_qty, 1)
        self.assertEqual(line_product_1.qty_delivered, 0)
        self.assertEqual(line_product_1.qty_invoiced, 1)
        self.assertEqual(line_product_1.qty_to_invoice, -1)
        self.assertEqual(line_product_2.product_uom_qty, 2)
        self.assertEqual(line_product_2.qty_delivered, 0)
        self.assertEqual(line_product_2.qty_invoiced, 2)
        self.assertEqual(line_product_2.qty_to_invoice, -2)

    def test_sale_with_pack_order_totalized(self):
        self.update_stock(self.product_1, self.stock_location, 100)
        self.update_stock(self.product_2, self.stock_location, 200)
        product_pack_qty = self.get_stock(
            self.product_pack_order_totalized, self.stock_location)
        self.assertEqual(product_pack_qty, 100)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_order_totalized.id,
                    'product_uom_qty': 5,
                }),
            ],
        })
        self.assertEqual(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_order_totalized)
        self.assertTrue(line_product_pack)
        self.assertEqual(line_product_pack.product_uom_qty, 5)
        self.assertEqual(line_product_pack.price_unit, 1100)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEqual(line_product_1.product_uom_qty, 5)
        self.assertEqual(line_product_1.price_unit, 0)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEqual(line_product_2.product_uom_qty, 10)
        self.assertEqual(line_product_2.price_unit, 0)
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(sale)
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_totalized)
        self.assertTrue(inv_line_product_pack)
        self.assertEqual(inv_line_product_pack.quantity, 5)
        self.assertEqual(inv_line_product_pack.price_unit, 1100)
        sale.invoice_ids.unlink()
        picking = sale.picking_ids[0]
        self.assertEqual(len(picking.move_ids), 2)
        move_product_pack = picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_totalized)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEqual(move_product_1.product_uom_qty, 5)
        move_product_2 = picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEqual(move_product_2.product_uom_qty, 10)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 2
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 4
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity_done = move.product_uom_qty
        picking._action_done()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(line_product_pack.product_uom_qty, 5)
        self.assertEqual(line_product_pack.qty_delivered, 0)
        self.assertEqual(line_product_pack.qty_invoiced, 0)
        self.assertEqual(line_product_pack.qty_to_invoice, 5)
        self.assertEqual(line_product_1.product_uom_qty, 5)
        self.assertEqual(line_product_1.qty_delivered, 5)
        self.assertEqual(line_product_1.qty_invoiced, 0)
        self.assertEqual(line_product_1.qty_to_invoice, 5)
        self.assertEqual(line_product_2.product_uom_qty, 10)
        self.assertEqual(line_product_2.qty_delivered, 10)
        self.assertEqual(line_product_2.qty_invoiced, 0)
        self.assertEqual(line_product_2.qty_to_invoice, 10)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(sale)
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEqual(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_totalized)
        self.assertTrue(inv_line_product_pack)
        self.assertEqual(inv_line_product_pack.quantity, 5)
        self.assertEqual(inv_line_product_pack.price_unit, 1100)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 5)
        self.assertTrue(inv_line_product_1)
        self.assertEqual(inv_line_product_1.price_unit, 0)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEqual(inv_line_product_2.quantity, 10)
        self.assertEqual(inv_line_product_2.price_unit, 0)
        self.assertEqual(line_product_pack.product_uom_qty, 5)
        self.assertEqual(line_product_pack.qty_delivered, 5)
        self.assertEqual(line_product_pack.qty_invoiced, 5)
        self.assertEqual(line_product_pack.qty_to_invoice, 0)
        self.assertEqual(line_product_1.product_uom_qty, 5)
        self.assertEqual(line_product_1.qty_delivered, 5)
        self.assertEqual(line_product_1.qty_invoiced, 5)
        self.assertEqual(line_product_1.qty_to_invoice, 0)
        self.assertEqual(line_product_2.product_uom_qty, 10)
        self.assertEqual(line_product_2.qty_delivered, 10)
        self.assertEqual(line_product_2.qty_invoiced, 10)
        self.assertEqual(line_product_2.qty_to_invoice, 0)

    def test_sale_with_pack_delivery_ignored(self):
        self.update_stock(self.product_1, self.stock_location, 100)
        self.update_stock(self.product_2, self.stock_location, 200)
        product_pack_qty = self.get_stock(
            self.product_pack_delivery_ignored, self.stock_location)
        self.assertEqual(product_pack_qty, 100)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_delivery_ignored.id,
                    'product_uom_qty': 5,
                }),
            ],
        })
        self.assertEqual(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored)
        self.assertTrue(line_product_pack)
        self.assertEqual(line_product_pack.product_uom_qty, 5)
        self.assertEqual(line_product_pack.price_unit, 1)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEqual(line_product_1.product_uom_qty, 5)
        self.assertEqual(line_product_1.price_unit, 0)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEqual(line_product_2.product_uom_qty, 10)
        self.assertEqual(line_product_2.price_unit, 0)
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEqual(len(picking.move_ids), 2)
        move_product_pack = picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEqual(move_product_1.product_uom_qty, 5)
        move_product_2 = picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEqual(move_product_2.product_uom_qty, 10)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 5
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 10
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity_done = move.product_uom_qty
        picking._action_done()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(line_product_pack.product_uom_qty, 5)
        self.assertEqual(line_product_pack.qty_delivered, 0)
        self.assertEqual(line_product_pack.qty_invoiced, 0)
        self.assertEqual(line_product_pack.qty_to_invoice, 0)
        self.assertEqual(line_product_1.product_uom_qty, 5)
        self.assertEqual(line_product_1.qty_delivered, 5)
        self.assertEqual(line_product_1.qty_invoiced, 0)
        self.assertEqual(line_product_1.qty_to_invoice, 5)
        self.assertEqual(line_product_2.product_uom_qty, 10)
        self.assertEqual(line_product_2.qty_delivered, 10)
        self.assertEqual(line_product_2.qty_invoiced, 0)
        self.assertEqual(line_product_2.qty_to_invoice, 10)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(sale)
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEqual(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_delivery_ignored)
        self.assertTrue(inv_line_product_pack)
        self.assertEqual(inv_line_product_pack.quantity, 5)
        self.assertEqual(inv_line_product_pack.price_unit, 1)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEqual(inv_line_product_1.quantity, 5)
        self.assertEqual(inv_line_product_1.price_unit, 0)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEqual(inv_line_product_2.quantity, 10)
        self.assertEqual(inv_line_product_2.price_unit, 0)
        self.assertEqual(line_product_pack.product_uom_qty, 5)
        self.assertEqual(line_product_pack.qty_delivered, 5)
        self.assertEqual(line_product_pack.qty_invoiced, 5)
        self.assertEqual(line_product_pack.qty_to_invoice, 0)
        self.assertEqual(line_product_1.product_uom_qty, 5)
        self.assertEqual(line_product_1.qty_delivered, 5)
        self.assertEqual(line_product_1.qty_invoiced, 5)
        self.assertEqual(line_product_1.qty_to_invoice, 0)
        self.assertEqual(line_product_2.product_uom_qty, 10)
        self.assertEqual(line_product_2.qty_delivered, 10)
        self.assertEqual(line_product_2.qty_invoiced, 10)
        self.assertEqual(line_product_2.qty_to_invoice, 0)

    def test_sale_with_pack_order_ignored(self):
        self.update_stock(self.product_1, self.stock_location, 100)
        self.update_stock(self.product_2, self.stock_location, 200)
        product_pack_qty = self.get_stock(
            self.product_pack_order_ignored, self.stock_location)
        self.assertEqual(product_pack_qty, 100)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_pack_order_ignored.id,
                    'product_uom_qty': 5,
                }),
            ],
        })
        self.assertEqual(len(sale.order_line), 3)
        line_product_pack = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_pack_order_ignored)
        self.assertTrue(line_product_pack)
        self.assertEqual(line_product_pack.product_uom_qty, 5)
        self.assertEqual(line_product_pack.price_unit, 1)
        line_product_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEqual(line_product_1.product_uom_qty, 5)
        self.assertEqual(line_product_1.price_unit, 0)
        line_product_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEqual(line_product_2.product_uom_qty, 10)
        self.assertEqual(line_product_2.price_unit, 0)
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(sale)
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_ignored)
        self.assertTrue(inv_line_product_pack)
        self.assertEqual(inv_line_product_pack.quantity, 5)
        self.assertEqual(inv_line_product_pack.price_unit, 1)
        sale.invoice_ids.unlink()
        picking = sale.picking_ids[0]
        self.assertEqual(len(picking.move_ids), 2)
        move_product_pack = picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_ignored)
        self.assertFalse(move_product_pack)
        move_product_1 = picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEqual(move_product_1.product_uom_qty, 5)
        move_product_2 = picking.move_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEqual(move_product_2.product_uom_qty, 10)
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_1).quantity_done = 5
        picking.move_ids_without_package.filtered(
            lambda ln: ln.product_id == self.product_2).quantity_done = 10
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity_done = move.product_uom_qty
        picking._action_done()
        self.assertEqual(line_product_pack.product_uom_qty, 5)
        self.assertEqual(line_product_pack.qty_delivered, 0)
        self.assertEqual(line_product_pack.qty_invoiced, 0)
        self.assertEqual(line_product_pack.qty_to_invoice, 5)
        self.assertEqual(line_product_1.product_uom_qty, 5)
        self.assertEqual(line_product_1.qty_delivered, 5)
        self.assertEqual(line_product_1.qty_invoiced, 0)
        self.assertEqual(line_product_1.qty_to_invoice, 5)
        self.assertEqual(line_product_2.product_uom_qty, 10)
        self.assertEqual(line_product_2.qty_delivered, 10)
        self.assertEqual(line_product_2.qty_invoiced, 0)
        self.assertEqual(line_product_2.qty_to_invoice, 10)
        invoice = self.env['sale.advance.payment.inv'].with_context({
            'active_model': 'sale.order',
            'active_id': sale.id,
        }).create({
            'advance_payment_method': 'delivered',
        })._create_invoices(sale)
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEqual(len(invoice.invoice_line_ids), 3)
        inv_line_product_pack = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_pack_order_ignored)
        self.assertTrue(inv_line_product_pack)
        self.assertEqual(inv_line_product_pack.quantity, 5)
        self.assertEqual(inv_line_product_pack.price_unit, 1)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1
            and ln.quantity == 5)
        self.assertTrue(inv_line_product_1)
        self.assertEqual(inv_line_product_1.price_unit, 0)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEqual(inv_line_product_2.quantity, 10)
        self.assertEqual(inv_line_product_2.price_unit, 0)
        self.assertEqual(line_product_pack.product_uom_qty, 5)
        self.assertEqual(line_product_pack.qty_delivered, 5)
        self.assertEqual(line_product_pack.qty_invoiced, 5)
        self.assertEqual(line_product_pack.qty_to_invoice, 0)
        self.assertEqual(line_product_1.product_uom_qty, 5)
        self.assertEqual(line_product_1.qty_delivered, 5)
        self.assertEqual(line_product_1.qty_invoiced, 5)
        self.assertEqual(line_product_1.qty_to_invoice, 0)
        self.assertEqual(line_product_2.product_uom_qty, 10)
        self.assertEqual(line_product_2.qty_delivered, 10)
        self.assertEqual(line_product_2.qty_invoiced, 10)
        self.assertEqual(line_product_2.qty_to_invoice, 0)
