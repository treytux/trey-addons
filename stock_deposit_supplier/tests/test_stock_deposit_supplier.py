###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestStockDepositSupplier(TransactionCase):

    def setUp(self):
        super().setUp()
        self.buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        self.wh_stock = self.env.ref('stock.warehouse0')
        self.customer_loc = self.env.ref('stock.stock_location_customers')
        self.supplier_loc = self.env.ref('stock.stock_location_suppliers')
        self.deposit_supplier_loc = self.env.ref(
            'stock_deposit_supplier.deposit_supplier_location')
        self.deposit_supplier_picking_type = self.env.ref(
            'stock_deposit_supplier.deposit_supplier_picking_type')
        self.picking_type_in = self.env.ref('stock.picking_type_in')
        self.assertTrue(self.deposit_supplier_picking_type)
        self.product_1 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
            'purchase_method': 'receive',
            'route_ids': [(6, 0, [self.buy_route.id])],
        })
        self.product_2 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product2',
            'standard_price': 33,
            'list_price': 55,
            'purchase_method': 'receive',
            'route_ids': [(6, 0, [self.buy_route.id])],
        })
        need_groups = [
            (4, self.env.ref('stock.group_stock_multi_locations').id),
            (4, self.env.ref('stock.group_stock_multi_warehouses').id),
            (4, self.env.ref('stock.group_adv_location').id),
        ]
        self.env.user.groups_id = need_groups
        self.customer = self.env['res.partner'].create({
            'name': 'Test customer',
            'customer': True,
        })
        self.supplier = self.env['res.partner'].create({
            'name': 'Test supplier',
            'supplier': True,
        })
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.product_1.product_tmpl_id.id,
            'name': self.supplier.id,
        })
        self.assertEquals(len(self.product_1.seller_ids), 1)
        self.create_orderpoint('test1', self.product_1, self.wh_stock)
        orderpoints = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', self.product_1.id),
        ])
        self.assertEquals(len(orderpoints), 1)

    def update_qty_on_hand(self, product, location, new_qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': new_qty,
            'location_id': location.id,
        })
        wizard.change_product_qty()
        self.assertEqual(
            product.with_context(location=location.id).qty_available, new_qty)

    def create_orderpoint(self, key, product, warehouse):
        return self.env['stock.warehouse.orderpoint'].create({
            'name': 'Orderpoint %s' % key,
            'product_id': product.id,
            'warehouse_id': warehouse.id,
            'location_id': warehouse.out_type_id.default_location_src_id.id,
            'product_min_qty': 5,
            'product_max_qty': 20,
        })

    def create_purchase(self):
        return self.env['purchase.order'].create({
            'partner_id': self.supplier.id,
        })

    def create_purchase_line(self, purchase, product, qty):
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': purchase.id,
            'name': product.name,
            'product_id': product.id,
            'product_uom': product.uom_id.id,
            'product_qty': qty,
        })
        line.onchange_product_id()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        line.write({
            'price_unit': 10,
            'product_qty': qty,
        })
        return line

    def create_sale(self, product, quantity, warehouse):
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'warehouse_id': warehouse.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'price_unit': 10,
                'product_uom_qty': quantity,
            })]
        })
        sale.action_confirm()
        return sale

    def picking_transfer(self, picking, qty):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = qty
        picking.action_done()
        self.assertEquals(picking.state, 'done')

    def test_po_deposit_supplier_one_line(self):
        self.assertEqual(
            self.product_1.with_context(
                location=self.wh_stock.lot_stock_id.id).qty_available, 0)
        self.assertEqual(
            self.product_1.with_context(
                location=self.deposit_supplier_loc.id).qty_available, 0)
        purchase = self.create_purchase()
        purchase.picking_type_id = self.deposit_supplier_picking_type.id
        self.create_purchase_line(purchase, self.product_1, 100)
        purchase.button_confirm()
        self.assertEquals(len(purchase.picking_ids), 2)
        picking_1 = purchase.picking_ids.filtered(
            lambda p: p.location_id == self.supplier_loc
            and p.location_dest_id == self.deposit_supplier_loc)
        self.assertTrue(picking_1)
        self.assertEquals(len(picking_1.move_lines), 1)
        self.assertEquals(
            picking_1.picking_type_id, self.deposit_supplier_picking_type)
        self.assertEquals(picking_1.state, 'assigned')
        picking_2 = purchase.picking_ids.filtered(
            lambda p: p.location_id == self.deposit_supplier_loc
            and p.location_dest_id == self.wh_stock.lot_stock_id)
        self.assertTrue(picking_2)
        self.assertEquals(len(picking_2.move_lines), 1)
        self.assertEquals(
            picking_2.picking_type_id, self.deposit_supplier_picking_type)
        self.assertEquals(picking_2.state, 'waiting')
        for move in picking_1.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_1.action_done()
        self.assertEquals(picking_1.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.wh_stock.lot_stock_id.id).qty_available, 100)
        self.assertEqual(
            self.product_1.with_context(
                location=self.deposit_supplier_loc.id).qty_available, 100)
        self.assertEquals(picking_2.state, 'assigned')
        for move in picking_2.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_2.action_done()
        self.assertEquals(picking_2.state, 'done')
        self.assertEquals(purchase.order_line.qty_received, 100)
        self.assertEquals(purchase.order_line.qty_invoiced, 0)
        self.assertEqual(
            self.product_1.with_context(
                location=self.wh_stock.lot_stock_id.id).qty_available, 100)
        self.assertEqual(
            self.product_1.with_context(
                location=self.deposit_supplier_loc.id).qty_available, 0)
        self.assertEquals(purchase.invoice_status, 'to invoice')
        res = purchase.with_context(create_bill=True).action_view_invoice()
        ctx = res.get('context')
        f = Form(self.env['account.invoice'].with_context(ctx),
                 view='account.invoice_supplier_form')
        invoice = f.save()
        self.assertEquals(purchase.invoice_ids, invoice)
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.assertEquals(purchase.invoice_status, 'invoiced')
        invoice = purchase.invoice_ids[0]
        self.assertEquals(invoice.type, 'in_invoice')
        self.assertEquals(len(invoice.invoice_line_ids), 1)
        inv_line = invoice.invoice_line_ids[0]
        self.assertEquals(inv_line.quantity, 100)
        self.assertEquals(inv_line.purchase_line_id.qty_received, 100)
        self.assertEquals(inv_line.purchase_line_id.qty_invoiced, 100)

    def test_po_deposit_supplier_several_lines(self):
        self.assertEqual(
            self.product_1.with_context(
                location=self.wh_stock.lot_stock_id.id).qty_available, 0)
        self.assertEqual(
            self.product_1.with_context(
                location=self.deposit_supplier_loc.id).qty_available, 0)
        self.assertEqual(
            self.product_2.with_context(
                location=self.wh_stock.lot_stock_id.id).qty_available, 0)
        self.assertEqual(
            self.product_2.with_context(
                location=self.deposit_supplier_loc.id).qty_available, 0)
        purchase = self.create_purchase()
        purchase.picking_type_id = self.deposit_supplier_picking_type.id
        self.create_purchase_line(purchase, self.product_1, 100)
        self.create_purchase_line(purchase, self.product_2, 500)
        purchase.button_confirm()
        self.assertEquals(len(purchase.picking_ids), 2)
        picking_1 = purchase.picking_ids.filtered(
            lambda p: p.location_id == self.supplier_loc
            and p.location_dest_id == self.deposit_supplier_loc)
        self.assertTrue(picking_1)
        self.assertEquals(len(picking_1.move_lines), 2)
        self.assertEquals(
            picking_1.picking_type_id, self.deposit_supplier_picking_type)
        self.assertEquals(picking_1.state, 'assigned')
        picking_2 = purchase.picking_ids.filtered(
            lambda p: p.location_id == self.deposit_supplier_loc
            and p.location_dest_id == self.wh_stock.lot_stock_id)
        self.assertTrue(picking_2)
        self.assertEquals(len(picking_2.move_lines), 2)
        self.assertEquals(
            picking_2.picking_type_id, self.deposit_supplier_picking_type)
        self.assertEquals(picking_2.state, 'waiting')
        for move in picking_1.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_1.action_done()
        self.assertEquals(picking_1.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.wh_stock.lot_stock_id.id).qty_available, 100)
        self.assertEqual(
            self.product_1.with_context(
                location=self.deposit_supplier_loc.id).qty_available, 100)
        self.assertEqual(
            self.product_2.with_context(
                location=self.wh_stock.lot_stock_id.id).qty_available, 500)
        self.assertEqual(
            self.product_2.with_context(
                location=self.deposit_supplier_loc.id).qty_available, 500)
        self.assertEquals(picking_2.state, 'assigned')
        for move in picking_2.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_2.action_done()
        self.assertEquals(picking_2.state, 'done')
        line_product_1 = purchase.order_line.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEquals(line_product_1.qty_received, 100)
        self.assertEquals(line_product_1.qty_invoiced, 0)
        line_product_2 = purchase.order_line.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEquals(line_product_2.qty_received, 500)
        self.assertEquals(line_product_2.qty_invoiced, 0)
        self.assertEqual(
            self.product_1.with_context(
                location=self.wh_stock.lot_stock_id.id).qty_available, 100)
        self.assertEqual(
            self.product_1.with_context(
                location=self.deposit_supplier_loc.id).qty_available, 0)
        self.assertEqual(
            self.product_2.with_context(
                location=self.wh_stock.lot_stock_id.id).qty_available, 500)
        self.assertEqual(
            self.product_2.with_context(
                location=self.deposit_supplier_loc.id).qty_available, 0)
        self.assertEquals(purchase.invoice_status, 'to invoice')
        res = purchase.with_context(create_bill=True).action_view_invoice()
        ctx = res.get('context')
        f = Form(self.env['account.invoice'].with_context(ctx),
                 view='account.invoice_supplier_form')
        invoice = f.save()
        self.assertEquals(purchase.invoice_ids, invoice)
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.assertEquals(purchase.invoice_status, 'invoiced')
        invoice = purchase.invoice_ids[0]
        self.assertEquals(invoice.type, 'in_invoice')
        self.assertEquals(len(invoice.invoice_line_ids), 2)
        inv_line_product_1 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(inv_line_product_1)
        self.assertEquals(inv_line_product_1.quantity, 100)
        inv_line_product_2 = invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(inv_line_product_2)
        self.assertEquals(inv_line_product_2.quantity, 500)
        self.assertEquals(
            inv_line_product_1.purchase_line_id.qty_received, 100)
        self.assertEquals(
            inv_line_product_1.purchase_line_id.qty_invoiced, 100)
        self.assertEquals(
            inv_line_product_2.purchase_line_id.qty_received, 500)
        self.assertEquals(
            inv_line_product_2.purchase_line_id.qty_invoiced, 500)

    def test_po_normal_picking_in(self):
        self.assertEqual(
            self.product_1.with_context(
                location=self.wh_stock.lot_stock_id.id).qty_available, 0)
        self.assertEqual(
            self.product_1.with_context(
                location=self.deposit_supplier_loc.id).qty_available, 0)
        self.assertEqual(
            self.product_1.with_context(
                location=self.supplier_loc.id).qty_available, 0)
        purchase = self.create_purchase()
        self.assertEquals(purchase.picking_type_id, self.picking_type_in)
        self.create_purchase_line(purchase, self.product_1, 100)
        purchase.button_confirm()
        self.assertEquals(len(purchase.picking_ids), 1)
        picking = purchase.picking_ids
        self.assertEquals(picking.picking_type_id, self.picking_type_in)
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.state, 'assigned')
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEquals(picking.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.wh_stock.lot_stock_id.id).qty_available, 100)
        self.assertEqual(
            self.product_1.with_context(
                location=self.deposit_supplier_loc.id).qty_available, 0)
        self.assertEqual(
            self.product_1.with_context(
                location=self.supplier_loc.id).qty_available, -100)
        self.assertEquals(purchase.order_line.qty_received, 100)
        self.assertEquals(purchase.order_line.qty_invoiced, 0)
        self.assertEqual(
            self.product_1.with_context(
                location=self.wh_stock.lot_stock_id.id).qty_available, 100)
        self.assertEqual(
            self.product_1.with_context(
                location=self.deposit_supplier_loc.id).qty_available, 0)
        self.assertEquals(purchase.invoice_status, 'to invoice')
        res = purchase.with_context(create_bill=True).action_view_invoice()
        ctx = res.get('context')
        f = Form(self.env['account.invoice'].with_context(ctx),
                 view='account.invoice_supplier_form')
        invoice = f.save()
        self.assertEquals(purchase.invoice_ids, invoice)
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.assertEquals(purchase.invoice_status, 'invoiced')
        invoice = purchase.invoice_ids[0]
        self.assertEquals(invoice.type, 'in_invoice')
        self.assertEquals(len(invoice.invoice_line_ids), 1)
        inv_line = invoice.invoice_line_ids[0]
        self.assertEquals(inv_line.quantity, 100)
        self.assertEquals(inv_line.purchase_line_id.qty_received, 100)
        self.assertEquals(inv_line.purchase_line_id.qty_invoiced, 100)

    def test_po_deposit_supplier_one_line_return(self):
        self.assertEqual(
            self.product_1.with_context(
                location=self.wh_stock.lot_stock_id.id).qty_available, 0)
        self.assertEqual(
            self.product_1.with_context(
                location=self.deposit_supplier_loc.id).qty_available, 0)
        purchase = self.create_purchase()
        purchase.picking_type_id = self.deposit_supplier_picking_type.id
        self.create_purchase_line(purchase, self.product_1, 100)
        purchase.button_confirm()
        self.assertEquals(len(purchase.picking_ids), 2)
        picking_1 = purchase.picking_ids.filtered(
            lambda p: p.location_id == self.supplier_loc
            and p.location_dest_id == self.deposit_supplier_loc)
        self.assertTrue(picking_1)
        self.assertEquals(len(picking_1.move_lines), 1)
        self.assertEquals(
            picking_1.picking_type_id, self.deposit_supplier_picking_type)
        self.assertEquals(picking_1.state, 'assigned')
        picking_2 = purchase.picking_ids.filtered(
            lambda p: p.location_id == self.deposit_supplier_loc
            and p.location_dest_id == self.wh_stock.lot_stock_id)
        self.assertTrue(picking_2)
        self.assertEquals(len(picking_2.move_lines), 1)
        self.assertEquals(
            picking_2.picking_type_id, self.deposit_supplier_picking_type)
        self.assertEquals(picking_2.state, 'waiting')
        for move in picking_1.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_1.action_done()
        self.assertEquals(picking_1.state, 'done')
        self.assertEqual(
            self.product_1.with_context(
                location=self.wh_stock.lot_stock_id.id).qty_available, 100)
        self.assertEqual(
            self.product_1.with_context(
                location=self.deposit_supplier_loc.id).qty_available, 100)
        self.assertEquals(picking_2.state, 'assigned')
        for move in picking_2.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_2.action_done()
        self.assertEquals(picking_2.state, 'done')
        self.assertEquals(purchase.order_line.qty_received, 100)
        self.assertEquals(purchase.order_line.qty_invoiced, 0)
        self.assertEqual(
            self.product_1.with_context(
                location=self.wh_stock.lot_stock_id.id).qty_available, 100)
        self.assertEqual(
            self.product_1.with_context(
                location=self.deposit_supplier_loc.id).qty_available, 0)
        self.assertEquals(purchase.invoice_status, 'to invoice')
        res = purchase.with_context(create_bill=True).action_view_invoice()
        ctx = res.get('context')
        f = Form(self.env['account.invoice'].with_context(ctx),
                 view='account.invoice_supplier_form')
        invoice = f.save()
        self.assertEquals(purchase.invoice_ids, invoice)
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.assertEquals(purchase.invoice_status, 'invoiced')
        invoice = purchase.invoice_ids[0]
        self.assertEquals(invoice.type, 'in_invoice')
        self.assertEquals(len(invoice.invoice_line_ids), 1)
        inv_line = invoice.invoice_line_ids[0]
        self.assertEquals(inv_line.quantity, 100)
        self.assertEquals(inv_line.purchase_line_id.qty_received, 100)
        self.assertEquals(inv_line.purchase_line_id.qty_invoiced, 100)
        picking_wizard = self.env['stock.return.picking'].with_context(
            active_ids=picking_2.ids,
            active_id=picking_2.id,
        ).create({})
        picking_wizard.product_return_moves.quantity = 1.0
        picking_wizard.product_return_moves.to_refund = True
        picking_return_action = picking_wizard.create_returns()
        picking_return_2 = self.env['stock.picking'].browse(
            picking_return_action['res_id'])
        picking_return_2.move_lines[0].move_line_ids[0].qty_done = 1.0
        self.assertTrue(picking_return_2.action_done())
        self.assertEquals(picking_return_2.state, 'done')
        self.assertEquals(purchase.order_line.qty_received, 100)
        self.assertEquals(purchase.order_line.qty_invoiced, 100)
        self.assertEqual(
            self.product_1.with_context(
                location=self.wh_stock.lot_stock_id.id).qty_available, 100)
        self.assertEqual(
            self.product_1.with_context(
                location=self.deposit_supplier_loc.id).qty_available, 1)
        self.assertEquals(purchase.invoice_status, 'invoiced')
        picking_wizard = self.env['stock.return.picking'].with_context(
            active_ids=picking_1.ids,
            active_id=picking_1.id,
        ).create({})
        picking_wizard.product_return_moves.quantity = 1.0
        picking_wizard.product_return_moves.to_refund = True
        picking_return_action = picking_wizard.create_returns()
        picking_return_2 = self.env['stock.picking'].browse(
            picking_return_action['res_id'])
        picking_return_2.move_lines[0].move_line_ids[0].qty_done = 1.0
        self.assertTrue(picking_return_2.action_done())
        self.assertEquals(picking_return_2.state, 'done')
        self.assertEquals(purchase.order_line.qty_received, 99)
        self.assertEquals(purchase.order_line.qty_invoiced, 100)
        self.assertEqual(
            self.product_1.with_context(
                location=self.wh_stock.lot_stock_id.id).qty_available, 99)
        self.assertEqual(
            self.product_1.with_context(
                location=self.deposit_supplier_loc.id).qty_available, 0)
        self.assertEquals(purchase.invoice_status, 'invoiced')
