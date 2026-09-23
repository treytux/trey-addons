###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import Form, common


class TestSaleInvoicePolicyAllDelivered(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.customer = self.env['res.partner'].create({
            'name': 'Test partner',
            'company_id': self.company.id,
        })
        self.supplier = self.env['res.partner'].create({
            'name': 'Test supplier',
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 1',
            'standard_price': 10,
            'list_price': 100,
            'invoice_policy': 'all_delivered',
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 2',
            'standard_price': 10,
            'list_price': 100,
            'invoice_policy': 'all_delivered',
        })
        self.service_product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 50,
            'invoice_policy': 'all_delivered',
        })
        self.shipping_product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Shipping product test',
            'standard_price': 10,
            'list_price': 100,
            'invoice_policy': 'all_delivered',
        })
        self.dropshipping_type = self.env['stock.picking.type'].search([
            ('company_id', '=', self.company.id),
            ('default_location_src_id.usage', '=', 'supplier'),
            ('default_location_dest_id.usage', '=', 'customer'),
        ], limit=1, order='sequence')
        self.dropshipping_route = self.env.ref(
            'stock_dropshipping.route_drop_shipping')
        self.product_dropshipping = self.env['product.product'].create({
            'name': 'Test product dropshipping',
            'type': 'product',
            'route_ids': [(6, 0, [self.dropshipping_route.id])],
            'invoice_policy': 'all_delivered',
            'seller_ids': [
                (0, 0, {
                    'partner_id': self.supplier.id,
                    'price': 10,
                }),
            ],
        })
        self.warehouse = self.env.ref('stock.warehouse0')
        self.location_test = self.env['stock.location'].create({
            'name': 'Test location',
            'usage': 'internal',
        })

    def create_sale(self, quantity, warehouse, partner):
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'company_id': self.company.id,
            'warehouse_id': warehouse.id,
            'invoice_policy': partner.invoice_policy,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 10,
                    'product_uom_qty': quantity,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 20,
                    'product_uom_qty': quantity,
                }),
            ],
        })
        sale.action_confirm()
        return sale

    def picking_transfer(self, picking, qty):
        picking.action_confirm()
        picking.action_confirm()
        for move in picking.move_ids:
            move.quantity_done = qty
        picking.button_validate()
        self.assertEqual(picking.state, 'done')

    def update_qty_on_hand(self, product, location, new_qty):
        quant = self.env['stock.quant'].search([
            ('product_id', '=', product.id),
            ('location_id', '=', location.id),
        ], limit=1)
        if quant:
            quant.inventory_quantity = new_qty
            quant.action_apply_inventory()
        else:
            self.env['stock.quant'].create({
                'product_id': product.id,
                'location_id': location.id,
                'inventory_quantity': new_qty,
            }).action_apply_inventory()
        self.assertEqual(
            product.with_context(location=location.id).qty_available, new_qty)

    def test_sale_no_shipment_01(self):
        self.assertFalse(self.customer.invoice_policy)
        self.customer.invoice_policy = 'all_delivered'
        self.assertEqual(self.customer.invoice_policy, 'all_delivered')
        self.update_qty_on_hand(
            self.product_01, self.warehouse.lot_stock_id, 10)
        self.update_qty_on_hand(
            self.product_02, self.warehouse.lot_stock_id, 10)
        sale = self.create_sale(1, self.warehouse, self.customer)
        self.assertEqual(sale.invoice_policy, 'all_delivered')
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEqual(picking.state, 'assigned')
        self.assertEqual(sale.invoice_status, 'no')
        self.assertEqual(len(picking.move_ids), 2)
        picking.move_ids[0].quantity_done = 1
        res = picking.button_validate()
        backorder_wizard = Form(
            self.env['stock.backorder.confirmation'].with_context(
                res['context'])).save()
        backorder_wizard.process()
        self.assertEqual(len(sale.picking_ids), 2)
        self.assertEqual(sale.picking_ids.mapped('state'), ['assigned', 'done'])
        self.assertEqual(sale.invoice_status, 'no')

    def test_sale_no_shipment_02(self):
        self.assertFalse(self.customer.invoice_policy)
        self.customer.invoice_policy = 'all_delivered'
        self.assertEqual(self.customer.invoice_policy, 'all_delivered')
        self.update_qty_on_hand(
            self.product_01, self.warehouse.lot_stock_id, 10)
        self.update_qty_on_hand(
            self.product_02, self.warehouse.lot_stock_id, 10)
        sale = self.create_sale(1, self.warehouse, self.customer)
        self.assertEqual(sale.invoice_policy, 'all_delivered')
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEqual(picking.state, 'assigned')
        self.assertEqual(sale.invoice_status, 'no')
        self.assertEqual(len(picking.move_ids), 2)
        picking.move_ids[0].quantity_done = 1
        res = picking.button_validate()
        backorder_wizard = Form(
            self.env['stock.backorder.confirmation'].with_context(
                res['context'])).save()
        backorder_wizard.process_cancel_backorder()
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(sale.picking_ids.state, 'done')
        self.assertEqual(sale.invoice_status, 'to invoice')

    def test_sale_one_order_line_no_shipment_01(self):
        self.assertFalse(self.customer.invoice_policy)
        self.customer.invoice_policy = 'all_delivered'
        self.assertEqual(self.customer.invoice_policy, 'all_delivered')
        self.update_qty_on_hand(
            self.product_01, self.warehouse.lot_stock_id, 5)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'company_id': self.company.id,
            'warehouse_id': self.warehouse.id,
            'invoice_policy': self.customer.invoice_policy,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 10,
                    'product_uom_qty': 10,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.invoice_policy, 'all_delivered')
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEqual(picking.state, 'assigned')
        self.assertEqual(sale.invoice_status, 'no')
        self.assertEqual(len(picking.move_ids), 1)
        picking.move_ids[0].quantity_done = 1
        res = picking.button_validate()
        backorder_wizard = Form(
            self.env['stock.backorder.confirmation'].with_context(
                res['context'])).save()
        backorder_wizard.process()
        self.assertEqual(len(sale.picking_ids), 2)
        self.assertEqual(sale.picking_ids.mapped('state'), ['assigned', 'done'])
        self.assertEqual(
            sale.picking_ids[0].move_ids[0].state, 'partially_available')
        self.assertEqual(
            sale.picking_ids[0].move_ids[0].product_uom_qty, 9)
        self.assertEqual(
            sale.picking_ids[1].move_ids[0].state, 'done')
        self.assertEqual(
            sale.picking_ids[1].move_ids[0].product_uom_qty, 1)
        self.assertEqual(sale.invoice_status, 'no')

    def test_sale_one_order_line_no_shipment_02(self):
        self.assertFalse(self.customer.invoice_policy)
        self.customer.invoice_policy = 'all_delivered'
        self.assertEqual(self.customer.invoice_policy, 'all_delivered')
        self.update_qty_on_hand(
            self.product_01, self.warehouse.lot_stock_id, 5)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'company_id': self.company.id,
            'warehouse_id': self.warehouse.id,
            'invoice_policy': self.customer.invoice_policy,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 10,
                    'product_uom_qty': 10,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.invoice_policy, 'all_delivered')
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEqual(picking.state, 'assigned')
        self.assertEqual(sale.invoice_status, 'no')
        self.assertEqual(len(picking.move_ids), 1)
        picking.move_ids[0].quantity_done = 1
        res = picking.button_validate()
        backorder_wizard = Form(
            self.env['stock.backorder.confirmation'].with_context(
                res['context'])).save()
        backorder_wizard.process_cancel_backorder()
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(sale.picking_ids.state, 'done')
        self.assertEqual(sale.invoice_status, 'to invoice')

    def test_sale_full_shipment(self):
        self.assertFalse(self.customer.invoice_policy)
        self.customer.invoice_policy = 'all_delivered'
        self.assertEqual(self.customer.invoice_policy, 'all_delivered')
        self.update_qty_on_hand(
            self.product_01, self.warehouse.lot_stock_id, 10)
        self.update_qty_on_hand(
            self.product_02, self.warehouse.lot_stock_id, 10)
        sale = self.create_sale(1, self.warehouse, self.customer)
        self.assertEqual(sale.invoice_policy, 'all_delivered')
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEqual(picking.state, 'assigned')
        self.assertEqual(sale.invoice_status, 'no')
        self.picking_transfer(picking, 1)
        self.assertEqual(picking.state, 'done')
        self.assertEqual(sale.invoice_status, 'to invoice')

    def test_partial_return_no_invoice(self):
        self.assertFalse(self.customer.invoice_policy)
        self.customer.invoice_policy = 'all_delivered'
        self.assertEqual(self.customer.invoice_policy, 'all_delivered')
        self.update_qty_on_hand(
            self.product_01, self.warehouse.lot_stock_id, 10)
        self.update_qty_on_hand(
            self.product_02, self.warehouse.lot_stock_id, 10)
        sale = self.create_sale(1, self.warehouse, self.customer)
        self.assertEqual(sale.invoice_policy, 'all_delivered')
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEqual(picking.state, 'assigned')
        self.assertEqual(sale.invoice_status, 'no')
        self.picking_transfer(picking, 1)
        self.assertEqual(picking.state, 'done')
        self.assertEqual(sale.invoice_status, 'to invoice')
        return_picking_form = Form(self.env['stock.return.picking'].with_context(
            active_model='stock.picking',
            active_id=picking.id,
            active_ids=picking.ids,
            default_location_id=self.location_test.id,
        ))
        return_picking = return_picking_form.save()
        self.assertEqual(len(return_picking.product_return_moves), 2)
        return_line = return_picking.product_return_moves.filtered(
            lambda ln: ln.product_id == self.product_02)
        return_picking.product_return_moves = [(3, return_line.id)]
        self.assertEqual(len(return_picking.product_return_moves), 1)
        return_picking.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(sale.picking_ids), 2)
        picking_ret = sale.picking_ids.filtered(lambda p: p.state != 'done')
        self.picking_transfer(picking_ret, 1)
        self.assertEqual(sale.invoice_status, 'no')
        sale_line = sale.order_line.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(sale_line.invoice_status, 'to invoice')

    def test_full_return_no_invoice(self):
        self.assertFalse(self.customer.invoice_policy)
        self.customer.invoice_policy = 'all_delivered'
        self.assertEqual(self.customer.invoice_policy, 'all_delivered')
        self.update_qty_on_hand(
            self.product_01, self.warehouse.lot_stock_id, 10)
        self.update_qty_on_hand(
            self.product_02, self.warehouse.lot_stock_id, 10)
        sale = self.create_sale(1, self.warehouse, self.customer)
        self.assertEqual(sale.invoice_policy, 'all_delivered')
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEqual(picking.state, 'assigned')
        self.assertEqual(sale.invoice_status, 'no')
        self.picking_transfer(picking, 1)
        self.assertEqual(picking.state, 'done')
        self.assertEqual(sale.invoice_status, 'to invoice')
        return_picking_form = Form(self.env['stock.return.picking'].with_context(
            active_model='stock.picking',
            active_id=picking.id,
            active_ids=picking.ids,
            default_location_id=self.location_test.id,
        ))
        return_picking = return_picking_form.save()
        self.assertEqual(len(return_picking.product_return_moves), 2)
        return_picking.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        self.assertEqual(return_picking.product_return_moves[0].quantity, 1)
        self.assertEqual(return_picking.product_return_moves[1].quantity, 1)
        return_picking.create_returns()
        self.assertEqual(len(sale.picking_ids), 2)
        picking_ret = sale.picking_ids.filtered(lambda p: p.state != 'done')
        self.picking_transfer(picking_ret, 1)
        self.assertEqual(sale.invoice_status, 'no')

    def test_partial_return_with_invoice(self):
        self.assertFalse(self.customer.invoice_policy)
        self.customer.invoice_policy = 'all_delivered'
        self.assertEqual(self.customer.invoice_policy, 'all_delivered')
        self.update_qty_on_hand(
            self.product_01, self.warehouse.lot_stock_id, 10)
        self.update_qty_on_hand(
            self.product_02, self.warehouse.lot_stock_id, 10)
        sale = self.create_sale(1, self.warehouse, self.customer)
        self.assertEqual(sale.invoice_policy, 'all_delivered')
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEqual(picking.state, 'assigned')
        self.assertEqual(sale.invoice_status, 'no')
        self.picking_transfer(picking, 1)
        self.assertEqual(picking.state, 'done')
        self.assertEqual(sale.invoice_status, 'to invoice')
        moves = sale._create_invoices()
        self.assertEqual(len(moves), 1)
        self.assertEqual(len(sale.invoice_ids), 1)
        self.assertEqual(sale.invoice_status, 'invoiced')
        return_picking_form = Form(self.env['stock.return.picking'].with_context(
            active_model='stock.picking',
            active_id=picking.id,
            active_ids=picking.ids,
            default_location_id=self.location_test.id,
        ))
        return_picking = return_picking_form.save()
        self.assertEqual(len(return_picking.product_return_moves), 2)
        return_line = return_picking.product_return_moves.filtered(
            lambda ln: ln.product_id == self.product_02)
        return_picking.product_return_moves = [(3, return_line.id)]
        self.assertEqual(len(return_picking.product_return_moves), 1)
        return_picking.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(sale.picking_ids), 2)
        picking_ret = sale.picking_ids.filtered(lambda p: p.state != 'done')
        self.picking_transfer(picking_ret, 1)
        self.assertEqual(sale.invoice_status, 'to invoice')

    def test_full_return_with_invoice(self):
        self.assertFalse(self.customer.invoice_policy)
        self.customer.invoice_policy = 'all_delivered'
        self.assertEqual(self.customer.invoice_policy, 'all_delivered')
        self.update_qty_on_hand(
            self.product_01, self.warehouse.lot_stock_id, 10)
        self.update_qty_on_hand(
            self.product_02, self.warehouse.lot_stock_id, 10)
        sale = self.create_sale(1, self.warehouse, self.customer)
        self.assertEqual(sale.invoice_policy, 'all_delivered')
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEqual(picking.state, 'assigned')
        self.assertEqual(sale.invoice_status, 'no')
        self.picking_transfer(picking, 1)
        self.assertEqual(picking.state, 'done')
        moves = sale._create_invoices()
        self.assertEqual(len(moves), 1)
        self.assertEqual(len(sale.invoice_ids), 1)
        self.assertEqual(sale.invoice_status, 'invoiced')
        return_picking_form = Form(self.env['stock.return.picking'].with_context(
            active_model='stock.picking',
            active_id=picking.id,
            active_ids=picking.ids,
            default_location_id=self.location_test.id,
        ))
        return_picking = return_picking_form.save()
        self.assertEqual(len(return_picking.product_return_moves), 2)
        return_picking.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(sale.picking_ids), 2)
        picking_ret = sale.picking_ids.filtered(lambda p: p.state != 'done')
        self.picking_transfer(picking_ret, 1)
        self.assertEqual(sale.invoice_status, 'to invoice')

    def test_sale_full_shipment_delivery_line_or_service_product(self):
        self.assertFalse(self.customer.invoice_policy)
        self.customer.invoice_policy = 'all_delivered'
        self.assertEqual(self.customer.invoice_policy, 'all_delivered')
        self.update_qty_on_hand(
            self.product_01, self.warehouse.lot_stock_id, 10)
        self.update_qty_on_hand(
            self.product_02, self.warehouse.lot_stock_id, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'company_id': self.company.id,
            'warehouse_id': self.warehouse.id,
            'invoice_policy': self.customer.invoice_policy,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 10,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 20,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.shipping_product.id,
                    'price_unit': 2.99,
                    'product_uom_qty': 1,
                    'is_delivery': True,
                }),
                (0, 0 , {
                    'product_id': self.service_product.id,
                    'price_unit': 3.99,
                    'product_uom_qty': 1,
                })
            ],
        })
        self.assertEqual(sale.invoice_policy, 'all_delivered')
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEqual(picking.state, 'assigned')
        self.assertEqual(sale.invoice_status, 'no')
        self.picking_transfer(picking, 1)
        self.assertEqual(picking.state, 'done')
        lines_delivered = sale.order_line.filtered(
            lambda ln: not ln.is_delivery and ln.product_id.type != 'service')
        qty_request = sum([line.product_uom_qty for line in lines_delivered])
        qty_delivered = sum([line.qty_delivered for line in lines_delivered])
        self.assertEqual(qty_request, qty_delivered)
        delivery_line = sale.order_line.filtered(lambda ln: ln.is_delivery)
        self.assertEqual(delivery_line.product_uom_qty, 1)
        self.assertEqual(delivery_line.qty_delivered, 0)
        service_line = sale.order_line.filtered(
            lambda ln: not ln.is_delivery and ln.product_id.type == 'service')
        self.assertEqual(service_line.product_uom_qty, 1)
        self.assertEqual(service_line.qty_delivered, 0)
        self.assertEqual(sale.invoice_status, 'to invoice')

    def test_sale_full_shipment_delivery_line_with_stock(self):
        self.assertFalse(self.customer.invoice_policy)
        self.customer.invoice_policy = 'all_delivered'
        self.assertEqual(self.customer.invoice_policy, 'all_delivered')
        self.update_qty_on_hand(
            self.product_01, self.warehouse.lot_stock_id, 10)
        self.update_qty_on_hand(
            self.product_02, self.warehouse.lot_stock_id, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'company_id': self.company.id,
            'warehouse_id': self.warehouse.id,
            'invoice_policy': self.customer.invoice_policy,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 10,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.shipping_product.id,
                    'price_unit': 2.99,
                    'product_uom_qty': 1,
                    'is_delivery': True,
                }),
            ],
        })
        self.assertEqual(sale.invoice_policy, 'all_delivered')
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEqual(picking.state, 'assigned')
        self.assertEqual(sale.invoice_status, 'no')
        self.picking_transfer(picking, 1)
        self.assertEqual(picking.state, 'done')
        self.assertEqual(sale.invoice_status, 'to invoice')
        lines_delivered = sale.order_line.filtered(
            lambda ln: not ln.is_delivery and ln.product_id.type != 'service')
        qty_request = sum([line.product_uom_qty for line in lines_delivered])
        qty_delivered = sum([line.qty_delivered for line in lines_delivered])
        self.assertEqual(qty_request, qty_delivered)
        delivery_line = sale.order_line.filtered(lambda ln: ln.is_delivery)
        self.assertEqual(delivery_line.product_uom_qty, 1)
        self.assertEqual(delivery_line.qty_delivered, 0)
        self.assertEqual(sale.invoice_status, 'to invoice')

    def test_sale_full_shipment_delivery_line_without_stock(self):
        self.assertFalse(self.customer.invoice_policy)
        self.customer.invoice_policy = 'all_delivered'
        self.assertEqual(self.customer.invoice_policy, 'all_delivered')
        self.update_qty_on_hand(
            self.product_01, self.warehouse.lot_stock_id, 0)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'company_id': self.company.id,
            'warehouse_id': self.warehouse.id,
            'invoice_policy': self.customer.invoice_policy,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 10,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.shipping_product.id,
                    'price_unit': 2.99,
                    'product_uom_qty': 1,
                    'is_delivery': True,
                }),
            ],
        })
        self.assertEqual(sale.invoice_policy, 'all_delivered')
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEqual(picking.state, 'confirmed')
        self.assertEqual(sale.invoice_status, 'no')

    def test_sale_partial_shipment(self):
        self.assertFalse(self.customer.invoice_policy)
        self.customer.invoice_policy = 'all_delivered'
        self.assertEqual(self.customer.invoice_policy, 'all_delivered')
        self.update_qty_on_hand(
            self.product_01, self.warehouse.lot_stock_id, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'company_id': self.company.id,
            'warehouse_id': self.warehouse.id,
            'invoice_policy': self.customer.invoice_policy,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 10,
                    'product_uom_qty': 2,
                }),
            ],
        })
        self.assertEqual(sale.invoice_status, 'no')
        sale.action_confirm()
        self.assertEqual(sale.invoice_status, 'no')
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.move_ids[0].quantity_done = 1
        res = picking.button_validate()
        backorder_wizard = Form(
            self.env['stock.backorder.confirmation'].with_context(
                res['context'])).save()
        backorder_wizard.process()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(len(sale.picking_ids), 2)
        self.assertEqual(sale.invoice_status, 'no')

    def test_sale_partial_shipment_partial_return(self):
        self.assertFalse(self.customer.invoice_policy)
        self.customer.invoice_policy = 'all_delivered'
        self.assertEqual(self.customer.invoice_policy, 'all_delivered')
        self.update_qty_on_hand(
            self.product_01, self.warehouse.lot_stock_id, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'company_id': self.company.id,
            'warehouse_id': self.warehouse.id,
            'invoice_policy': self.customer.invoice_policy,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 10,
                    'product_uom_qty': 3,
                }),
            ],
        })
        self.assertEqual(sale.invoice_status, 'no')
        sale.action_confirm()
        self.assertEqual(sale.invoice_status, 'no')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.move_ids[0].quantity_done = 2
        res = picking.button_validate()
        backorder_wizard = Form(
            self.env['stock.backorder.confirmation'].with_context(
                res['context'])).save()
        backorder_wizard.process()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(len(sale.picking_ids), 2)
        self.assertEqual(sale.invoice_status, 'no')
        return_picking_form = Form(self.env['stock.return.picking'].with_context(
            active_model='stock.picking',
            active_id=picking.id,
            active_ids=picking.ids,
            default_location_id=self.location_test.id,
        ))
        return_picking = return_picking_form.save()
        return_picking.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(sale.picking_ids), 3)
        picking_ret = max(sale.picking_ids, key=lambda p: p.id)
        self.picking_transfer(picking_ret, 1)
        self.assertEqual(sale.invoice_status, 'no')

    def test_sale_partial_shipment_full_return(self):
        self.assertFalse(self.customer.invoice_policy)
        self.customer.invoice_policy = 'all_delivered'
        self.assertEqual(self.customer.invoice_policy, 'all_delivered')
        self.update_qty_on_hand(
            self.product_01, self.warehouse.lot_stock_id, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'company_id': self.company.id,
            'warehouse_id': self.warehouse.id,
            'invoice_policy': self.customer.invoice_policy,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 10,
                    'product_uom_qty': 3,
                }),
            ],
        })
        self.assertEqual(sale.invoice_status, 'no')
        sale.action_confirm()
        self.assertEqual(sale.invoice_status, 'no')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.move_ids[0].quantity_done = 2
        res = picking.button_validate()
        backorder_wizard = Form(
            self.env['stock.backorder.confirmation'].with_context(
                res['context'])).save()
        backorder_wizard.process()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(len(sale.picking_ids), 2)
        self.assertEqual(sale.invoice_status, 'no')
        return_picking_form = Form(self.env['stock.return.picking'].with_context(
            active_model='stock.picking',
            active_id=picking.id,
            active_ids=picking.ids,
            default_location_id=self.location_test.id,
        ))
        return_picking = return_picking_form.save()
        return_picking.product_return_moves.write({
            'quantity': 2.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(sale.picking_ids), 3)
        picking_ret = max(sale.picking_ids, key=lambda p: p.id)
        self.picking_transfer(picking_ret, 2)
        self.assertEqual(sale.invoice_status, 'no')

    def test_invoice_status_dropshipping_return_full(self):
        self.customer.invoice_policy = 'all_delivered'
        self.update_qty_on_hand(
            self.product_dropshipping, self.warehouse.lot_stock_id, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'warehouse_id': self.warehouse.id,
            'invoice_policy': 'all_delivered',
            'order_line': [
                (0, 0, {
                    'product_id': self.product_dropshipping.id,
                    'price_unit': 10,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.service_product.id,
                    'price_unit': 20,
                    'product_uom_qty': 1,
                    'is_delivery': True,
                })
            ],
        })
        self.assertEqual(sale.invoice_policy, 'all_delivered')
        self.assertEqual(sale.invoice_status, 'no')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(sale.invoice_status, 'no')
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sale.procurement_group_id.id),
        ])
        self.assertEqual(len(purchase), 1)
        self.assertEqual(purchase.state, 'draft')
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(sale.invoice_status, 'no')
        purchase.button_confirm()
        self.assertEqual(sale.invoice_status, 'no')
        self.assertEqual(len(purchase.picking_ids), 1)
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(sale.picking_ids[0], purchase.picking_ids[0])
        picking = sale.picking_ids[0]
        self.picking_transfer(picking, qty=1)
        self.assertEqual(sale.invoice_status, 'to invoice')
        return_picking_form = Form(self.env['stock.return.picking'].with_context(
            active_model='stock.picking',
            active_id=picking.id,
            active_ids=picking.ids,
            default_location_id=self.location_test.id,
        ))
        return_picking = return_picking_form.save()
        return_picking.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(sale.picking_ids), 2)
        picking_ret = max(sale.picking_ids, key=lambda p: p.id)
        self.picking_transfer(picking_ret, 1)
        self.assertEqual(sale.invoice_status, 'no')

    def test_invoice_status_dropshipping_return_partial(self):
        self.customer.invoice_policy = 'all_delivered'
        self.update_qty_on_hand(
            self.product_dropshipping, self.warehouse.lot_stock_id, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'warehouse_id': self.warehouse.id,
            'invoice_policy': 'all_delivered',
            'order_line': [
                (0, 0, {
                    'product_id': self.product_dropshipping.id,
                    'price_unit': 10,
                    'product_uom_qty': 2,
                }),
                (0, 0, {
                    'product_id': self.service_product.id,
                    'price_unit': 20,
                    'product_uom_qty': 1,
                    'is_delivery': True,
                })
            ],
        })
        self.assertEqual(sale.invoice_policy, 'all_delivered')
        self.assertEqual(sale.invoice_status, 'no')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(sale.invoice_status, 'no')
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sale.procurement_group_id.id),
        ])
        self.assertEqual(len(purchase), 1)
        self.assertEqual(purchase.state, 'draft')
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(sale.invoice_status, 'no')
        purchase.button_confirm()
        self.assertEqual(sale.invoice_status, 'no')
        self.assertEqual(len(purchase.picking_ids), 1)
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(sale.picking_ids[0], purchase.picking_ids[0])
        picking = sale.picking_ids[0]
        self.picking_transfer(picking, qty=2)
        self.assertEqual(sale.invoice_status, 'to invoice')
        return_picking_form = Form(self.env['stock.return.picking'].with_context(
            active_model='stock.picking',
            active_id=picking.id,
            active_ids=picking.ids,
            default_location_id=self.location_test.id,
        ))
        return_picking = return_picking_form.save()
        return_picking.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(sale.picking_ids), 2)
        picking_ret = max(sale.picking_ids, key=lambda p: p.id)
        self.picking_transfer(picking_ret, 1)
        self.assertEqual(sale.invoice_status, 'no')

    def test_invoice_status_dropshipping(self):
        self.customer.invoice_policy = 'all_delivered'
        self.update_qty_on_hand(
            self.product_dropshipping, self.warehouse.lot_stock_id, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'warehouse_id': self.warehouse.id,
            'invoice_policy': 'all_delivered',
            'order_line': [
                (0, 0, {
                    'product_id': self.product_dropshipping.id,
                    'price_unit': 10,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.service_product.id,
                    'price_unit': 20,
                    'product_uom_qty': 1,
                    'is_delivery': True,
                })
            ],
        })
        self.assertEqual(sale.invoice_policy, 'all_delivered')
        self.assertEqual(sale.invoice_status, 'no')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(sale.invoice_status, 'no')
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sale.procurement_group_id.id),
        ])
        self.assertEqual(len(purchase), 1)
        self.assertEqual(purchase.state, 'draft')
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(
            purchase.order_line[0].product_id, self.product_dropshipping)
        self.assertEqual(purchase.order_line[0].product_uom_qty, 1)
        self.assertEqual(sale.invoice_status, 'no')
        purchase.button_confirm()
        self.assertEqual(sale.invoice_status, 'no')
        self.assertEqual(len(purchase.picking_ids), 1)
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(sale.picking_ids[0], purchase.picking_ids[0])
        purchase_picking = purchase.picking_ids[0]
        self.picking_transfer(purchase_picking, qty=1)
        self.assertEqual(sale.invoice_status, 'to invoice')
        self.assertEqual(
            purchase_picking.picking_type_id, self.dropshipping_type)

    def test_sale_dropshipping_partial_cancel(self):
        self.customer.invoice_policy = 'all_delivered'
        self.update_qty_on_hand(
            self.product_dropshipping, self.warehouse.lot_stock_id, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'warehouse_id': self.warehouse.id,
            'invoice_policy': 'all_delivered',
            'order_line': [
                (0, 0, {
                    'product_id': self.product_dropshipping.id,
                    'price_unit': 10,
                    'product_uom_qty': 2,
                }),
                (0, 0, {
                    'product_id': self.service_product.id,
                    'price_unit': 20,
                    'product_uom_qty': 1,
                    'is_delivery': True,
                })
            ],
        })
        self.assertEqual(sale.invoice_policy, 'all_delivered')
        self.assertEqual(sale.invoice_status, 'no')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(sale.invoice_status, 'no')
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sale.procurement_group_id.id),
        ])
        self.assertEqual(len(purchase), 1)
        self.assertEqual(purchase.state, 'draft')
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(
            purchase.order_line[0].product_id, self.product_dropshipping)
        self.assertEqual(purchase.order_line[0].product_uom_qty, 2)
        self.assertEqual(sale.invoice_status, 'no')
        purchase.button_confirm()
        self.assertEqual(sale.invoice_status, 'no')
        self.assertEqual(len(purchase.picking_ids), 1)
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(sale.picking_ids[0], purchase.picking_ids[0])
        purchase_picking = purchase.picking_ids[0]
        purchase_picking.move_ids[0].quantity_done = 1
        wizard = self.env['stock.backorder.confirmation'].create({
            'pick_ids': [(4, purchase_picking.id)],
        })
        wizard.process_cancel_backorder()
        self.assertEqual(sale.invoice_status, 'no')
        self.assertEqual(
            purchase_picking.picking_type_id, self.dropshipping_type)

    def test_sale_dropshipping_partial_return_full(self):
        self.customer.invoice_policy = 'all_delivered'
        self.update_qty_on_hand(
            self.product_dropshipping, self.warehouse.lot_stock_id, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'warehouse_id': self.warehouse.id,
            'invoice_policy': 'all_delivered',
            'order_line': [
                (0, 0, {
                    'product_id': self.product_dropshipping.id,
                    'price_unit': 10,
                    'product_uom_qty': 2,
                }),
                (0, 0, {
                    'product_id': self.service_product.id,
                    'price_unit': 20,
                    'product_uom_qty': 1,
                    'is_delivery': True,
                })
            ],
        })
        self.assertEqual(sale.invoice_policy, 'all_delivered')
        self.assertEqual(sale.invoice_status, 'no')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(sale.invoice_status, 'no')
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sale.procurement_group_id.id),
        ])
        self.assertEqual(len(purchase), 1)
        self.assertEqual(purchase.state, 'draft')
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(
            purchase.order_line[0].product_id, self.product_dropshipping)
        self.assertEqual(purchase.order_line[0].product_uom_qty, 2)
        self.assertEqual(sale.invoice_status, 'no')
        purchase.button_confirm()
        self.assertEqual(sale.invoice_status, 'no')
        self.assertEqual(len(purchase.picking_ids), 1)
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(sale.picking_ids[0], purchase.picking_ids[0])
        purchase_picking = purchase.picking_ids[0]
        purchase_picking.move_ids[0].quantity_done = 1
        res = purchase_picking.button_validate()
        backorder_wizard = Form(
            self.env['stock.backorder.confirmation'].with_context(
                res['context'])).save()
        backorder_wizard.process()
        self.assertEqual(sale.invoice_status, 'no')
        self.assertEqual(
            purchase_picking.picking_type_id, self.dropshipping_type)
        return_picking_form = Form(self.env['stock.return.picking'].with_context(
            active_model='stock.picking',
            active_id=purchase_picking.id,
            active_ids=purchase_picking.ids,
            default_location_id=self.location_test.id,
        ))
        return_picking = return_picking_form.save()
        return_picking.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(sale.picking_ids), 3)
        picking_ret = max(sale.picking_ids, key=lambda p: p.id)
        self.picking_transfer(picking_ret, 1)
        self.assertEqual(sale.invoice_status, 'no')

    def test_sale_dropshipping_partial_return_partial(self):
        self.customer.invoice_policy = 'all_delivered'
        self.update_qty_on_hand(
            self.product_dropshipping, self.warehouse.lot_stock_id, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'warehouse_id': self.warehouse.id,
            'invoice_policy': 'all_delivered',
            'order_line': [
                (0, 0, {
                    'product_id': self.product_dropshipping.id,
                    'price_unit': 10,
                    'product_uom_qty': 3,
                }),
                (0, 0, {
                    'product_id': self.service_product.id,
                    'price_unit': 20,
                    'product_uom_qty': 1,
                    'is_delivery': True,
                })
            ],
        })
        self.assertEqual(sale.invoice_policy, 'all_delivered')
        self.assertEqual(sale.invoice_status, 'no')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(sale.invoice_status, 'no')
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sale.procurement_group_id.id),
        ])
        self.assertEqual(len(purchase), 1)
        self.assertEqual(purchase.state, 'draft')
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(
            purchase.order_line[0].product_id, self.product_dropshipping)
        self.assertEqual(purchase.order_line[0].product_uom_qty, 3)
        self.assertEqual(sale.invoice_status, 'no')
        purchase.button_confirm()
        self.assertEqual(sale.invoice_status, 'no')
        self.assertEqual(len(purchase.picking_ids), 1)
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(sale.picking_ids[0], purchase.picking_ids[0])
        purchase_picking = purchase.picking_ids[0]
        purchase_picking.move_ids[0].quantity_done = 2
        res = purchase_picking.button_validate()
        backorder_wizard = Form(
            self.env['stock.backorder.confirmation'].with_context(
                res['context'])).save()
        backorder_wizard.process()
        self.assertEqual(sale.invoice_status, 'no')
        self.assertEqual(
            purchase_picking.picking_type_id, self.dropshipping_type)
        return_picking_form = Form(self.env['stock.return.picking'].with_context(
            active_model='stock.picking',
            active_id=purchase_picking.id,
            active_ids=purchase_picking.ids,
            default_location_id=self.location_test.id,
        ))
        return_picking = return_picking_form.save()
        return_picking.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(sale.picking_ids), 3)
        picking_ret = max(sale.picking_ids, key=lambda p: p.id)
        self.picking_transfer(picking_ret, 1)
        self.assertEqual(sale.invoice_status, 'no')

    def test_invoice_policy_ondelete_cleanup(self):
        self.customer.invoice_policy = 'all_delivered'
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'company_id': self.company.id,
            'invoice_policy': 'all_delivered',
        })
        sale_ondelete = (
            sale._fields['invoice_policy'].ondelete['all_delivered']
        )
        product_ondelete = (
            self.product_01.product_tmpl_id._fields['invoice_policy']
            .ondelete['all_delivered']
        )
        partner_ondelete = (
            self.customer._fields['invoice_policy'].ondelete['all_delivered']
        )
        sale_ondelete(sale)
        product_ondelete(self.product_01.product_tmpl_id)
        partner_ondelete(self.customer)
        self.assertEqual(sale.invoice_policy, 'delivery')
        self.assertEqual(
            self.product_01.product_tmpl_id.invoice_policy, 'delivery')
        self.assertEqual(self.customer.invoice_policy, 'delivery')
