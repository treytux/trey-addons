###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestStockDeposit(TransactionCase):

    def setUp(self):
        super().setUp()
        type_revenue = self.env.ref('account.data_account_type_revenue')
        type_payable = self.env.ref('account.data_account_type_payable')
        self.account_customer = self.env['account.account'].create({
            'name': 'Customer',
            'code': 'XX_430',
            'user_type_id': type_payable.id,
            'reconcile': True,
        })
        self.account_supplier = self.env['account.account'].create({
            'name': 'Supplier',
            'code': 'XX_400',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        self.account_700 = self.env['account.account'].create({
            'code': '700000',
            'name': '700000',
            'user_type_id': self.ref('account.data_account_type_revenue'),
        })
        self.journal_sale = self.env['account.journal'].create({
            'name': 'Sale journal',
            'type': 'sale',
            'code': 'SJ',
        })
        self.journal_sale_refund = self.env['account.journal'].create({
            'name': 'Sale refund journal',
            'type': 'sale',
            'code': 'SRJ',
        })
        self.env.user.company_id.deposit_journal_invoice_id = (
            self.journal_sale.id)
        self.env.user.company_id.deposit_journal_refund_id = (
            self.journal_sale_refund.id)
        tax = self.env['account.tax'].create({
            'name': 'Tax Test 21%',
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'amount': 21,
        })
        self.product1 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
            'invoice_policy': 'delivery',
            'property_account_income_id': self.account_700.id,
        })
        self.product1.product_tmpl_id.taxes_id = [(6, 0, [tax.id])]
        self.product2 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product2',
            'standard_price': 33,
            'list_price': 55,
            'invoice_policy': 'delivery',
            'property_account_income_id': self.account_700.id,
        })
        self.product2.product_tmpl_id.taxes_id = [(6, 0, [tax.id])]
        self.wh_stock = self.env.ref('stock.warehouse0')
        self.wh_stock.int_type_id.active = True
        self.customer_loc = self.env.ref('stock.stock_location_customers')
        self.inventory_loc = self.env.ref('stock.location_inventory')
        need_groups = [
            (4, self.env.ref('stock.group_stock_multi_locations').id),
            (4, self.env.ref('stock.group_stock_multi_warehouses').id),
            (4, self.env.ref('stock.group_adv_location').id),
        ]
        self.env.user.groups_id = need_groups
        self.stock_wh = self.env.ref('stock.warehouse0')
        self.buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        self.supplier = self.env['res.partner'].create({
            'name': 'Test supplier',
            'supplier': True,
        })
        self.partner_common = self.env['res.partner'].create({
            'name': 'Test common customer',
            'customer': True,
        })
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.product1.product_tmpl_id.id,
            'name': self.supplier.id,
        })
        self.assertEquals(len(self.product1.seller_ids), 1)
        self.create_orderpoint('test', self.product1, self.stock_wh)
        orderpoints = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', self.product1.id),
        ])
        self.assertEquals(len(orderpoints), 1)
        self.orderpoint = orderpoints[0]
        self.assertEquals(self.orderpoint.name, 'Orderpoint test')
        self.new_pricelist = self.env['product.pricelist'].create({
            'name': 'Customer Pricelist',
            'item_ids': [
                (0, 0, {
                    'product_tmpl_id': self.product1.product_tmpl_id.id,
                    'applied_on': '1_product',
                    'min_quantity': 1,
                    'compute_price': 'fixed',
                    'fixed_price': 1,
                }),
                (0, 0, {
                    'product_tmpl_id': self.product2.product_tmpl_id.id,
                    'applied_on': '1_product',
                    'min_quantity': 1,
                    'compute_price': 'fixed',
                    'fixed_price': 2,
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

    def create_partner_deposit(self, name, location):
        partner_deposit = self.env['res.partner'].create({
            'name': 'Test %s partner' % name,
            'customer': True,
            'property_account_receivable_id': self.account_customer.id,
            'property_account_payable_id': self.account_supplier.id,
        })
        partner_deposit_ship = self.env['res.partner'].create({
            'name': 'Test %s shipping partner' % name,
            'parent_id': partner_deposit.id,
            'type': 'delivery',
            'property_stock_customer': location.id,
        })
        return partner_deposit, partner_deposit_ship

    def create_sale_order(
            self, partner, partner_shipping, warehouse, product, qty,
            price_forced=0, discount=0, pricelist=None):
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'partner_invoice_id': partner.id,
            'partner_shipping_id': partner_shipping.id,
            'warehouse_id': warehouse.id,
            'pricelist_id': (
                pricelist and pricelist.id
                or self.env.ref('product.list0').id),
        })
        order.onchange_partner_id()
        vline = self.env['sale.order.line'].new({
            'order_id': order.id,
            'name': product.name,
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': product.uom_id.id,
            'price_unit': price_forced,
            'discount': discount,
            'tax_id': [(6, 0, [product.taxes_id.id])],
        })
        vline.product_id_change()
        line = self.env['sale.order.line'].create(
            vline._convert_to_write(vline._cache))
        if price_forced != 0:
            line.price_unit = price_forced
        return order

    def check_and_assign_action_create_deposit(self, deposit_name):
        deposits_view_loc = self.env['stock.location'].search([
            ('name', '=', 'Parent deposits'),
            ('usage', '=', 'view'),
        ])
        self.assertEquals(len(deposits_view_loc), 1)
        deposits_loc = self.env['stock.location'].search([
            ('name', '=', deposit_name),
        ])
        deposit_loc = deposits_loc[0]
        self.assertEquals(len(deposit_loc), 1)
        self.assertEquals(deposit_loc.usage, 'internal')
        self.assertEquals(deposit_loc.location_id, deposits_view_loc)
        self.assertEquals(self.stock_wh.int_type_id.active, True)
        wh2deposit_route = self.env['stock.location.route'].search([
            ('name', '=', '%s -> %s' % (self.stock_wh.name, deposit_name)),
        ])
        self.assertEquals(len(wh2deposit_route), 1)
        domain_rule = [
            ('name', '=', '%s -> %s' % (
                self.stock_wh.lot_stock_id.name, deposit_name)),
            ('action', '=', 'pull'),
            ('picking_type_id', '=', self.stock_wh.int_type_id.id),
            ('location_src_id', '=', self.stock_wh.lot_stock_id.id),
            ('location_id', '=', deposit_loc.id),
            ('procure_method', '=', 'make_to_stock'),
            ('group_propagation_option', '=', 'propagate'),
            ('propagate', '=', True),
        ]
        wh2deposit_rule_dom = domain_rule + [
            ('route_id', '=', wh2deposit_route.id),
            ('sequence', '=', 20),
        ]
        wh2deposit_rule = self.env['stock.rule'].search(wh2deposit_rule_dom)
        self.assertEquals(len(wh2deposit_rule), 1)
        buy_rule_dom = domain_rule + [
            ('route_id', '=', self.buy_route.id),
            ('sequence', '=', 10),
        ]
        buy_rule = self.env['stock.rule'].search(buy_rule_dom)
        self.assertEquals(len(buy_rule), 1)
        return deposit_loc

    def test_deposit_sale_last_price_inv_sale_line(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 3)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.move_line_ids.location_dest_id,
            self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_last_price_inv_sale_line_2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 2,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 4)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 6)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 2)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 2)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 2)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 2)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.move_line_ids.location_dest_id,
            self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 2)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 2)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 4)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 2)

    def test_deposit_sale_last_price_no_inv_sale_line(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': False,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 3)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'to invoice')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 7)
        self.assertEqual(new_sale.order_line.qty_invoiced, 0)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        self.assertFalse(new_sale.invoice_ids)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_last_price_no_inv_sale_line2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': False,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 2,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 4)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 6)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'to invoice')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 2)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 2)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 2)
        self.assertEqual(new_sale.order_line.qty_invoiced, 0)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 2)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 2)
        self.assertEqual(new_picking.state, 'done')
        self.assertFalse(new_sale.invoice_ids)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 4)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 2)

    def test_deposit_sale_last_price_inv_more_qty(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 12,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 12)
        self.assertEqual(wizard.line_ids.qty_finish, -2)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 12)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 12)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 12)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 12)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 12)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 12)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12)

    def test_deposit_sale_last_price_inv_more_qty2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 12,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 12)
        self.assertEqual(wizard.line_ids.qty_finish, -6)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 6)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 12)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 12)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 12)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 12)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 12)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 12)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12)

    def test_deposit_sale_last_price_no_inv_more_qty(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': False,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 12,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 12)
        self.assertEqual(wizard.line_ids.qty_finish, -2)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'to invoice')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 12)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 12)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 12)
        self.assertEqual(new_sale.order_line.qty_invoiced, 0)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 12)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 12)
        self.assertEqual(new_picking.state, 'done')
        self.assertFalse(new_sale.invoice_ids)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12)

    def test_deposit_sale_last_price_no_inv_more_qty2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': False,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 12,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 12)
        self.assertEqual(wizard.line_ids.qty_finish, -6)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 6)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'to invoice')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 12)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 12)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 12)
        self.assertEqual(new_sale.order_line.qty_invoiced, 0)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 12)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 12)
        self.assertEqual(new_picking.state, 'done')
        self.assertFalse(new_sale.invoice_ids)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12)

    def test_deposit_sale_last_price_inv_not_sale_line(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 55 - 7)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 55)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 7)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_last_price_inv_not_sale_line2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 55 - 7)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 55)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 7)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_last_price_inv_not_sale_line_more_qty(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 30,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 30)
        self.assertEqual(wizard.line_ids.qty_finish, 55 - 30)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 55)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 30)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 30)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 30)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 30)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 30)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 30)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 30)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 30)

    def test_deposit_sale_last_price_inv_not_sale_line_more_qty2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 30,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 30)
        self.assertEqual(wizard.line_ids.qty_finish, 55 - 30)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 55)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 30)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 30)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 30)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 30)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 30)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 30)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 30)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 30)

    def test_deposit_sale_last_price_no_inv_not_sale_line(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': False,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 55 - 7)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 55)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'to invoice')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 7)
        self.assertEqual(new_sale.order_line.qty_invoiced, 0)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        self.assertFalse(new_sale.invoice_ids)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 7)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_last_price_no_inv_not_sale_line2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': False,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 55 - 7)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 55)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'to invoice')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 7)
        self.assertEqual(new_sale.order_line.qty_invoiced, 0)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        self.assertFalse(new_sale.invoice_ids)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 7)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_last_price_inv_sale_line_new_pricelist(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        partner_deposit1.property_product_pricelist = self.new_pricelist.id
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale1.pricelist_id, self.new_pricelist)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale2.pricelist_id, self.new_pricelist)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 3)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 1)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_last_price_inv_sale_line_new_pricelist2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        partner_deposit1.property_product_pricelist = self.new_pricelist.id
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, pricelist=self.new_pricelist)
        self.assertEqual(sale1.pricelist_id, self.new_pricelist)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale2.pricelist_id, self.new_pricelist)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, -1)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids[0].force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 6)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 1)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_last_price_inv_more_qty_new_pricelist(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        partner_deposit1.property_product_pricelist = self.new_pricelist.id
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale1.pricelist_id, self.new_pricelist)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale2.pricelist_id, self.new_pricelist)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 12,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 12)
        self.assertEqual(wizard.line_ids.qty_finish, 10 - 12)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 12)
        self.assertEqual(new_sale.order_line.price_unit, 1)
        self.assertEqual(new_sale.order_line.qty_delivered, 12)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 12)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 12)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 12)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 12)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12)

    def test_deposit_sale_last_price_inv_more_qty_new_pricelist2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        partner_deposit1.property_product_pricelist = self.new_pricelist.id
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, pricelist=self.new_pricelist)
        self.assertEqual(sale1.pricelist_id, self.new_pricelist)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale2.pricelist_id, self.new_pricelist)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 12,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 12)
        self.assertEqual(wizard.line_ids.qty_finish, 6 - 12)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 6)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 12)
        self.assertEqual(new_sale.order_line.price_unit, 1)
        self.assertEqual(new_sale.order_line.qty_delivered, 12)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 12)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 12)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 12)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 12)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12)

    def test_deposit_sale_last_price_inv_not_sale_line_new_pricelist(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        partner_deposit1.property_product_pricelist = self.new_pricelist.id
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale1.pricelist_id, self.new_pricelist)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale2.pricelist_id, self.new_pricelist)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 55 - 7)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 55)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 1)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 7)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_last_price_inv_not_sale_line_new_pricelist2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        partner_deposit1.property_product_pricelist = self.new_pricelist.id
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, pricelist=self.new_pricelist)
        self.assertEqual(sale1.pricelist_id, self.new_pricelist)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale2.pricelist_id, self.new_pricelist)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 55 - 7)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 55)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 1)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 7)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_last_price_inv_sale_line_2wizlines(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        sale3 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product2, 10, price_forced=200)
        self.assertEqual(sale3.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale3.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale3.action_confirm()
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(len(sale3.picking_ids), 1)
        picking_int = sale3.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 10
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product1.id,
                    'qty': 7,
                }),
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product2.id,
                    'qty': 11,
                })
            ],
        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 7)
        self.assertEqual(wizard.line_ids[0].qty_finish, 3)
        self.assertEqual(wizard.line_ids[1].qty, 11)
        self.assertEqual(wizard.line_ids[1].qty_finish, -1)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids[1].force_inventory = True
        wizard.line_ids[1].onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids[0].qty_theorical, 10)
        self.assertEqual(wizard.line_ids[1].qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale3.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(sale3.order_line.qty_to_invoice, 0)
        self.assertEqual(sale3.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 2)
        line_qty7 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(line_qty7)
        self.assertEqual(line_qty7.product_id, self.product1)
        self.assertEqual(line_qty7.product_uom_qty, 7)
        self.assertEqual(line_qty7.price_unit, 20)
        self.assertEqual(line_qty7.qty_delivered, 7)
        self.assertEqual(line_qty7.qty_to_invoice, 0)
        self.assertEqual(line_qty7.qty_invoiced, 7)
        line_qty11 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(line_qty11)
        self.assertEqual(line_qty11.product_id, self.product2)
        self.assertEqual(line_qty11.product_uom_qty, 11)
        self.assertEqual(line_qty11.price_unit, 200)
        self.assertEqual(line_qty11.qty_delivered, 11)
        self.assertEqual(line_qty11.qty_to_invoice, 0)
        self.assertEqual(line_qty11.qty_invoiced, 11)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 2)
        move_qty7 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(move_qty7)
        self.assertEqual(move_qty7.product_id, self.product1)
        self.assertEqual(move_qty7.location_id, deposit_loc1)
        self.assertEqual(move_qty7.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty7.sale_line_id, line_qty7)
        self.assertEqual(move_qty7.sale_line_id.qty_delivered, 7)
        move_qty11 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(move_qty11)
        self.assertEqual(move_qty11.product_id, self.product2)
        self.assertEqual(move_qty11.location_id, deposit_loc1)
        self.assertEqual(move_qty11.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty11.sale_line_id, line_qty11)
        self.assertEqual(move_qty11.sale_line_id.qty_delivered, 11)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 2)
        line_inv_qty7 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 7)
        self.assertEqual(line_inv_qty7.product_id, self.product1)
        self.assertEqual(line_inv_qty7.price_unit, 20)
        self.assertEqual(line_inv_qty7.sale_line_ids, line_qty7)
        line_inv_qty11 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 11)
        self.assertEqual(line_inv_qty11.product_id, self.product2)
        self.assertEqual(line_inv_qty11.price_unit, 200)
        self.assertEqual(line_inv_qty11.sale_line_ids, line_qty11)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11)

    def test_deposit_sale_last_price_inv_sale_line_2wizlines2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        sale3 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product2, 10, price_forced=200)
        self.assertEqual(sale3.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale3.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale3.action_confirm()
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(len(sale3.picking_ids), 1)
        picking_int = sale3.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 10
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 90)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product1.id,
                    'qty': 7,
                }),
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product2.id,
                    'qty': 11,
                })
            ],
        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 7)
        self.assertEqual(wizard.line_ids[0].qty_finish, -1)
        self.assertEqual(wizard.line_ids[1].qty, 11)
        self.assertEqual(wizard.line_ids[1].qty_finish, -1)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids[0].force_inventory = True
        wizard.line_ids[0].onchange_qty()
        wizard.line_ids[1].force_inventory = True
        wizard.line_ids[1].onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids[0].qty_theorical, 6)
        self.assertEqual(wizard.line_ids[1].qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale3.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(sale3.order_line.qty_to_invoice, 0)
        self.assertEqual(sale3.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 2)
        line_qty7 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(line_qty7)
        self.assertEqual(line_qty7.product_id, self.product1)
        self.assertEqual(line_qty7.product_uom_qty, 7)
        self.assertEqual(line_qty7.price_unit, 20)
        self.assertEqual(line_qty7.qty_delivered, 7)
        self.assertEqual(line_qty7.qty_to_invoice, 0)
        self.assertEqual(line_qty7.qty_invoiced, 7)
        line_qty11 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(line_qty11)
        self.assertEqual(line_qty11.product_id, self.product2)
        self.assertEqual(line_qty11.product_uom_qty, 11)
        self.assertEqual(line_qty11.price_unit, 200)
        self.assertEqual(line_qty11.qty_delivered, 11)
        self.assertEqual(line_qty11.qty_to_invoice, 0)
        self.assertEqual(line_qty11.qty_invoiced, 11)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 2)
        move_qty7 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(move_qty7)
        self.assertEqual(move_qty7.product_id, self.product1)
        self.assertEqual(move_qty7.location_id, deposit_loc1)
        self.assertEqual(move_qty7.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty7.sale_line_id, line_qty7)
        self.assertEqual(move_qty7.sale_line_id.qty_delivered, 7)
        move_qty11 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(move_qty11)
        self.assertEqual(move_qty11.product_id, self.product2)
        self.assertEqual(move_qty11.location_id, deposit_loc1)
        self.assertEqual(move_qty11.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty11.sale_line_id, line_qty11)
        self.assertEqual(move_qty11.sale_line_id.qty_delivered, 11)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 2)
        line_inv_qty7 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 7)
        self.assertEqual(line_inv_qty7.product_id, self.product1)
        self.assertEqual(line_inv_qty7.price_unit, 20)
        self.assertEqual(line_inv_qty7.sale_line_ids, line_qty7)
        line_inv_qty11 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 11)
        self.assertEqual(line_inv_qty11.product_id, self.product2)
        self.assertEqual(line_inv_qty11.price_unit, 200)
        self.assertEqual(line_inv_qty11.sale_line_ids, line_qty11)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 90)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11)

    def test_deposit_sale_last_price_inv_not_sale_line_2wizlines(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        sale3 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product2, 10, price_forced=200)
        self.assertEqual(sale3.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale3.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale3.action_confirm()
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(len(sale3.picking_ids), 1)
        picking_int = sale3.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 10
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product1.id,
                    'qty': 7,
                }),
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product2.id,
                    'qty': 11,
                })
            ],
        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 7)
        self.assertEqual(wizard.line_ids[1].qty, 11)
        self.assertEqual(wizard.line_ids[0].qty_finish, 55 - 7)
        self.assertEqual(wizard.line_ids[1].qty_finish, -1)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids[1].force_inventory = True
        wizard.line_ids[1].onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids[0].qty_theorical, 55)
        self.assertEqual(wizard.line_ids[1].qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale3.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(sale3.order_line.qty_to_invoice, 0)
        self.assertEqual(sale3.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 2)
        line_qty7 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(line_qty7)
        self.assertEqual(line_qty7.product_id, self.product1)
        self.assertEqual(line_qty7.product_uom_qty, 7)
        self.assertEqual(line_qty7.price_unit, 20)
        self.assertEqual(line_qty7.qty_delivered, 7)
        self.assertEqual(line_qty7.qty_to_invoice, 0)
        self.assertEqual(line_qty7.qty_invoiced, 7)
        line_qty11 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(line_qty11)
        self.assertEqual(line_qty11.product_id, self.product2)
        self.assertEqual(line_qty11.product_uom_qty, 11)
        self.assertEqual(line_qty11.price_unit, 200)
        self.assertEqual(line_qty11.qty_delivered, 11)
        self.assertEqual(line_qty11.qty_to_invoice, 0)
        self.assertEqual(line_qty11.qty_invoiced, 11)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 2)
        move_qty7 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(move_qty7)
        self.assertEqual(move_qty7.product_id, self.product1)
        self.assertEqual(move_qty7.location_id, deposit_loc1)
        self.assertEqual(move_qty7.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty7.sale_line_id, line_qty7)
        self.assertEqual(move_qty7.sale_line_id.qty_delivered, 7)
        move_qty11 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(move_qty11)
        self.assertEqual(move_qty11.product_id, self.product2)
        self.assertEqual(move_qty11.location_id, deposit_loc1)
        self.assertEqual(move_qty11.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty11.sale_line_id, line_qty11)
        self.assertEqual(move_qty11.sale_line_id.qty_delivered, 11)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 2)
        line_inv_qty7 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 7)
        self.assertEqual(line_inv_qty7.product_id, self.product1)
        self.assertEqual(line_inv_qty7.price_unit, 20)
        self.assertEqual(line_inv_qty7.sale_line_ids, line_qty7)
        line_inv_qty11 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 11)
        self.assertEqual(line_inv_qty11.product_id, self.product2)
        self.assertEqual(line_inv_qty11.price_unit, 200)
        self.assertEqual(line_inv_qty11.sale_line_ids, line_qty11)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 7)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11)

    def test_deposit_sale_last_price_inv_not_sale_line_2wizlines2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        sale3 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product2, 10, price_forced=200)
        self.assertEqual(sale3.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale3.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale3.action_confirm()
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(len(sale3.picking_ids), 1)
        picking_int = sale3.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 10
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 90)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product1.id,
                    'qty': 7,
                }),
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product2.id,
                    'qty': 11,
                })
            ],
        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 7)
        self.assertEqual(wizard.line_ids[1].qty, 11)
        self.assertEqual(wizard.line_ids[0].qty_finish, 55 - 7)
        self.assertEqual(wizard.line_ids[1].qty_finish, -1)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids[1].force_inventory = True
        wizard.line_ids[1].onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids[0].qty_theorical, 55)
        self.assertEqual(wizard.line_ids[1].qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale3.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(sale3.order_line.qty_to_invoice, 0)
        self.assertEqual(sale3.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 2)
        line_qty7 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(line_qty7)
        self.assertEqual(line_qty7.product_id, self.product1)
        self.assertEqual(line_qty7.product_uom_qty, 7)
        self.assertEqual(line_qty7.price_unit, 20)
        self.assertEqual(line_qty7.qty_delivered, 7)
        self.assertEqual(line_qty7.qty_to_invoice, 0)
        self.assertEqual(line_qty7.qty_invoiced, 7)
        line_qty11 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(line_qty11)
        self.assertEqual(line_qty11.product_id, self.product2)
        self.assertEqual(line_qty11.product_uom_qty, 11)
        self.assertEqual(line_qty11.price_unit, 200)
        self.assertEqual(line_qty11.qty_delivered, 11)
        self.assertEqual(line_qty11.qty_to_invoice, 0)
        self.assertEqual(line_qty11.qty_invoiced, 11)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 2)
        move_qty7 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(move_qty7)
        self.assertEqual(move_qty7.product_id, self.product1)
        self.assertEqual(move_qty7.location_id, deposit_loc1)
        self.assertEqual(move_qty7.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty7.sale_line_id, line_qty7)
        self.assertEqual(move_qty7.sale_line_id.qty_delivered, 7)
        move_qty11 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(move_qty11)
        self.assertEqual(move_qty11.product_id, self.product2)
        self.assertEqual(move_qty11.location_id, deposit_loc1)
        self.assertEqual(move_qty11.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty11.sale_line_id, line_qty11)
        self.assertEqual(move_qty11.sale_line_id.qty_delivered, 11)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 2)
        line_inv_qty7 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 7)
        self.assertEqual(line_inv_qty7.product_id, self.product1)
        self.assertEqual(line_inv_qty7.price_unit, 20)
        self.assertEqual(line_inv_qty7.sale_line_ids, line_qty7)
        line_inv_qty11 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 11)
        self.assertEqual(line_inv_qty11.product_id, self.product2)
        self.assertEqual(line_inv_qty11.price_unit, 200)
        self.assertEqual(line_inv_qty11.sale_line_ids, line_qty11)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 7)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 90)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11)

    def test_deposit_sale_last_price_inv_more_qty_2wizlines(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        sale3 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product2, 10, price_forced=200)
        self.assertEqual(sale3.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale3.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale3.action_confirm()
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(len(sale3.picking_ids), 1)
        picking_int = sale3.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 10
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product1.id,
                    'qty': 12,
                }),
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product2.id,
                    'qty': 11,
                })
            ],
        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 12)
        self.assertEqual(wizard.line_ids[0].qty_finish, -2)
        self.assertEqual(wizard.line_ids[1].qty, 11)
        self.assertEqual(wizard.line_ids[1].qty_finish, -1)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids[0].force_inventory = True
        wizard.line_ids[0].onchange_qty()
        wizard.line_ids[1].force_inventory = True
        wizard.line_ids[1].onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids[0].qty_theorical, 10)
        self.assertEqual(wizard.line_ids[1].qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale3.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(sale3.order_line.qty_to_invoice, 0)
        self.assertEqual(sale3.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 2)
        line_qty12 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 12)
        self.assertTrue(line_qty12)
        self.assertEqual(line_qty12.product_id, self.product1)
        self.assertEqual(line_qty12.price_unit, 20)
        self.assertEqual(line_qty12.qty_delivered, 12)
        self.assertEqual(line_qty12.qty_to_invoice, 0)
        self.assertEqual(line_qty12.qty_invoiced, 12)
        line_qty11 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(line_qty11)
        self.assertEqual(line_qty11.product_id, self.product2)
        self.assertEqual(line_qty11.price_unit, 200)
        self.assertEqual(line_qty11.qty_delivered, 11)
        self.assertEqual(line_qty11.qty_to_invoice, 0)
        self.assertEqual(line_qty11.qty_invoiced, 11)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 2)
        move_qty12 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 12)
        self.assertTrue(move_qty12)
        self.assertEqual(move_qty12.product_id, self.product1)
        self.assertEqual(move_qty12.location_id, deposit_loc1)
        self.assertEqual(move_qty12.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty12.sale_line_id, line_qty12)
        self.assertEqual(move_qty12.sale_line_id.qty_delivered, 12)
        move_qty11 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(move_qty11)
        self.assertEqual(move_qty11.product_id, self.product2)
        self.assertEqual(move_qty11.location_id, deposit_loc1)
        self.assertEqual(move_qty11.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty11.sale_line_id, line_qty11)
        self.assertEqual(move_qty11.sale_line_id.qty_delivered, 11)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 2)
        line_inv_qty12 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 12)
        self.assertEqual(line_inv_qty12.product_id, self.product1)
        self.assertEqual(line_inv_qty12.price_unit, 20)
        self.assertEqual(line_inv_qty12.sale_line_ids, line_qty12)
        line_inv_qty11 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 11)
        self.assertEqual(line_inv_qty11.product_id, self.product2)
        self.assertEqual(line_inv_qty11.price_unit, 200)
        self.assertEqual(line_inv_qty11.sale_line_ids, line_qty11)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11)

    def test_deposit_sale_last_price_inv_more_qty_2wizlines2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        sale3 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product2, 10, price_forced=200)
        self.assertEqual(sale3.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale3.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale3.action_confirm()
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(len(sale3.picking_ids), 1)
        picking_int = sale3.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 10
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 90)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product1.id,
                    'qty': 12,
                }),
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product2.id,
                    'qty': 11,
                })
            ],
        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 12)
        self.assertEqual(wizard.line_ids[0].qty_finish, -6)
        self.assertEqual(wizard.line_ids[1].qty, 11)
        self.assertEqual(wizard.line_ids[1].qty_finish, -1)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids[0].force_inventory = True
        wizard.line_ids[0].onchange_qty()
        wizard.line_ids[1].force_inventory = True
        wizard.line_ids[1].onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids[0].qty_theorical, 6)
        self.assertEqual(wizard.line_ids[1].qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale3.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(sale3.order_line.qty_to_invoice, 0)
        self.assertEqual(sale3.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 2)
        line_qty12 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 12)
        self.assertTrue(line_qty12)
        self.assertEqual(line_qty12.product_id, self.product1)
        self.assertEqual(line_qty12.price_unit, 20)
        self.assertEqual(line_qty12.qty_delivered, 12)
        self.assertEqual(line_qty12.qty_to_invoice, 0)
        self.assertEqual(line_qty12.qty_invoiced, 12)
        line_qty11 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(line_qty11)
        self.assertEqual(line_qty11.product_id, self.product2)
        self.assertEqual(line_qty11.price_unit, 200)
        self.assertEqual(line_qty11.qty_delivered, 11)
        self.assertEqual(line_qty11.qty_to_invoice, 0)
        self.assertEqual(line_qty11.qty_invoiced, 11)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 2)
        move_qty12 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 12)
        self.assertTrue(move_qty12)
        self.assertEqual(move_qty12.product_id, self.product1)
        self.assertEqual(move_qty12.location_id, deposit_loc1)
        self.assertEqual(move_qty12.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty12.sale_line_id, line_qty12)
        self.assertEqual(move_qty12.sale_line_id.qty_delivered, 12)
        move_qty11 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(move_qty11)
        self.assertEqual(move_qty11.product_id, self.product2)
        self.assertEqual(move_qty11.location_id, deposit_loc1)
        self.assertEqual(move_qty11.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty11.sale_line_id, line_qty11)
        self.assertEqual(move_qty11.sale_line_id.qty_delivered, 11)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 2)
        line_inv_qty12 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 12)
        self.assertEqual(line_inv_qty12.product_id, self.product1)
        self.assertEqual(line_inv_qty12.price_unit, 20)
        self.assertEqual(line_inv_qty12.sale_line_ids, line_qty12)
        line_inv_qty11 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 11)
        self.assertEqual(line_inv_qty11.product_id, self.product2)
        self.assertEqual(line_inv_qty11.price_unit, 200)
        self.assertEqual(line_inv_qty11.sale_line_ids, line_qty11)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 90)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11)

    def test_deposit_sale_last_price_inv_sale_line_new_pricelist_2wizlines(
            self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        partner_deposit1.property_product_pricelist = self.new_pricelist.id
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale1.pricelist_id, self.new_pricelist)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale2.pricelist_id, self.new_pricelist)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        sale3 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product2, 10, discount=10, pricelist=self.new_pricelist)
        self.assertEqual(sale2.pricelist_id, self.new_pricelist)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale3.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale3.action_confirm()
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(len(sale3.picking_ids), 1)
        picking_int = sale3.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 10
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product1.id,
                    'qty': 7,
                }),
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product2.id,
                    'qty': 11,
                })
            ],
        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 7)
        self.assertEqual(wizard.line_ids[0].qty_finish, 3)
        self.assertEqual(wizard.line_ids[1].qty, 11)
        self.assertEqual(wizard.line_ids[1].qty_finish, -1)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids[1].force_inventory = True
        wizard.line_ids[1].onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids[0].qty_theorical, 10)
        self.assertEqual(wizard.line_ids[1].qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale3.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(sale3.order_line.qty_to_invoice, 0)
        self.assertEqual(sale3.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 3)
        line_qty7 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(line_qty7)
        self.assertEqual(line_qty7.product_id, self.product1)
        self.assertEqual(line_qty7.price_unit, 1)
        self.assertEqual(line_qty7.discount, 0)
        self.assertEqual(line_qty7.qty_delivered, 7)
        self.assertEqual(line_qty7.qty_to_invoice, 0)
        self.assertEqual(line_qty7.qty_invoiced, 7)
        line_qty10 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 10)
        self.assertTrue(line_qty10)
        self.assertEqual(line_qty10.product_id, self.product2)
        self.assertEqual(line_qty10.price_unit, 2)
        self.assertEqual(line_qty10.discount, 10)
        self.assertEqual(line_qty10.qty_delivered, 10)
        self.assertEqual(line_qty10.qty_to_invoice, 0)
        self.assertEqual(line_qty10.qty_invoiced, 10)
        line_qty1 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertTrue(line_qty1)
        self.assertEqual(line_qty1.product_id, self.product2)
        self.assertEqual(line_qty1.price_unit, 2)
        self.assertEqual(line_qty1.discount, 0)
        self.assertEqual(line_qty1.qty_delivered, 1)
        self.assertEqual(line_qty1.qty_to_invoice, 0)
        self.assertEqual(line_qty1.qty_invoiced, 1)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 3)
        move_qty7 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(move_qty7)
        self.assertEqual(move_qty7.product_id, self.product1)
        self.assertEqual(move_qty7.location_id, deposit_loc1)
        self.assertEqual(move_qty7.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty7.sale_line_id, line_qty7)
        self.assertEqual(move_qty7.sale_line_id.qty_delivered, 7)
        move_qty10 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 10)
        self.assertTrue(move_qty10)
        self.assertEqual(move_qty10.product_id, self.product2)
        self.assertEqual(move_qty10.location_id, deposit_loc1)
        self.assertEqual(move_qty10.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty10.sale_line_id, line_qty10)
        self.assertEqual(move_qty10.sale_line_id.qty_delivered, 10)
        self.assertEqual(new_picking.state, 'done')
        move_qty1 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertTrue(move_qty1)
        self.assertEqual(move_qty1.product_id, self.product2)
        self.assertEqual(move_qty1.location_id, deposit_loc1)
        self.assertEqual(move_qty1.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty1.sale_line_id, line_qty1)
        self.assertEqual(move_qty1.sale_line_id.qty_delivered, 1)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 3)
        line_inv_qty7 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 7)
        self.assertEqual(line_inv_qty7.product_id, self.product1)
        self.assertEqual(line_inv_qty7.price_unit, 1)
        self.assertEqual(line_inv_qty7.discount, 0)
        self.assertEqual(line_inv_qty7.sale_line_ids, line_qty7)
        line_inv_qty10 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 10)
        self.assertEqual(line_inv_qty10.product_id, self.product2)
        self.assertEqual(line_inv_qty10.price_unit, 2)
        self.assertEqual(line_inv_qty10.discount, 10)
        self.assertEqual(line_inv_qty10.sale_line_ids, line_qty10)
        line_inv_qty1 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 1)
        self.assertEqual(line_inv_qty1.product_id, self.product2)
        self.assertEqual(line_inv_qty1.price_unit, 2)
        self.assertEqual(line_inv_qty1.discount, 0)
        self.assertEqual(line_inv_qty1.sale_line_ids, line_qty1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11)

    def test_deposit_sale_last_price_inv_sale_line_new_pricelist_2wizlines2(
            self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        partner_deposit1.property_product_pricelist = self.new_pricelist.id
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, pricelist=self.new_pricelist)
        self.assertEqual(sale1.pricelist_id, self.new_pricelist)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale2.pricelist_id, self.new_pricelist)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        sale3 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product2, 10, discount=10, pricelist=self.new_pricelist)
        self.assertEqual(sale2.pricelist_id, self.new_pricelist)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale3.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale3.action_confirm()
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(len(sale3.picking_ids), 1)
        picking_int = sale3.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 10
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 90)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product1.id,
                    'qty': 7,
                }),
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product2.id,
                    'qty': 11,
                })
            ],
        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 7)
        self.assertEqual(wizard.line_ids[0].qty_finish, -1)
        self.assertEqual(wizard.line_ids[1].qty, 11)
        self.assertEqual(wizard.line_ids[1].qty_finish, -1)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids[0].force_inventory = True
        wizard.line_ids[0].onchange_qty()
        wizard.line_ids[1].force_inventory = True
        wizard.line_ids[1].onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids[0].qty_theorical, 6)
        self.assertEqual(wizard.line_ids[1].qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale3.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(sale3.order_line.qty_to_invoice, 0)
        self.assertEqual(sale3.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 3)
        line_qty7 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(line_qty7)
        self.assertEqual(line_qty7.product_id, self.product1)
        self.assertEqual(line_qty7.price_unit, 1)
        self.assertEqual(line_qty7.discount, 0)
        self.assertEqual(line_qty7.qty_delivered, 7)
        self.assertEqual(line_qty7.qty_to_invoice, 0)
        self.assertEqual(line_qty7.qty_invoiced, 7)
        line_qty10 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 10)
        self.assertTrue(line_qty10)
        self.assertEqual(line_qty10.product_id, self.product2)
        self.assertEqual(line_qty10.price_unit, 2)
        self.assertEqual(line_qty10.discount, 10)
        self.assertEqual(line_qty10.qty_delivered, 10)
        self.assertEqual(line_qty10.qty_to_invoice, 0)
        self.assertEqual(line_qty10.qty_invoiced, 10)
        line_qty1 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertTrue(line_qty1)
        self.assertEqual(line_qty1.product_id, self.product2)
        self.assertEqual(line_qty1.price_unit, 2)
        self.assertEqual(line_qty1.discount, 0)
        self.assertEqual(line_qty1.qty_delivered, 1)
        self.assertEqual(line_qty1.qty_to_invoice, 0)
        self.assertEqual(line_qty1.qty_invoiced, 1)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 3)
        move_qty7 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(move_qty7)
        self.assertEqual(move_qty7.product_id, self.product1)
        self.assertEqual(move_qty7.location_id, deposit_loc1)
        self.assertEqual(move_qty7.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty7.sale_line_id, line_qty7)
        self.assertEqual(move_qty7.sale_line_id.qty_delivered, 7)
        move_qty10 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 10)
        self.assertTrue(move_qty10)
        self.assertEqual(move_qty10.product_id, self.product2)
        self.assertEqual(move_qty10.location_id, deposit_loc1)
        self.assertEqual(move_qty10.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty10.sale_line_id, line_qty10)
        self.assertEqual(move_qty10.sale_line_id.qty_delivered, 10)
        self.assertEqual(new_picking.state, 'done')
        move_qty1 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertTrue(move_qty1)
        self.assertEqual(move_qty1.product_id, self.product2)
        self.assertEqual(move_qty1.location_id, deposit_loc1)
        self.assertEqual(move_qty1.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty1.sale_line_id, line_qty1)
        self.assertEqual(move_qty1.sale_line_id.qty_delivered, 1)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 3)
        line_inv_qty7 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 7)
        self.assertEqual(line_inv_qty7.product_id, self.product1)
        self.assertEqual(line_inv_qty7.price_unit, 1)
        self.assertEqual(line_inv_qty7.discount, 0)
        self.assertEqual(line_inv_qty7.sale_line_ids, line_qty7)
        line_inv_qty10 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 10)
        self.assertEqual(line_inv_qty10.product_id, self.product2)
        self.assertEqual(line_inv_qty10.price_unit, 2)
        self.assertEqual(line_inv_qty10.discount, 10)
        self.assertEqual(line_inv_qty10.sale_line_ids, line_qty10)
        line_inv_qty1 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 1)
        self.assertEqual(line_inv_qty1.product_id, self.product2)
        self.assertEqual(line_inv_qty1.price_unit, 2)
        self.assertEqual(line_inv_qty1.discount, 0)
        self.assertEqual(line_inv_qty1.sale_line_ids, line_qty1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 90)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11)

    def test_deposit_sale_last_price_inv_product_not_sale_line(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product2.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, -7)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 0)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product2)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 55)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product2)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product2)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 55)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_last_price_inv_product_not_sale_line2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product2.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 0 - 7)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 0)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product2)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 55)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product2)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product2)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 55)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_real_fifo_inv_sale_line(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 3)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 2)
        line_qty5 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 5)
        self.assertEqual(line_qty5.product_id, self.product1)
        self.assertEqual(line_qty5.price_unit, 10)
        self.assertEqual(line_qty5.qty_delivered, 5)
        self.assertEqual(line_qty5.qty_to_invoice, 0)
        self.assertEqual(line_qty5.qty_invoiced, 5)
        line_qty2 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 2)
        self.assertEqual(line_qty2.product_id, self.product1)
        self.assertEqual(line_qty2.price_unit, 20)
        self.assertEqual(line_qty2.qty_delivered, 2)
        self.assertEqual(line_qty2.qty_to_invoice, 0)
        self.assertEqual(line_qty2.qty_invoiced, 2)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 2)
        move_qty5 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 5)
        self.assertEqual(move_qty5.product_id, self.product1)
        self.assertEqual(move_qty5.location_id, deposit_loc1)
        self.assertEqual(move_qty5.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty5.sale_line_id, line_qty5)
        self.assertEqual(move_qty5.sale_line_id.qty_delivered, 5)
        move_qty2 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 2)
        self.assertEqual(move_qty2.product_id, self.product1)
        self.assertEqual(move_qty2.location_id, deposit_loc1)
        self.assertEqual(move_qty2.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty2.sale_line_id, line_qty2)
        self.assertEqual(move_qty2.sale_line_id.qty_delivered, 2)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 2)
        line_inv_qty5 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 5)
        self.assertEqual(line_inv_qty5.product_id, self.product1)
        self.assertEqual(line_inv_qty5.price_unit, 10)
        self.assertEqual(line_inv_qty5.sale_line_ids, line_qty5)
        line_inv_qty2 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 2)
        self.assertEqual(line_inv_qty2.product_id, self.product1)
        self.assertEqual(line_inv_qty2.price_unit, 20)
        self.assertEqual(line_inv_qty2.sale_line_ids, line_qty2)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_real_fifo_inv_sale_line2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 6 - 7)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 6)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 3)
        line_qty5 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 5)
        self.assertEqual(line_qty5.product_id, self.product1)
        self.assertEqual(line_qty5.price_unit, 20)
        self.assertEqual(line_qty5.qty_delivered, 5)
        self.assertEqual(line_qty5.qty_to_invoice, 0)
        self.assertEqual(line_qty5.qty_invoiced, 5)
        line_qty1_price10 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1 and ln.price_unit == 10)
        self.assertEqual(line_qty1_price10.product_id, self.product1)
        self.assertEqual(line_qty1_price10.qty_delivered, 1)
        self.assertEqual(line_qty1_price10.qty_to_invoice, 0)
        self.assertEqual(line_qty1_price10.qty_invoiced, 1)
        line_qty1_price100 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1 and ln.price_unit == 100)
        self.assertEqual(line_qty1_price100.product_id, self.product1)
        self.assertEqual(line_qty1_price100.qty_delivered, 1)
        self.assertEqual(line_qty1_price100.qty_to_invoice, 0)
        self.assertEqual(line_qty1_price100.qty_invoiced, 1)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 3)
        move_qty5 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 5)
        self.assertEqual(move_qty5.product_id, self.product1)
        self.assertEqual(move_qty5.location_id, deposit_loc1)
        self.assertEqual(move_qty5.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty5.sale_line_id, line_qty5)
        self.assertEqual(move_qty5.sale_line_id.qty_delivered, 5)
        moves_qty1 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertEqual(moves_qty1[0].product_id, self.product1)
        self.assertEqual(moves_qty1[0].location_id, deposit_loc1)
        self.assertEqual(moves_qty1[0].location_dest_id, self.customer_loc)
        self.assertEqual(moves_qty1[0].sale_line_id, line_qty1_price10)
        self.assertEqual(moves_qty1[0].sale_line_id.qty_delivered, 1)
        self.assertEqual(moves_qty1[1].product_id, self.product1)
        self.assertEqual(moves_qty1[1].location_id, deposit_loc1)
        self.assertEqual(moves_qty1[1].location_dest_id, self.customer_loc)
        self.assertEqual(moves_qty1[1].sale_line_id, line_qty1_price100)
        self.assertEqual(moves_qty1[1].sale_line_id.qty_delivered, 1)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 3)
        line_inv_qty5 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 5)
        self.assertEqual(line_inv_qty5.product_id, self.product1)
        self.assertEqual(line_inv_qty5.price_unit, 20)
        self.assertEqual(line_inv_qty5.sale_line_ids, line_qty5)
        line_inv_qty1_price10 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 1 and ln.price_unit == 10)
        self.assertEqual(line_inv_qty1_price10.product_id, self.product1)
        self.assertEqual(
            line_inv_qty1_price10.sale_line_ids, line_qty1_price10)
        line_inv_qty1_price100 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 1 and ln.price_unit == 100)
        self.assertEqual(line_inv_qty1_price100.product_id, self.product1)
        self.assertEqual(
            line_inv_qty1_price100.sale_line_ids, line_qty1_price100)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_real_fifo_inv_more_qty(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 12,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 12)
        self.assertEqual(wizard.line_ids.qty_finish, -2)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 3)
        line_qty5_price20 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 5 and ln.price_unit == 20)
        self.assertEqual(line_qty5_price20.product_id, self.product1)
        self.assertEqual(line_qty5_price20.qty_delivered, 5)
        self.assertEqual(line_qty5_price20.qty_to_invoice, 0)
        self.assertEqual(line_qty5_price20.qty_invoiced, 5)
        line_qty5_price10 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 5 and ln.price_unit == 10)
        self.assertEqual(line_qty5_price10.product_id, self.product1)
        self.assertEqual(line_qty5_price10.qty_delivered, 5)
        self.assertEqual(line_qty5_price10.qty_to_invoice, 0)
        self.assertEqual(line_qty5_price10.qty_invoiced, 5)
        line_qty2 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 2)
        self.assertEqual(line_qty2.product_id, self.product1)
        self.assertEqual(line_qty2.price_unit, 100)
        self.assertEqual(line_qty2.qty_delivered, 2)
        self.assertEqual(line_qty2.qty_to_invoice, 0)
        self.assertEqual(line_qty2.qty_invoiced, 2)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 3)
        moves_qty5 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 5)
        self.assertEqual(len(moves_qty5), 2)
        for move in moves_qty5:
            self.assertEqual(move.product_id, self.product1)
            self.assertEqual(move.location_id, deposit_loc1)
            self.assertEqual(move.location_dest_id, self.customer_loc)
            self.assertEqual(move.sale_line_id.qty_delivered, 5)
        move_sale_line_price10 = moves_qty5.filtered(
            lambda ln: ln.sale_line_id == line_qty5_price10)
        self.assertEqual(len(move_sale_line_price10), 1)
        move_sale_line_price20 = moves_qty5.filtered(
            lambda ln: ln.sale_line_id == line_qty5_price20)
        self.assertEqual(len(move_sale_line_price20), 1)
        move_qty2 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 2)
        self.assertEqual(move_qty2.product_id, self.product1)
        self.assertEqual(move_qty2.location_id, deposit_loc1)
        self.assertEqual(move_qty2.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty2.sale_line_id, line_qty2)
        self.assertEqual(move_qty2.sale_line_id.qty_delivered, 2)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 3)
        inv_line_qty5_price20 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 5 and ln.price_unit == 20)
        self.assertEqual(inv_line_qty5_price20.product_id, self.product1)
        self.assertEqual(
            inv_line_qty5_price20.sale_line_ids, line_qty5_price20)
        inv_line_qty5_price10 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 5 and ln.price_unit == 10)
        self.assertEqual(inv_line_qty5_price10.product_id, self.product1)
        self.assertEqual(
            inv_line_qty5_price10.sale_line_ids, line_qty5_price10)
        inv_line_qty2 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 2)
        self.assertEqual(inv_line_qty2.product_id, self.product1)
        self.assertEqual(inv_line_qty2.price_unit, 100)
        self.assertEqual(inv_line_qty2.sale_line_ids, line_qty2)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12)

    def test_deposit_sale_real_fifo_inv_more_qty2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 12,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 12)
        self.assertEqual(wizard.line_ids.qty_finish, -6)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 6)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 3)
        line_qty1 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertEqual(line_qty1.product_id, self.product1)
        self.assertEqual(line_qty1.price_unit, 10)
        self.assertEqual(line_qty1.qty_delivered, 1)
        self.assertEqual(line_qty1.qty_to_invoice, 0)
        self.assertEqual(line_qty1.qty_invoiced, 1)
        line_qty5 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 5)
        self.assertEqual(line_qty5.product_id, self.product1)
        self.assertEqual(line_qty5.price_unit, 20)
        self.assertEqual(line_qty5.qty_delivered, 5)
        self.assertEqual(line_qty5.qty_to_invoice, 0)
        self.assertEqual(line_qty5.qty_invoiced, 5)
        line_qty6 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 6)
        self.assertEqual(line_qty6.product_id, self.product1)
        self.assertEqual(line_qty6.price_unit, 100)
        self.assertEqual(line_qty6.qty_delivered, 6)
        self.assertEqual(line_qty6.qty_to_invoice, 0)
        self.assertEqual(line_qty6.qty_invoiced, 6)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 3)
        move_qty1 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertEqual(move_qty1.product_id, self.product1)
        self.assertEqual(move_qty1.location_id, deposit_loc1)
        self.assertEqual(move_qty1.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty1.sale_line_id, line_qty1)
        self.assertEqual(move_qty1.sale_line_id.qty_delivered, 1)
        move_qty5 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 5)
        self.assertEqual(move_qty5.product_id, self.product1)
        self.assertEqual(move_qty5.location_id, deposit_loc1)
        self.assertEqual(move_qty5.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty5.sale_line_id, line_qty5)
        self.assertEqual(move_qty5.sale_line_id.qty_delivered, 5)
        move_qty6 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 6)
        self.assertEqual(move_qty6.product_id, self.product1)
        self.assertEqual(move_qty6.location_id, deposit_loc1)
        self.assertEqual(move_qty6.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty6.sale_line_id, line_qty6)
        self.assertEqual(move_qty6.sale_line_id.qty_delivered, 6)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 3)
        inv_line_qty1 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 1)
        self.assertEqual(inv_line_qty1.product_id, self.product1)
        self.assertEqual(inv_line_qty1.price_unit, 10)
        self.assertEqual(inv_line_qty1.sale_line_ids, line_qty1)
        inv_line_qty5 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 5)
        self.assertEqual(inv_line_qty5.product_id, self.product1)
        self.assertEqual(inv_line_qty5.price_unit, 20)
        self.assertEqual(inv_line_qty5.sale_line_ids, line_qty5)
        inv_line_qty6 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 6)
        self.assertEqual(inv_line_qty6.product_id, self.product1)
        self.assertEqual(inv_line_qty6.price_unit, 100)
        self.assertEqual(inv_line_qty6.sale_line_ids, line_qty6)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12)

    def test_deposit_sale_real_fifo_inv_not_sale_line(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 55 - 7)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 55)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 2)
        line_qty5 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 5)
        self.assertEqual(line_qty5.product_id, self.product1)
        self.assertEqual(line_qty5.price_unit, 10)
        self.assertEqual(line_qty5.qty_delivered, 5)
        self.assertEqual(line_qty5.qty_to_invoice, 0)
        self.assertEqual(line_qty5.qty_invoiced, 5)
        line_qty2 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 2)
        self.assertEqual(line_qty2.product_id, self.product1)
        self.assertEqual(line_qty2.price_unit, 100)
        self.assertEqual(line_qty2.qty_delivered, 2)
        self.assertEqual(line_qty2.qty_to_invoice, 0)
        self.assertEqual(line_qty2.qty_invoiced, 2)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 2)
        move_qty5 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 5)
        self.assertEqual(move_qty5.product_id, self.product1)
        self.assertEqual(move_qty5.product_uom_qty, 5)
        self.assertEqual(move_qty5.location_id, deposit_loc1)
        self.assertEqual(move_qty5.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty5.sale_line_id, line_qty5)
        self.assertEqual(move_qty5.sale_line_id.qty_delivered, 5)
        move_qty2 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 2)
        self.assertEqual(move_qty2.product_id, self.product1)
        self.assertEqual(move_qty2.product_uom_qty, 2)
        self.assertEqual(move_qty2.location_id, deposit_loc1)
        self.assertEqual(move_qty2.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty2.sale_line_id, line_qty2)
        self.assertEqual(move_qty2.sale_line_id.qty_delivered, 2)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 2)
        inv_line_qty5 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 5)
        self.assertEqual(inv_line_qty5.product_id, self.product1)
        self.assertEqual(inv_line_qty5.price_unit, 10)
        self.assertEqual(inv_line_qty5.sale_line_ids, line_qty5)
        inv_line_qty2 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 2)
        self.assertEqual(inv_line_qty2.product_id, self.product1)
        self.assertEqual(inv_line_qty2.price_unit, 100)
        self.assertEqual(inv_line_qty2.sale_line_ids, line_qty2)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 7)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_real_fifo_inv_not_sale_line2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 55 - 7)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 55)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 2)
        line_qty1_price10 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1 and ln.price_unit == 10)
        self.assertEqual(line_qty1_price10.product_id, self.product1)
        self.assertEqual(line_qty1_price10.qty_delivered, 1)
        self.assertEqual(line_qty1_price10.qty_to_invoice, 0)
        self.assertEqual(line_qty1_price10.qty_invoiced, 1)
        line_qty6_price100 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 6 and ln.price_unit == 100)
        self.assertEqual(line_qty6_price100.product_id, self.product1)
        self.assertEqual(line_qty6_price100.qty_delivered, 6)
        self.assertEqual(line_qty6_price100.qty_to_invoice, 0)
        self.assertEqual(line_qty6_price100.qty_invoiced, 6)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 2)
        move_qty1 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertEqual(len(move_qty1), 1)
        self.assertEqual(move_qty1.product_id, self.product1)
        self.assertEqual(move_qty1.location_id, deposit_loc1)
        self.assertEqual(move_qty1.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty1.sale_line_id, line_qty1_price10)
        self.assertEqual(move_qty1.sale_line_id.qty_delivered, 1)
        move_qty6 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 6)
        self.assertEqual(move_qty6.product_id, self.product1)
        self.assertEqual(move_qty6.location_id, deposit_loc1)
        self.assertEqual(move_qty6.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty6.sale_line_id, line_qty6_price100)
        self.assertEqual(move_qty6.sale_line_id.qty_delivered, 6)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 2)
        inv_line_qty1_price10 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 1)
        self.assertEqual(inv_line_qty1_price10.product_id, self.product1)
        self.assertEqual(inv_line_qty1_price10.price_unit, 10)
        self.assertEqual(
            inv_line_qty1_price10.sale_line_ids, line_qty1_price10)
        inv_line_qty6_price100 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 6)
        self.assertEqual(inv_line_qty6_price100.product_id, self.product1)
        self.assertEqual(inv_line_qty6_price100.price_unit, 100)
        self.assertEqual(
            inv_line_qty6_price100.sale_line_ids, line_qty6_price100)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 7)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_real_fifo_inv_not_sale_line_more_qty(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 30,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 30)
        self.assertEqual(wizard.line_ids.qty_finish, 55 - 30)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 55)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 2)
        line_qty5_price10 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 5 and ln.price_unit == 10)
        self.assertEqual(line_qty5_price10.product_id, self.product1)
        self.assertEqual(line_qty5_price10.qty_delivered, 5)
        self.assertEqual(line_qty5_price10.qty_to_invoice, 0)
        self.assertEqual(line_qty5_price10.qty_invoiced, 5)
        line_qty25 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 25)
        self.assertEqual(line_qty25.product_id, self.product1)
        self.assertEqual(line_qty25.price_unit, 100)
        self.assertEqual(line_qty25.qty_delivered, 25)
        self.assertEqual(line_qty25.qty_to_invoice, 0)
        self.assertEqual(line_qty25.qty_invoiced, 25)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 2)
        move_qty5 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 5)
        self.assertEqual(len(move_qty5), 1)
        self.assertEqual(move_qty5.product_id, self.product1)
        self.assertEqual(move_qty5.location_id, deposit_loc1)
        self.assertEqual(move_qty5.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty5.sale_line_id.qty_delivered, 5)
        move_qty25 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 25)
        self.assertEqual(len(move_qty25), 1)
        self.assertEqual(move_qty25.product_id, self.product1)
        self.assertEqual(move_qty25.location_id, deposit_loc1)
        self.assertEqual(move_qty25.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty25.sale_line_id.qty_delivered, 25)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 2)
        inv_line_qty5_price10 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 5 and ln.price_unit == 10)
        self.assertEqual(inv_line_qty5_price10.product_id, self.product1)
        self.assertEqual(
            inv_line_qty5_price10.sale_line_ids, line_qty5_price10)
        inv_line_qty25_price100 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 25 and ln.price_unit == 100)
        self.assertEqual(inv_line_qty25_price100.product_id, self.product1)
        self.assertEqual(inv_line_qty25_price100.sale_line_ids, line_qty25)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 30)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 30)

    def test_deposit_sale_real_fifo_inv_not_sale_line_more_qty2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 30,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 30)
        self.assertEqual(wizard.line_ids.qty_finish, 55 - 30)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 55)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 2)
        line_qty1 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertEqual(line_qty1.product_id, self.product1)
        self.assertEqual(line_qty1.price_unit, 10)
        self.assertEqual(line_qty1.qty_delivered, 1)
        self.assertEqual(line_qty1.qty_to_invoice, 0)
        self.assertEqual(line_qty1.qty_invoiced, 1)
        line_qty29 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 29)
        self.assertEqual(line_qty29.product_id, self.product1)
        self.assertEqual(line_qty29.price_unit, 100)
        self.assertEqual(line_qty29.qty_delivered, 29)
        self.assertEqual(line_qty29.qty_to_invoice, 0)
        self.assertEqual(line_qty29.qty_invoiced, 29)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 2)
        move_qty1 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertEqual(move_qty1.product_id, self.product1)
        self.assertEqual(move_qty1.location_id, deposit_loc1)
        self.assertEqual(move_qty1.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty1.sale_line_id, line_qty1)
        self.assertEqual(move_qty1.sale_line_id.qty_delivered, 1)
        move_qty29 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 29)
        self.assertEqual(move_qty29.product_id, self.product1)
        self.assertEqual(move_qty29.location_id, deposit_loc1)
        self.assertEqual(move_qty29.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty29.sale_line_id, line_qty29)
        self.assertEqual(move_qty29.sale_line_id.qty_delivered, 29)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 2)
        inv_line_qty1 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 1)
        self.assertEqual(inv_line_qty1.product_id, self.product1)
        self.assertEqual(inv_line_qty1.price_unit, 10)
        self.assertEqual(inv_line_qty1.sale_line_ids, line_qty1)
        inv_line_qty29 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 29)
        self.assertEqual(inv_line_qty29.product_id, self.product1)
        self.assertEqual(inv_line_qty29.price_unit, 100)
        self.assertEqual(inv_line_qty29.sale_line_ids, line_qty29)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 30)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 30)

    def test_deposit_sale_real_fifo_inv_sale_line_new_pricelist(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        partner_deposit1.property_product_pricelist = self.new_pricelist.id
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale1.pricelist_id, self.new_pricelist)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale2.pricelist_id, self.new_pricelist)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 3)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 1)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_real_fifo_inv_sale_line_new_pricelist2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        partner_deposit1.property_product_pricelist = self.new_pricelist.id
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, pricelist=self.new_pricelist)
        self.assertEqual(sale1.pricelist_id, self.new_pricelist)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale2.pricelist_id, self.new_pricelist)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 6 - 7)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 6)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 1)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_real_fifo_inv_not_sale_line_new_pricelist(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        partner_deposit1.property_product_pricelist = self.new_pricelist.id
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale1.pricelist_id, self.new_pricelist)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale2.pricelist_id, self.new_pricelist)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 55 - 7)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 55)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 1)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 7)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_real_fifo_inv_not_sale_line_new_pricelist2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        partner_deposit1.property_product_pricelist = self.new_pricelist.id
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, pricelist=self.new_pricelist)
        self.assertEqual(sale1.pricelist_id, self.new_pricelist)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale2.pricelist_id, self.new_pricelist)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 55 - 7)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 55)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 1)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 7)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_real_fifo_inv_more_qty_new_pricelist(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        partner_deposit1.property_product_pricelist = self.new_pricelist.id
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale1.pricelist_id, self.new_pricelist)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale2.pricelist_id, self.new_pricelist)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 12,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 12)
        self.assertEqual(wizard.line_ids.qty_finish, 10 - 12)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 12)
        self.assertEqual(new_sale.order_line.price_unit, 1)
        self.assertEqual(new_sale.order_line.qty_delivered, 12)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 12)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 12)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 12)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 12)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12)

    def test_deposit_sale_real_fifo_inv_more_qty_new_pricelist2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        partner_deposit1.property_product_pricelist = self.new_pricelist.id
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, pricelist=self.new_pricelist)
        self.assertEqual(sale1.pricelist_id, self.new_pricelist)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale2.pricelist_id, self.new_pricelist)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 12,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 12)
        self.assertEqual(wizard.line_ids.qty_finish, 6 - 12)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 6)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 12)
        self.assertEqual(new_sale.order_line.price_unit, 1)
        self.assertEqual(new_sale.order_line.qty_delivered, 12)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 12)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 12)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 12)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 12)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12)

    def test_deposit_sale_real_fifo_inv_sale_line_2wizlines(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        sale3 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product2, 10, price_forced=200)
        self.assertEqual(sale3.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale3.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale3.action_confirm()
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(len(sale3.picking_ids), 1)
        picking_int = sale3.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 10
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product1.id,
                    'qty': 7,
                }),
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product2.id,
                    'qty': 11,
                })
            ],
        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 7)
        self.assertEqual(wizard.line_ids[0].qty_finish, 3)
        self.assertEqual(wizard.line_ids[1].qty, 11)
        self.assertEqual(wizard.line_ids[1].qty_finish, -1)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids[1].force_inventory = True
        wizard.line_ids[1].onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids[0].qty_theorical, 10)
        self.assertEqual(wizard.line_ids[1].qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale3.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(sale3.order_line.qty_to_invoice, 0)
        self.assertEqual(sale3.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 4)
        line_qty5 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 5)
        self.assertEqual(line_qty5.product_id, self.product1)
        self.assertEqual(line_qty5.price_unit, 10)
        self.assertEqual(line_qty5.qty_delivered, 5)
        self.assertEqual(line_qty5.qty_to_invoice, 0)
        self.assertEqual(line_qty5.qty_invoiced, 5)
        line_qty2 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 2)
        self.assertEqual(line_qty2.product_id, self.product1)
        self.assertEqual(line_qty2.price_unit, 20)
        self.assertEqual(line_qty2.qty_delivered, 2)
        self.assertEqual(line_qty2.qty_to_invoice, 0)
        self.assertEqual(line_qty2.qty_invoiced, 2)
        line_qty10 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 10)
        self.assertEqual(line_qty10.product_id, self.product2)
        self.assertEqual(line_qty10.price_unit, 200)
        self.assertEqual(line_qty10.qty_delivered, 10)
        self.assertEqual(line_qty10.qty_to_invoice, 0)
        self.assertEqual(line_qty10.qty_invoiced, 10)
        line_qty1 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertEqual(line_qty1.product_id, self.product2)
        self.assertEqual(line_qty1.price_unit, 55)
        self.assertEqual(line_qty1.qty_delivered, 1)
        self.assertEqual(line_qty1.qty_to_invoice, 0)
        self.assertEqual(line_qty1.qty_invoiced, 1)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 4)
        move_qty5 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 5)
        self.assertEqual(move_qty5.product_id, self.product1)
        self.assertEqual(move_qty5.location_id, deposit_loc1)
        self.assertEqual(move_qty5.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty5.sale_line_id, line_qty5)
        self.assertEqual(move_qty5.sale_line_id.qty_delivered, 5)
        move_qty2 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 2)
        self.assertEqual(move_qty2.product_id, self.product1)
        self.assertEqual(move_qty2.location_id, deposit_loc1)
        self.assertEqual(move_qty2.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty2.sale_line_id, line_qty2)
        self.assertEqual(move_qty2.sale_line_id.qty_delivered, 2)
        move_qty10 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 10)
        self.assertEqual(move_qty10.product_id, self.product2)
        self.assertEqual(move_qty10.location_id, deposit_loc1)
        self.assertEqual(move_qty10.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty10.sale_line_id, line_qty10)
        self.assertEqual(move_qty10.sale_line_id.qty_delivered, 10)
        move_qty1 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertEqual(move_qty1.product_id, self.product2)
        self.assertEqual(move_qty1.location_id, deposit_loc1)
        self.assertEqual(move_qty1.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty1.sale_line_id, line_qty1)
        self.assertEqual(move_qty1.sale_line_id.qty_delivered, 1)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 4)
        inv_line_qty5 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 5)
        self.assertEqual(inv_line_qty5.product_id, self.product1)
        self.assertEqual(inv_line_qty5.price_unit, 10)
        self.assertEqual(inv_line_qty5.sale_line_ids, line_qty5)
        inv_line_qty2 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 2)
        self.assertEqual(inv_line_qty2.product_id, self.product1)
        self.assertEqual(inv_line_qty2.price_unit, 20)
        self.assertEqual(inv_line_qty2.sale_line_ids, line_qty2)
        inv_line_qty10 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 10)
        self.assertEqual(inv_line_qty10.product_id, self.product2)
        self.assertEqual(inv_line_qty10.price_unit, 200)
        self.assertEqual(inv_line_qty10.sale_line_ids, line_qty10)
        inv_line_qty1 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 1)
        self.assertEqual(inv_line_qty1.product_id, self.product2)
        self.assertEqual(inv_line_qty1.price_unit, 55)
        self.assertEqual(inv_line_qty1.sale_line_ids, line_qty1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11)

    def test_deposit_sale_real_fifo_inv_sale_line_2wizlines2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        sale3 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product2, 10, price_forced=200)
        self.assertEqual(sale3.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale3.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale3.action_confirm()
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(len(sale3.picking_ids), 1)
        picking_int = sale3.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 10
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 90)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product1.id,
                    'qty': 7,
                }),
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product2.id,
                    'qty': 11,
                })
            ],
        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 7)
        self.assertEqual(wizard.line_ids[0].qty_finish, -1)
        self.assertEqual(wizard.line_ids[1].qty, 11)
        self.assertEqual(wizard.line_ids[1].qty_finish, -1)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids[0].force_inventory = True
        wizard.line_ids[0].onchange_qty()
        wizard.line_ids[1].force_inventory = True
        wizard.line_ids[1].onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids[0].qty_theorical, 6)
        self.assertEqual(wizard.line_ids[1].qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale3.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(sale3.order_line.qty_to_invoice, 0)
        self.assertEqual(sale3.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 5)
        line_qty5 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 5)
        self.assertEqual(line_qty5.product_id, self.product1)
        self.assertEqual(line_qty5.price_unit, 20)
        self.assertEqual(line_qty5.qty_delivered, 5)
        self.assertEqual(line_qty5.qty_to_invoice, 0)
        self.assertEqual(line_qty5.qty_invoiced, 5)
        line_qty1_price10 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1 and ln.price_unit == 10)
        self.assertEqual(line_qty1_price10.product_id, self.product1)
        self.assertEqual(line_qty1_price10.qty_delivered, 1)
        self.assertEqual(line_qty1_price10.qty_to_invoice, 0)
        self.assertEqual(line_qty1_price10.qty_invoiced, 1)
        line_qty1_price100 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1 and ln.price_unit == 100)
        self.assertEqual(line_qty1_price100.product_id, self.product1)
        self.assertEqual(line_qty1_price100.qty_delivered, 1)
        self.assertEqual(line_qty1_price100.qty_to_invoice, 0)
        self.assertEqual(line_qty1_price100.qty_invoiced, 1)
        line_prod2_qty1 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1
            and ln.product_id == self.product2)
        self.assertEqual(line_prod2_qty1.qty_delivered, 1)
        self.assertEqual(line_prod2_qty1.qty_to_invoice, 0)
        self.assertEqual(line_prod2_qty1.qty_invoiced, 1)
        line_prod2_qty10 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 10
            and ln.product_id == self.product2)
        self.assertEqual(line_prod2_qty10.qty_delivered, 10)
        self.assertEqual(line_prod2_qty10.qty_to_invoice, 0)
        self.assertEqual(line_prod2_qty10.qty_invoiced, 10)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 5)
        move_qty5 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 5)
        self.assertEqual(move_qty5.product_id, self.product1)
        self.assertEqual(move_qty5.location_id, deposit_loc1)
        self.assertEqual(move_qty5.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty5.sale_line_id, line_qty5)
        self.assertEqual(move_qty5.sale_line_id.qty_delivered, 5)
        moves_qty1 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 1
            and ln.product_id == self.product1)
        self.assertEqual(len(moves_qty1), 2)
        self.assertEqual(moves_qty1[0].product_id, self.product1)
        self.assertEqual(moves_qty1[0].location_id, deposit_loc1)
        self.assertEqual(moves_qty1[0].location_dest_id, self.customer_loc)
        self.assertEqual(moves_qty1[0].sale_line_id, line_qty1_price10)
        self.assertEqual(moves_qty1[0].sale_line_id.qty_delivered, 1)
        self.assertEqual(moves_qty1[1].product_id, self.product1)
        self.assertEqual(moves_qty1[1].location_id, deposit_loc1)
        self.assertEqual(moves_qty1[1].location_dest_id, self.customer_loc)
        self.assertEqual(moves_qty1[1].sale_line_id, line_qty1_price100)
        self.assertEqual(moves_qty1[1].sale_line_id.qty_delivered, 1)
        move_qty10 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 10)
        self.assertEqual(move_qty10.product_id, self.product2)
        self.assertEqual(move_qty10.location_id, deposit_loc1)
        self.assertEqual(move_qty10.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty10.sale_line_id, line_prod2_qty10)
        self.assertEqual(move_qty10.sale_line_id.qty_delivered, 10)
        move_qty1 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 1
            and ln.product_id == self.product2)
        self.assertEqual(move_qty1.product_id, self.product2)
        self.assertEqual(move_qty1.location_id, deposit_loc1)
        self.assertEqual(move_qty1.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty1.sale_line_id, line_prod2_qty1)
        self.assertEqual(move_qty1.sale_line_id.qty_delivered, 1)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 5)
        inv_line_qty5 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 5)
        self.assertEqual(inv_line_qty5.product_id, self.product1)
        self.assertEqual(inv_line_qty5.price_unit, 20)
        self.assertEqual(inv_line_qty5.sale_line_ids, line_qty5)
        inv_line_prod1_qty1_price10 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 1 and ln.product_id == self.product1
            and ln.price_unit == 10)
        self.assertEqual(
            inv_line_prod1_qty1_price10.sale_line_ids, line_qty1_price10)
        inv_line_prod1_qty1_price100 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 1 and ln.product_id == self.product1
            and ln.price_unit == 100)
        self.assertEqual(
            inv_line_prod1_qty1_price100.sale_line_ids, line_qty1_price100)
        inv_line_prod2_qty10 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 10 and ln.product_id == self.product2)
        self.assertEqual(
            inv_line_prod2_qty10.sale_line_ids, line_prod2_qty10)
        inv_line_prod2_qty1 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 1 and ln.product_id == self.product2)
        self.assertEqual(
            inv_line_prod2_qty1.sale_line_ids, line_prod2_qty1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 90)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11)

    def test_deposit_sale_real_fifo_inv_not_sale_line_2wizlines(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        sale3 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product2, 10, price_forced=200)
        self.assertEqual(sale3.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale3.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale3.action_confirm()
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(len(sale3.picking_ids), 1)
        picking_int = sale3.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 10
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product1.id,
                    'qty': 7,
                }),
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product2.id,
                    'qty': 11,
                })
            ],
        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 7)
        self.assertEqual(wizard.line_ids[1].qty, 11)
        self.assertEqual(wizard.line_ids[0].qty_finish, 55 - 7)
        self.assertEqual(wizard.line_ids[1].qty_finish, -1)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids[1].force_inventory = True
        wizard.line_ids[1].onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids[0].qty_theorical, 55)
        self.assertEqual(wizard.line_ids[1].qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale3.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(sale3.order_line.qty_to_invoice, 0)
        self.assertEqual(sale3.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 4)
        line_qty5 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 5)
        self.assertEqual(line_qty5.product_id, self.product1)
        self.assertEqual(line_qty5.price_unit, 10)
        self.assertEqual(line_qty5.qty_delivered, 5)
        self.assertEqual(line_qty5.qty_to_invoice, 0)
        self.assertEqual(line_qty5.qty_invoiced, 5)
        line_qty2 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 2)
        self.assertEqual(line_qty2.product_id, self.product1)
        self.assertEqual(line_qty2.price_unit, 100)
        self.assertEqual(line_qty2.qty_delivered, 2)
        self.assertEqual(line_qty2.qty_to_invoice, 0)
        self.assertEqual(line_qty2.qty_invoiced, 2)
        line_qty10 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 10)
        self.assertEqual(line_qty10.product_id, self.product2)
        self.assertEqual(line_qty10.price_unit, 200)
        self.assertEqual(line_qty10.qty_delivered, 10)
        self.assertEqual(line_qty10.qty_to_invoice, 0)
        self.assertEqual(line_qty10.qty_invoiced, 10)
        line_qty1 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertEqual(line_qty1.product_id, self.product2)
        self.assertEqual(line_qty1.price_unit, 55)
        self.assertEqual(line_qty1.qty_delivered, 1)
        self.assertEqual(line_qty1.qty_to_invoice, 0)
        self.assertEqual(line_qty1.qty_invoiced, 1)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 4)
        move_qty5 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 5)
        self.assertEqual(move_qty5.product_id, self.product1)
        self.assertEqual(move_qty5.location_id, deposit_loc1)
        self.assertEqual(move_qty5.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty5.sale_line_id, line_qty5)
        self.assertEqual(move_qty5.sale_line_id.qty_delivered, 5)
        move_qty2 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 2)
        self.assertEqual(move_qty2.product_id, self.product1)
        self.assertEqual(move_qty2.location_id, deposit_loc1)
        self.assertEqual(move_qty2.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty2.sale_line_id, line_qty2)
        self.assertEqual(move_qty2.sale_line_id.qty_delivered, 2)
        move_qty10 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 10)
        self.assertEqual(move_qty10.product_id, self.product2)
        self.assertEqual(move_qty10.location_id, deposit_loc1)
        self.assertEqual(move_qty10.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty10.sale_line_id, line_qty10)
        self.assertEqual(move_qty10.sale_line_id.qty_delivered, 10)
        move_qty1 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertEqual(move_qty1.product_id, self.product2)
        self.assertEqual(move_qty1.location_id, deposit_loc1)
        self.assertEqual(move_qty1.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty1.sale_line_id, line_qty1)
        self.assertEqual(move_qty1.sale_line_id.qty_delivered, 1)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 4)
        inv_line_qty5 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 5)
        self.assertEqual(inv_line_qty5.product_id, self.product1)
        self.assertEqual(inv_line_qty5.price_unit, 10)
        self.assertEqual(inv_line_qty5.sale_line_ids, line_qty5)
        inv_line_qty2 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 2)
        self.assertEqual(inv_line_qty2.product_id, self.product1)
        self.assertEqual(inv_line_qty2.price_unit, 100)
        self.assertEqual(inv_line_qty2.sale_line_ids, line_qty2)
        inv_line_qty10 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 10)
        self.assertEqual(inv_line_qty10.product_id, self.product2)
        self.assertEqual(inv_line_qty10.price_unit, 200)
        self.assertEqual(inv_line_qty10.sale_line_ids, line_qty10)
        inv_line_qty1 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 1)
        self.assertEqual(inv_line_qty1.product_id, self.product2)
        self.assertEqual(inv_line_qty1.price_unit, 55)
        self.assertEqual(inv_line_qty1.sale_line_ids, line_qty1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 7)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11)

    def test_deposit_sale_real_fifo_inv_more_qty_2wizlines(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        sale3 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product2, 10, price_forced=200)
        self.assertEqual(sale3.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale3.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale3.action_confirm()
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(len(sale3.picking_ids), 1)
        picking_int = sale3.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 10
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product1.id,
                    'qty': 12,
                }),
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product2.id,
                    'qty': 11,
                })
            ],
        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 12)
        self.assertEqual(wizard.line_ids[0].qty_finish, -2)
        self.assertEqual(wizard.line_ids[1].qty, 11)
        self.assertEqual(wizard.line_ids[1].qty_finish, -1)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids[0].force_inventory = True
        wizard.line_ids[0].onchange_qty()
        wizard.line_ids[1].force_inventory = True
        wizard.line_ids[1].onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids[0].qty_theorical, 10)
        self.assertEqual(wizard.line_ids[1].qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale3.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(sale3.order_line.qty_to_invoice, 0)
        self.assertEqual(sale3.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 5)
        line_qty5_price10 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 5 and ln.price_unit == 10)
        self.assertEqual(line_qty5_price10.product_id, self.product1)
        self.assertEqual(line_qty5_price10.qty_delivered, 5)
        self.assertEqual(line_qty5_price10.qty_to_invoice, 0)
        self.assertEqual(line_qty5_price10.qty_invoiced, 5)
        line_qty5_price20 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 5 and ln.price_unit == 20)
        self.assertEqual(line_qty5_price20.product_id, self.product1)
        self.assertEqual(line_qty5_price20.qty_delivered, 5)
        self.assertEqual(line_qty5_price20.qty_to_invoice, 0)
        self.assertEqual(line_qty5_price20.qty_invoiced, 5)
        line_qty2 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 2)
        self.assertEqual(line_qty2.product_id, self.product1)
        self.assertEqual(line_qty2.price_unit, 100)
        self.assertEqual(line_qty2.qty_delivered, 2)
        self.assertEqual(line_qty2.qty_to_invoice, 0)
        self.assertEqual(line_qty2.qty_invoiced, 2)
        line_qty10 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 10)
        self.assertEqual(line_qty10.product_id, self.product2)
        self.assertEqual(line_qty10.price_unit, 200)
        self.assertEqual(line_qty10.qty_delivered, 10)
        self.assertEqual(line_qty10.qty_to_invoice, 0)
        self.assertEqual(line_qty10.qty_invoiced, 10)
        line_qty1 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertEqual(line_qty1.product_id, self.product2)
        self.assertEqual(line_qty1.price_unit, 55)
        self.assertEqual(line_qty1.qty_delivered, 1)
        self.assertEqual(line_qty1.qty_to_invoice, 0)
        self.assertEqual(line_qty1.qty_invoiced, 1)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 5)
        moves_qty5 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 5)
        self.assertEqual(len(moves_qty5), 2)
        for move in moves_qty5:
            self.assertEqual(move.product_id, self.product1)
            self.assertEqual(move.location_id, deposit_loc1)
            self.assertEqual(move.location_dest_id, self.customer_loc)
            self.assertEqual(move.sale_line_id.qty_delivered, 5)
        move_sale_line_price10 = moves_qty5.filtered(
            lambda ln: ln.sale_line_id == line_qty5_price10)
        self.assertEqual(len(move_sale_line_price10), 1)
        move_sale_line_price20 = moves_qty5.filtered(
            lambda ln: ln.sale_line_id == line_qty5_price20)
        self.assertEqual(len(move_sale_line_price20), 1)
        move_qty2 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 2)
        self.assertEqual(move_qty2.product_id, self.product1)
        self.assertEqual(move_qty2.location_id, deposit_loc1)
        self.assertEqual(move_qty2.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty2.sale_line_id, line_qty2)
        self.assertEqual(move_qty2.sale_line_id.qty_delivered, 2)
        move_qty10 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 10)
        self.assertEqual(move_qty10.product_id, self.product2)
        self.assertEqual(move_qty10.location_id, deposit_loc1)
        self.assertEqual(move_qty10.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty10.sale_line_id, line_qty10)
        self.assertEqual(move_qty10.sale_line_id.qty_delivered, 10)
        move_qty1 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertEqual(move_qty1.product_id, self.product2)
        self.assertEqual(move_qty1.location_id, deposit_loc1)
        self.assertEqual(move_qty1.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty1.sale_line_id, line_qty1)
        self.assertEqual(move_qty1.sale_line_id.qty_delivered, 1)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 5)
        inv_line_qty5_price10 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 5 and ln.price_unit == 10)
        self.assertEqual(inv_line_qty5_price10.product_id, self.product1)
        self.assertEqual(
            inv_line_qty5_price10.sale_line_ids, line_qty5_price10)
        inv_line_qty5_price20 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 5 and ln.price_unit == 20)
        self.assertEqual(inv_line_qty5_price20.product_id, self.product1)
        self.assertEqual(
            inv_line_qty5_price20.sale_line_ids, line_qty5_price20)
        inv_line_qty2 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 2)
        self.assertEqual(inv_line_qty2.product_id, self.product1)
        self.assertEqual(inv_line_qty2.price_unit, 100)
        self.assertEqual(inv_line_qty2.sale_line_ids, line_qty2)
        inv_line_qty10 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 10)
        self.assertEqual(inv_line_qty10.product_id, self.product2)
        self.assertEqual(inv_line_qty10.price_unit, 200)
        self.assertEqual(inv_line_qty10.sale_line_ids, line_qty10)
        inv_line_qty1 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 1)
        self.assertEqual(inv_line_qty1.product_id, self.product2)
        self.assertEqual(inv_line_qty1.price_unit, 55)
        self.assertEqual(inv_line_qty1.sale_line_ids, line_qty1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11)

    def test_deposit_sale_real_fifo_inv_sale_line_new_pricelist_2wizlines(
            self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        partner_deposit1.property_product_pricelist = self.new_pricelist.id
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale1.pricelist_id, self.new_pricelist)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, pricelist=self.new_pricelist)
        self.assertEqual(sale2.pricelist_id, self.new_pricelist)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        sale3 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product2, 10, discount=10, pricelist=self.new_pricelist)
        self.assertEqual(sale2.pricelist_id, self.new_pricelist)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale3.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale3.action_confirm()
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(len(sale3.picking_ids), 1)
        picking_int = sale3.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 10
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product1.id,
                    'qty': 7,
                }),
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product2.id,
                    'qty': 11,
                })
            ],
        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 7)
        self.assertEqual(wizard.line_ids[0].qty_finish, 3)
        self.assertEqual(wizard.line_ids[1].qty, 11)
        self.assertEqual(wizard.line_ids[1].qty_finish, -1)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids[1].force_inventory = True
        wizard.line_ids[1].onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids[0].qty_theorical, 10)
        self.assertEqual(wizard.line_ids[1].qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale3.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(sale3.order_line.qty_to_invoice, 0)
        self.assertEqual(sale3.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 3)
        line_qty7 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(line_qty7)
        self.assertEqual(line_qty7.product_id, self.product1)
        self.assertEqual(line_qty7.price_unit, 1)
        self.assertEqual(line_qty7.qty_delivered, 7)
        self.assertEqual(line_qty7.qty_to_invoice, 0)
        self.assertEqual(line_qty7.qty_invoiced, 7)
        line_qty10 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 10)
        self.assertTrue(line_qty10)
        self.assertEqual(line_qty10.product_id, self.product2)
        self.assertEqual(line_qty10.price_unit, 2)
        self.assertEqual(line_qty10.discount, 10)
        self.assertEqual(line_qty10.qty_delivered, 10)
        self.assertEqual(line_qty10.qty_to_invoice, 0)
        self.assertEqual(line_qty10.qty_invoiced, 10)
        line_qty1 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertTrue(line_qty1)
        self.assertEqual(line_qty1.product_id, self.product2)
        self.assertEqual(line_qty1.price_unit, 2)
        self.assertEqual(line_qty1.discount, 0)
        self.assertEqual(line_qty1.qty_delivered, 1)
        self.assertEqual(line_qty1.qty_to_invoice, 0)
        self.assertEqual(line_qty1.qty_invoiced, 1)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(len(new_picking.move_lines), 3)
        move_qty7 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(move_qty7)
        self.assertEqual(move_qty7.product_id, self.product1)
        self.assertEqual(move_qty7.location_id, deposit_loc1)
        self.assertEqual(move_qty7.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty7.sale_line_id, line_qty7)
        self.assertEqual(move_qty7.sale_line_id.qty_delivered, 7)
        move_qty10 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 10)
        self.assertTrue(move_qty10)
        self.assertEqual(move_qty10.product_id, self.product2)
        self.assertEqual(move_qty10.location_id, deposit_loc1)
        self.assertEqual(move_qty10.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty10.sale_line_id, line_qty10)
        self.assertEqual(move_qty10.sale_line_id.qty_delivered, 10)
        move_qty1 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertTrue(move_qty1)
        self.assertEqual(move_qty1.product_id, self.product2)
        self.assertEqual(move_qty1.location_id, deposit_loc1)
        self.assertEqual(move_qty1.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty1.sale_line_id, line_qty1)
        self.assertEqual(move_qty1.sale_line_id.qty_delivered, 1)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 3)
        line_inv_qty7 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 7)
        self.assertEqual(line_inv_qty7.product_id, self.product1)
        self.assertEqual(line_inv_qty7.price_unit, 1)
        self.assertEqual(line_inv_qty7.discount, 0)
        self.assertEqual(line_inv_qty7.sale_line_ids, line_qty7)
        line_inv_qty10 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 10)
        self.assertEqual(line_inv_qty10.product_id, self.product2)
        self.assertEqual(line_inv_qty10.price_unit, 2)
        self.assertEqual(line_inv_qty10.discount, 10)
        self.assertEqual(line_inv_qty10.sale_line_ids, line_qty10)
        line_inv_qty1 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 1)
        self.assertEqual(line_inv_qty1.product_id, self.product2)
        self.assertEqual(line_inv_qty1.price_unit, 2)
        self.assertEqual(line_inv_qty1.discount, 0)
        self.assertEqual(line_inv_qty1.sale_line_ids, line_qty1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11)

    def test_deposit_sale_real_fifo_inv_product_not_sale_line(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product2.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, -7)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 0)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product2)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 55)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product2)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product2)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 55)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_constrains_only_one_line_for_each_product(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        with self.assertRaises(ValidationError):
            self.env['stock.deposit'].create({
                'create_invoice': True,
                'warehouse_id': self.wh_stock.id,
                'location_id': deposit_loc1.id,
                'partner_id': partner_deposit1_ship.id,
                'price_option': 'last_price',
                'line_ids': [
                    (0, 0, {
                        'ttype': 'sale',
                        'product_id': self.product1.id,
                        'qty': 12,
                    }),
                    (0, 0, {
                        'ttype': 'sale',
                        'product_id': self.product1.id,
                        'qty': 11,
                    })
                ],
            })

    def test_deposit_return_customer_last_price_inv_sale_line_no_create_inv(
            self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': False,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 10 - 7)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'to invoice')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 7)
        self.assertEqual(new_sale.order_line.qty_invoiced, 0)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.move_line_ids.location_dest_id,
            self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': False,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale_return_customer',
                'product_id': self.product1.id,
                'qty': 2,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 3 + 2)
        wizard.action_confirm()
        new_picking_return = self.env['stock.picking'].search(
            [], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return), 1)
        self.assertEqual(new_picking_return.location_id, self.customer_loc)
        self.assertEqual(new_picking_return.location_dest_id, deposit_loc1)
        self.assertEqual(len(new_picking_return.move_lines), 1)
        self.assertEqual(
            new_picking_return.move_lines.product_id, self.product1)
        self.assertEqual(new_picking_return.move_lines.product_uom_qty, 2)
        self.assertEqual(
            new_picking_return.move_lines.location_id, self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.location_dest_id, deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_id,
            self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_dest_id,
            deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id.qty_delivered, 7 - 2)
        self.assertEqual(new_picking_return.state, 'done')
        self.assertEqual(len(new_sale.invoice_ids), 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3 + 2)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7 - 2)
        new_sale = new_picking_return.move_lines.sale_line_id.order_id
        self.assertEqual(len(new_sale), 1)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 5)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 5)
        self.assertEqual(new_sale.order_line.qty_invoiced, 0)

    def test_deposit_return_customer_last_price_inv_sale_line_2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 2,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 6 - 2)
        wizard.action_confirm()
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 2)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 2)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 2)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 2)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.move_line_ids.location_dest_id,
            self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 2)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 2)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 4)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 2)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale_return_customer',
                'product_id': self.product1.id,
                'qty': 2,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 4 + 2)
        wizard.action_confirm()
        new_picking_return = self.env['stock.picking'].search(
            [], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return), 1)
        self.assertEqual(new_picking_return.location_id, self.customer_loc)
        self.assertEqual(new_picking_return.location_dest_id, deposit_loc1)
        self.assertEqual(len(new_picking_return.move_lines), 1)
        self.assertEqual(
            new_picking_return.move_lines.product_id, self.product1)
        self.assertEqual(new_picking_return.move_lines.product_uom_qty, 2)
        self.assertEqual(
            new_picking_return.move_lines.location_id, self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.location_dest_id, deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_id,
            self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_dest_id,
            deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id.qty_delivered, 2 - 2)
        self.assertEqual(new_picking_return.state, 'done')
        self.assertEqual(len(new_sale.invoice_ids), 2)
        new_invoice_return = new_sale.invoice_ids.filtered(
            lambda inv: inv.type == 'out_refund')
        self.assertEqual(len(new_invoice_return), 1)
        self.assertEqual(len(new_invoice_return.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice_return.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice_return.invoice_line_ids.quantity, 2)
        self.assertEqual(new_invoice_return.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice_return.invoice_line_ids.sale_line_ids,
            new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 4 + 2)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 2 - 2)
        new_sale = new_picking_return.move_lines.sale_line_id.order_id
        self.assertEqual(len(new_sale), 1)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 2)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 2 - 2)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 2 - 2)

    def test_deposit_return_customer_last_price_inv_more_qty(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 12,
            })],
        })

        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 12)
        self.assertEqual(wizard.line_ids.qty_finish, 10 - 12)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 12)
        self.assertEqual(wizard.line_ids.qty_finish, 0)
        wizard.action_confirm()
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 12)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 12)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 12)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 12)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 12)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 12)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale_return_customer',
                'product_id': self.product1.id,
                'qty': 2,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 0 + 2)
        wizard.action_confirm()
        new_picking_return = self.env['stock.picking'].search(
            [], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return), 1)
        self.assertEqual(new_picking_return.location_id, self.customer_loc)
        self.assertEqual(new_picking_return.location_dest_id, deposit_loc1)
        self.assertEqual(len(new_picking_return.move_lines), 1)
        self.assertEqual(new_picking_return.move_lines.product_id, self.product1)
        self.assertEqual(new_picking_return.move_lines.product_uom_qty, 2)
        self.assertEqual(
            new_picking_return.move_lines.location_id, self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.location_dest_id, deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_id,
            self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_dest_id,
            deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id.qty_delivered, 12 - 2)
        self.assertEqual(new_picking_return.state, 'done')
        self.assertEqual(len(new_sale.invoice_ids), 2)
        new_invoice_return = new_sale.invoice_ids.filtered(
            lambda inv: inv.type == 'out_refund')
        self.assertEqual(len(new_invoice_return), 1)
        self.assertEqual(len(new_invoice_return.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice_return.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice_return.invoice_line_ids.quantity, 2)
        self.assertEqual(new_invoice_return.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice_return.invoice_line_ids.sale_line_ids,
            new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0 + 2)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12 - 2)
        new_sale = new_picking_return.move_lines.sale_line_id.order_id
        self.assertEqual(len(new_sale), 1)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 12)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 12 - 2)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 12 - 2)

    def test_deposit_return_customer_last_price_inv_more_qty2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 12,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 12)
        self.assertEqual(wizard.line_ids.qty_finish, -6)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 6)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 12)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 12)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 12)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 12)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 12)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 12)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale_return_customer',
                'product_id': self.product1.id,
                'qty': 2,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 0 + 2)
        wizard.action_confirm()
        new_picking_return = self.env['stock.picking'].search(
            [], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return), 1)
        self.assertEqual(new_picking_return.location_id, self.customer_loc)
        self.assertEqual(new_picking_return.location_dest_id, deposit_loc1)
        self.assertEqual(len(new_picking_return.move_lines), 1)
        self.assertEqual(new_picking_return.move_lines.product_id, self.product1)
        self.assertEqual(new_picking_return.move_lines.product_uom_qty, 2)
        self.assertEqual(
            new_picking_return.move_lines.location_id, self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.location_dest_id, deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_id,
            self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_dest_id,
            deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id.qty_delivered, 12 - 2)
        self.assertEqual(new_picking_return.state, 'done')
        self.assertEqual(len(new_sale.invoice_ids), 2)
        new_invoice_return = new_sale.invoice_ids.filtered(
            lambda inv: inv.type == 'out_refund')
        self.assertEqual(len(new_invoice_return), 1)
        self.assertEqual(len(new_invoice_return.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice_return.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice_return.invoice_line_ids.quantity, 2)
        self.assertEqual(new_invoice_return.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice_return.invoice_line_ids.sale_line_ids,
            new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0 + 2)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12 - 2)
        new_sale = new_picking_return.move_lines.sale_line_id.order_id
        self.assertEqual(len(new_sale), 1)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 12)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 12 - 2)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 12 - 2)

    def test_deposit_return_customer_last_price_no_inv_more_qty(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': False,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 12,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 12)
        self.assertEqual(wizard.line_ids.qty_finish, -2)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'to invoice')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 12)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 12)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 12)
        self.assertEqual(new_sale.order_line.qty_invoiced, 0)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 12)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 12)
        self.assertEqual(new_picking.state, 'done')
        self.assertFalse(new_sale.invoice_ids)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale_return_customer',
                'product_id': self.product1.id,
                'qty': 2,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 0 + 2)
        wizard.action_confirm()
        new_picking_return = self.env['stock.picking'].search(
            [], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return), 1)
        self.assertEqual(new_picking_return.location_id, self.customer_loc)
        self.assertEqual(new_picking_return.location_dest_id, deposit_loc1)
        self.assertEqual(len(new_picking_return.move_lines), 1)
        self.assertEqual(
            new_picking_return.move_lines.product_id, self.product1)
        self.assertEqual(new_picking_return.move_lines.product_uom_qty, 2)
        self.assertEqual(
            new_picking_return.move_lines.location_id, self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.location_dest_id, deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_id,
            self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_dest_id,
            deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id.qty_delivered, 12 - 2)
        self.assertEqual(new_picking_return.state, 'done')
        self.assertEqual(len(new_sale.invoice_ids), 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0 + 2)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12 - 2)
        new_sale = new_picking_return.move_lines.sale_line_id.order_id
        self.assertEqual(len(new_sale), 1)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 12)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 12 - 2)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 10)
        self.assertEqual(new_sale.order_line.qty_invoiced, 0)

    def test_deposit_return_customer_last_price_no_inv_more_qty2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': False,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 12,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 12)
        self.assertEqual(wizard.line_ids.qty_finish, -6)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 6)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'to invoice')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 12)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 12)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 12)
        self.assertEqual(new_sale.order_line.qty_invoiced, 0)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 12)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 12)
        self.assertEqual(new_picking.state, 'done')
        self.assertFalse(new_sale.invoice_ids)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale_return_customer',
                'product_id': self.product1.id,
                'qty': 2,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 0 + 2)
        wizard.action_confirm()
        new_picking_return = self.env['stock.picking'].search(
            [], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return), 1)
        self.assertEqual(new_picking_return.location_id, self.customer_loc)
        self.assertEqual(new_picking_return.location_dest_id, deposit_loc1)
        self.assertEqual(len(new_picking_return.move_lines), 1)
        self.assertEqual(
            new_picking_return.move_lines.product_id, self.product1)
        self.assertEqual(new_picking_return.move_lines.product_uom_qty, 2)
        self.assertEqual(
            new_picking_return.move_lines.location_id, self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.location_dest_id, deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_id,
            self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_dest_id,
            deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id.qty_delivered, 12 - 2)
        self.assertEqual(new_picking_return.state, 'done')
        self.assertEqual(len(new_sale.invoice_ids), 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0 + 2)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12 - 2)
        new_sale = new_picking_return.move_lines.sale_line_id.order_id
        self.assertEqual(len(new_sale), 1)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 12)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 12 - 2)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 10)
        self.assertEqual(new_sale.order_line.qty_invoiced, 0)

    def test_deposit_return_customer_last_price_inv_not_sale_line(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 55 - 7)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 55)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 7)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale_return_customer',
                'product_id': self.product1.id,
                'qty': 2,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 48 + 2)
        wizard.action_confirm()
        new_picking_return = self.env['stock.picking'].search(
            [], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return), 1)
        self.assertEqual(new_picking_return.location_id, self.customer_loc)
        self.assertEqual(new_picking_return.location_dest_id, deposit_loc1)
        self.assertEqual(len(new_picking_return.move_lines), 1)
        self.assertEqual(new_picking_return.move_lines.product_id, self.product1)
        self.assertEqual(new_picking_return.move_lines.product_uom_qty, 2)
        self.assertEqual(
            new_picking_return.move_lines.location_id, self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.location_dest_id, deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_id,
            self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_dest_id,
            deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id.qty_delivered, 7 - 2)
        self.assertEqual(new_picking_return.state, 'done')
        self.assertEqual(len(new_sale.invoice_ids), 2)
        new_invoice_return = new_sale.invoice_ids.filtered(
            lambda inv: inv.type == 'out_refund')
        self.assertEqual(len(new_invoice_return), 1)
        self.assertEqual(len(new_invoice_return.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice_return.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice_return.invoice_line_ids.quantity, 2)
        self.assertEqual(new_invoice_return.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice_return.invoice_line_ids.sale_line_ids,
            new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 48 + 2)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7 - 2)
        new_sale = new_picking_return.move_lines.sale_line_id.order_id
        self.assertEqual(len(new_sale), 1)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 7 - 2)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7 - 2)

    def test_deposit_return_customer_last_price_inv_not_sale_line2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 55 - 7)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 55)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 7)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale_return_customer',
                'product_id': self.product1.id,
                'qty': 2,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 48 + 2)
        wizard.action_confirm()
        new_picking_return = self.env['stock.picking'].search(
            [], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return), 1)
        self.assertEqual(new_picking_return.location_id, self.customer_loc)
        self.assertEqual(new_picking_return.location_dest_id, deposit_loc1)
        self.assertEqual(len(new_picking_return.move_lines), 1)
        self.assertEqual(new_picking_return.move_lines.product_id, self.product1)
        self.assertEqual(new_picking_return.move_lines.product_uom_qty, 2)
        self.assertEqual(
            new_picking_return.move_lines.location_id, self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.location_dest_id, deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_id,
            self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_dest_id,
            deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id.qty_delivered, 7 - 2)
        self.assertEqual(new_picking_return.state, 'done')
        self.assertEqual(len(new_sale.invoice_ids), 2)
        new_invoice_return = new_sale.invoice_ids.filtered(
            lambda inv: inv.type == 'out_refund')
        self.assertEqual(len(new_invoice_return), 1)
        self.assertEqual(len(new_invoice_return.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice_return.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice_return.invoice_line_ids.quantity, 2)
        self.assertEqual(new_invoice_return.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice_return.invoice_line_ids.sale_line_ids,
            new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 48 + 2)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7 - 2)
        new_sale = new_picking_return.move_lines.sale_line_id.order_id
        self.assertEqual(len(new_sale), 1)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 7 - 2)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7 - 2)

    def test_deposit_return_customer_last_price_inv_not_sale_line_more_qty(
            self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 30,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 30)
        self.assertEqual(wizard.line_ids.qty_finish, 55 - 30)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 55)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 30)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 30)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 30)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 30)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 30)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 30)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 30)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 30)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale_return_customer',
                'product_id': self.product1.id,
                'qty': 2,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 25 + 2)
        wizard.action_confirm()
        new_picking_return = self.env['stock.picking'].search(
            [], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return), 1)
        self.assertEqual(new_picking_return.location_id, self.customer_loc)
        self.assertEqual(new_picking_return.location_dest_id, deposit_loc1)
        self.assertEqual(len(new_picking_return.move_lines), 1)
        self.assertEqual(new_picking_return.move_lines.product_id, self.product1)
        self.assertEqual(new_picking_return.move_lines.product_uom_qty, 2)
        self.assertEqual(
            new_picking_return.move_lines.location_id, self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.location_dest_id, deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_id,
            self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_dest_id,
            deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id.qty_delivered, 30 - 2)
        self.assertEqual(new_picking_return.state, 'done')
        self.assertEqual(len(new_sale.invoice_ids), 2)
        new_invoice_return = new_sale.invoice_ids.filtered(
            lambda inv: inv.type == 'out_refund')
        self.assertEqual(len(new_invoice_return), 1)
        self.assertEqual(len(new_invoice_return.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice_return.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice_return.invoice_line_ids.quantity, 2)
        self.assertEqual(new_invoice_return.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice_return.invoice_line_ids.sale_line_ids,
            new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 25 + 2)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 30 - 2)
        new_sale = new_picking_return.move_lines.sale_line_id.order_id
        self.assertEqual(len(new_sale), 1)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 30)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 30 - 2)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 30 - 2)

    def test_deposit_return_customer_last_price_inv_not_sale_line_more_qty2(
            self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 30,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 30)
        self.assertEqual(wizard.line_ids.qty_finish, 55 - 30)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 55)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 30)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 30)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 30)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 30)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 30)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 30)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 30)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 30)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale_return_customer',
                'product_id': self.product1.id,
                'qty': 2,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 25 + 2)
        wizard.action_confirm()
        new_picking_return = self.env['stock.picking'].search(
            [], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return), 1)
        self.assertEqual(new_picking_return.location_id, self.customer_loc)
        self.assertEqual(new_picking_return.location_dest_id, deposit_loc1)
        self.assertEqual(len(new_picking_return.move_lines), 1)
        self.assertEqual(new_picking_return.move_lines.product_id, self.product1)
        self.assertEqual(new_picking_return.move_lines.product_uom_qty, 2)
        self.assertEqual(
            new_picking_return.move_lines.location_id, self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.location_dest_id, deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_id,
            self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_dest_id,
            deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id.qty_delivered, 30 - 2)
        self.assertEqual(new_picking_return.state, 'done')
        self.assertEqual(len(new_sale.invoice_ids), 2)
        new_invoice_return = new_sale.invoice_ids.filtered(
            lambda inv: inv.type == 'out_refund')
        self.assertEqual(len(new_invoice_return), 1)
        self.assertEqual(len(new_invoice_return.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice_return.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice_return.invoice_line_ids.quantity, 2)
        self.assertEqual(new_invoice_return.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice_return.invoice_line_ids.sale_line_ids,
            new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 25 + 2)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 30 - 2)
        new_sale = new_picking_return.move_lines.sale_line_id.order_id
        self.assertEqual(len(new_sale), 1)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 30)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 30 - 2)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 30 - 2)

    def test_deposit_return_customer_last_price_inv_sale_line_2wizlines(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        sale3 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product2, 10, price_forced=200)
        self.assertEqual(sale3.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale3.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale3.action_confirm()
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(len(sale3.picking_ids), 1)
        picking_int = sale3.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 10
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product1.id,
                    'qty': 7,
                }),
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product2.id,
                    'qty': 11,
                })
            ],
        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 7)
        self.assertEqual(wizard.line_ids[0].qty_finish, 3)
        self.assertEqual(wizard.line_ids[1].qty, 11)
        self.assertEqual(wizard.line_ids[1].qty_finish, -1)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids[1].force_inventory = True
        wizard.line_ids[1].onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids[0].qty_theorical, 10)
        self.assertEqual(wizard.line_ids[1].qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale3.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(sale3.order_line.qty_to_invoice, 0)
        self.assertEqual(sale3.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 2)
        line_qty7 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(line_qty7)
        self.assertEqual(line_qty7.product_id, self.product1)
        self.assertEqual(line_qty7.product_uom_qty, 7)
        self.assertEqual(line_qty7.price_unit, 20)
        self.assertEqual(line_qty7.qty_delivered, 7)
        self.assertEqual(line_qty7.qty_to_invoice, 0)
        self.assertEqual(line_qty7.qty_invoiced, 7)
        line_qty11 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(line_qty11)
        self.assertEqual(line_qty11.product_id, self.product2)
        self.assertEqual(line_qty11.product_uom_qty, 11)
        self.assertEqual(line_qty11.price_unit, 200)
        self.assertEqual(line_qty11.qty_delivered, 11)
        self.assertEqual(line_qty11.qty_to_invoice, 0)
        self.assertEqual(line_qty11.qty_invoiced, 11)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 2)
        move_qty7 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(move_qty7)
        self.assertEqual(move_qty7.product_id, self.product1)
        self.assertEqual(move_qty7.location_id, deposit_loc1)
        self.assertEqual(move_qty7.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty7.sale_line_id, line_qty7)
        self.assertEqual(move_qty7.sale_line_id.qty_delivered, 7)
        move_qty11 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(move_qty11)
        self.assertEqual(move_qty11.product_id, self.product2)
        self.assertEqual(move_qty11.location_id, deposit_loc1)
        self.assertEqual(move_qty11.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty11.sale_line_id, line_qty11)
        self.assertEqual(move_qty11.sale_line_id.qty_delivered, 11)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 2)
        line_inv_qty7 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 7)
        self.assertEqual(line_inv_qty7.product_id, self.product1)
        self.assertEqual(line_inv_qty7.price_unit, 20)
        self.assertEqual(line_inv_qty7.sale_line_ids, line_qty7)
        line_inv_qty11 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 11)
        self.assertEqual(line_inv_qty11.product_id, self.product2)
        self.assertEqual(line_inv_qty11.price_unit, 200)
        self.assertEqual(line_inv_qty11.sale_line_ids, line_qty11)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale_return_customer',
                'product_id': self.product1.id,
                'qty': 2,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 3 + 2)
        wizard.action_confirm()
        new_picking_return = self.env['stock.picking'].search(
            [], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return), 1)
        self.assertEqual(new_picking_return.location_id, self.customer_loc)
        self.assertEqual(new_picking_return.location_dest_id, deposit_loc1)
        self.assertEqual(len(new_picking_return.move_lines), 1)
        self.assertEqual(new_picking_return.move_lines.product_id, self.product1)
        self.assertEqual(new_picking_return.move_lines.product_uom_qty, 2)
        self.assertEqual(
            new_picking_return.move_lines.location_id, self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.location_dest_id, deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_id,
            self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_dest_id,
            deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id,
            new_sale.order_line.filtered(
                lambda ln: ln.product_id == self.product1))
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id.qty_delivered, 7 - 2)
        self.assertEqual(new_picking_return.state, 'done')
        self.assertEqual(len(new_sale.invoice_ids), 2)
        new_invoice_return = new_sale.invoice_ids.filtered(
            lambda inv: inv.type == 'out_refund')
        self.assertEqual(len(new_invoice_return), 1)
        self.assertEqual(len(new_invoice_return.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice_return.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice_return.invoice_line_ids.quantity, 2)
        self.assertEqual(new_invoice_return.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice_return.invoice_line_ids.sale_line_ids,
            new_sale.order_line.filtered(
                lambda ln: ln.product_id == self.product1))
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3 + 2)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7 - 2)
        new_sale = new_picking_return.move_lines.sale_line_id.order_id
        self.assertEqual(len(new_sale), 1)
        order_line_product1 = (
            new_sale.order_line.filtered(
                lambda ln: ln.product_id == self.product1))
        self.assertEqual(len(order_line_product1), 1)
        self.assertEqual(order_line_product1.product_id, self.product1)
        self.assertEqual(order_line_product1.product_uom_qty, 7)
        self.assertEqual(order_line_product1.price_unit, 20)
        self.assertEqual(order_line_product1.qty_delivered, 7 - 2)
        self.assertEqual(order_line_product1.qty_to_invoice, 0)
        self.assertEqual(order_line_product1.qty_invoiced, 7 - 2)

    def test_deposit_return_customer_last_price_inv_sale_line_2wizlines2(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 100)
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 100)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 100)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 99)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        sale3 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product2, 10, price_forced=200)
        self.assertEqual(sale3.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale3.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale3.action_confirm()
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(len(sale3.picking_ids), 1)
        picking_int = sale3.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 10
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 90)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product1.id,
                    'qty': 7,
                }),
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product2.id,
                    'qty': 11,
                })
            ],
        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 7)
        self.assertEqual(wizard.line_ids[0].qty_finish, -1)
        self.assertEqual(wizard.line_ids[1].qty, 11)
        self.assertEqual(wizard.line_ids[1].qty_finish, -1)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids[0].force_inventory = True
        wizard.line_ids[0].onchange_qty()
        wizard.line_ids[1].force_inventory = True
        wizard.line_ids[1].onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids[0].qty_theorical, 6)
        self.assertEqual(wizard.line_ids[1].qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale3.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(sale3.order_line.qty_to_invoice, 0)
        self.assertEqual(sale3.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 2)
        line_qty7 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(line_qty7)
        self.assertEqual(line_qty7.product_id, self.product1)
        self.assertEqual(line_qty7.product_uom_qty, 7)
        self.assertEqual(line_qty7.price_unit, 20)
        self.assertEqual(line_qty7.qty_delivered, 7)
        self.assertEqual(line_qty7.qty_to_invoice, 0)
        self.assertEqual(line_qty7.qty_invoiced, 7)
        line_qty11 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(line_qty11)
        self.assertEqual(line_qty11.product_id, self.product2)
        self.assertEqual(line_qty11.product_uom_qty, 11)
        self.assertEqual(line_qty11.price_unit, 200)
        self.assertEqual(line_qty11.qty_delivered, 11)
        self.assertEqual(line_qty11.qty_to_invoice, 0)
        self.assertEqual(line_qty11.qty_invoiced, 11)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 2)
        move_qty7 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(move_qty7)
        self.assertEqual(move_qty7.product_id, self.product1)
        self.assertEqual(move_qty7.location_id, deposit_loc1)
        self.assertEqual(move_qty7.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty7.sale_line_id, line_qty7)
        self.assertEqual(move_qty7.sale_line_id.qty_delivered, 7)
        move_qty11 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(move_qty11)
        self.assertEqual(move_qty11.product_id, self.product2)
        self.assertEqual(move_qty11.location_id, deposit_loc1)
        self.assertEqual(move_qty11.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty11.sale_line_id, line_qty11)
        self.assertEqual(move_qty11.sale_line_id.qty_delivered, 11)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 2)
        line_inv_qty7 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 7)
        self.assertEqual(line_inv_qty7.product_id, self.product1)
        self.assertEqual(line_inv_qty7.price_unit, 20)
        self.assertEqual(line_inv_qty7.sale_line_ids, line_qty7)
        line_inv_qty11 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 11)
        self.assertEqual(line_inv_qty11.product_id, self.product2)
        self.assertEqual(line_inv_qty11.price_unit, 200)
        self.assertEqual(line_inv_qty11.sale_line_ids, line_qty11)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 90)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale_return_customer',
                    'product_id': self.product1.id,
                    'qty': 2,
                }),
                (0, 0, {
                    'ttype': 'sale_return_customer',
                    'product_id': self.product2.id,
                    'qty': 12,
                })
            ],

        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 2)
        self.assertEqual(wizard.line_ids[0].qty_finish, 2)
        self.assertEqual(wizard.line_ids[1].qty, 12)
        self.assertEqual(wizard.line_ids[1].qty_finish, 12)
        wizard.action_confirm()
        new_picking_return = self.env['stock.picking'].search(
            [], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return), 1)
        self.assertEqual(new_picking_return.location_id, self.customer_loc)
        self.assertEqual(new_picking_return.location_dest_id, deposit_loc1)
        self.assertEqual(len(new_picking_return.move_lines), 2)
        move_return_product1 = new_picking_return.move_lines.filtered(
            lambda m: m.product_id == self.product1)
        self.assertEqual(move_return_product1.product_id, self.product1)
        self.assertEqual(move_return_product1.product_uom_qty, 2)
        self.assertEqual(move_return_product1.location_id, self.customer_loc)
        self.assertEqual(move_return_product1.location_dest_id, deposit_loc1)
        self.assertEqual(
            move_return_product1.move_line_ids.location_id, self.customer_loc)
        self.assertEqual(
            move_return_product1.move_line_ids.location_dest_id, deposit_loc1)
        self.assertEqual(
            move_return_product1.sale_line_id,
            new_sale.order_line.filtered(
                lambda ln: ln.product_id == self.product1))
        self.assertEqual(
            move_return_product1.sale_line_id.qty_delivered, 7 - 2)
        move_return_product2 = new_picking_return.move_lines.filtered(
            lambda m: m.product_id == self.product2)
        self.assertEqual(move_return_product2.product_id, self.product2)
        self.assertEqual(move_return_product2.product_uom_qty, 12)
        self.assertEqual(move_return_product2.location_id, self.customer_loc)
        self.assertEqual(move_return_product2.location_dest_id, deposit_loc1)
        self.assertEqual(
            move_return_product2.move_line_ids.location_id, self.customer_loc)
        self.assertEqual(
            move_return_product2.move_line_ids.location_dest_id, deposit_loc1)
        self.assertEqual(
            move_return_product2.sale_line_id,
            new_sale.order_line.filtered(
                lambda ln: ln.product_id == self.product2))
        self.assertEqual(
            move_return_product2.sale_line_id.qty_delivered, 11 - 12)
        self.assertEqual(new_picking_return.state, 'done')
        self.assertEqual(len(new_sale.invoice_ids), 2)
        new_invoice_return = new_sale.invoice_ids.filtered(
            lambda inv: inv.type == 'out_refund')
        self.assertEqual(len(new_invoice_return), 1)
        self.assertEqual(len(new_invoice_return.invoice_line_ids), 2)
        invline_return_product1 = new_invoice_return.invoice_line_ids.filtered(
            lambda m: m.product_id == self.product1)
        self.assertEqual(invline_return_product1.product_id, self.product1)
        self.assertEqual(invline_return_product1.quantity, 2)
        self.assertEqual(invline_return_product1.price_unit, 20)
        self.assertEqual(
            invline_return_product1.sale_line_ids,
            new_sale.order_line.filtered(
                lambda ln: ln.product_id == self.product1))
        invline_return_product2 = new_invoice_return.invoice_line_ids.filtered(
            lambda m: m.product_id == self.product2)
        self.assertEqual(invline_return_product2.product_id, self.product2)
        self.assertEqual(invline_return_product2.quantity, 12)
        self.assertEqual(invline_return_product2.price_unit, 200)
        self.assertEqual(
            invline_return_product2.sale_line_ids,
            new_sale.order_line.filtered(
                lambda ln: ln.product_id == self.product2))
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 94)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 2)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7 - 2)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 90)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 12)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11 - 12)
        new_sale = new_picking_return.move_lines[0].sale_line_id.order_id
        self.assertEqual(len(new_sale), 1)
        order_line_product1 = (
            new_sale.order_line.filtered(
                lambda ln: ln.product_id == self.product1))
        self.assertEqual(len(order_line_product1), 1)
        self.assertEqual(order_line_product1.product_id, self.product1)
        self.assertEqual(order_line_product1.product_uom_qty, 7)
        self.assertEqual(order_line_product1.price_unit, 20)
        self.assertEqual(order_line_product1.qty_delivered, 7 - 2)
        self.assertEqual(order_line_product1.qty_to_invoice, 0)
        self.assertEqual(order_line_product1.qty_invoiced, 7 - 2)
        order_line_product2 = (
            new_sale.order_line.filtered(
                lambda ln: ln.product_id == self.product2))
        self.assertEqual(len(order_line_product2), 1)
        self.assertEqual(order_line_product2.product_id, self.product2)
        self.assertEqual(order_line_product2.product_uom_qty, 11)
        self.assertEqual(order_line_product2.price_unit, 200)
        self.assertEqual(order_line_product2.qty_delivered, 11 - 12)
        self.assertEqual(order_line_product2.qty_to_invoice, 0)
        self.assertEqual(order_line_product2.qty_invoiced, 11 - 12)

    def test_deposit_return_customer_last_price_inv_not_sale_line_2wizlines(
            self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        # Create inventory adjust to set 50 instead of 5 units.
        self.update_qty_on_hand(self.product1, deposit_loc1, 50)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        sale3 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product2, 10, price_forced=200)
        self.assertEqual(sale3.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale3.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale3.action_confirm()
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(len(sale3.picking_ids), 1)
        picking_int = sale3.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 10
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product1.id,
                    'qty': 7,
                }),
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product2.id,
                    'qty': 11,
                })
            ],
        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 7)
        self.assertEqual(wizard.line_ids[1].qty, 11)
        self.assertEqual(wizard.line_ids[0].qty_finish, 55 - 7)
        self.assertEqual(wizard.line_ids[1].qty_finish, 10 - 11)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids[1].force_inventory = True
        wizard.line_ids[1].onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids[0].qty_theorical, 55)
        self.assertEqual(wizard.line_ids[1].qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale3.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(sale3.order_line.qty_to_invoice, 0)
        self.assertEqual(sale3.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 2)
        line_qty7 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(line_qty7)
        self.assertEqual(line_qty7.product_id, self.product1)
        self.assertEqual(line_qty7.product_uom_qty, 7)
        self.assertEqual(line_qty7.price_unit, 20)
        self.assertEqual(line_qty7.qty_delivered, 7)
        self.assertEqual(line_qty7.qty_to_invoice, 0)
        self.assertEqual(line_qty7.qty_invoiced, 7)
        line_qty11 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(line_qty11)
        self.assertEqual(line_qty11.product_id, self.product2)
        self.assertEqual(line_qty11.product_uom_qty, 11)
        self.assertEqual(line_qty11.price_unit, 200)
        self.assertEqual(line_qty11.qty_delivered, 11)
        self.assertEqual(line_qty11.qty_to_invoice, 0)
        self.assertEqual(line_qty11.qty_invoiced, 11)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 2)
        move_qty7 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(move_qty7)
        self.assertEqual(move_qty7.product_id, self.product1)
        self.assertEqual(move_qty7.location_id, deposit_loc1)
        self.assertEqual(move_qty7.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty7.sale_line_id, line_qty7)
        self.assertEqual(move_qty7.sale_line_id.qty_delivered, 7)
        move_qty11 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(move_qty11)
        self.assertEqual(move_qty11.product_id, self.product2)
        self.assertEqual(move_qty11.location_id, deposit_loc1)
        self.assertEqual(move_qty11.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty11.sale_line_id, line_qty11)
        self.assertEqual(move_qty11.sale_line_id.qty_delivered, 11)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 2)
        line_inv_qty7 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 7)
        self.assertEqual(line_inv_qty7.product_id, self.product1)
        self.assertEqual(line_inv_qty7.price_unit, 20)
        self.assertEqual(line_inv_qty7.sale_line_ids, line_qty7)
        line_inv_qty11 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 11)
        self.assertEqual(line_inv_qty11.product_id, self.product2)
        self.assertEqual(line_inv_qty11.price_unit, 200)
        self.assertEqual(line_inv_qty11.sale_line_ids, line_qty11)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 55 - 7)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale_return_customer',
                    'product_id': self.product1.id,
                    'qty': 2,
                }),
                (0, 0, {
                    'ttype': 'sale_return_customer',
                    'product_id': self.product2.id,
                    'qty': 12,
                })
            ],

        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 2)
        self.assertEqual(wizard.line_ids[0].qty_finish, 50)
        self.assertEqual(wizard.line_ids[1].qty, 12)
        self.assertEqual(wizard.line_ids[1].qty_finish, 12)
        wizard.action_confirm()
        new_picking_return = self.env['stock.picking'].search(
            [], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return), 1)
        self.assertEqual(new_picking_return.location_id, self.customer_loc)
        self.assertEqual(new_picking_return.location_dest_id, deposit_loc1)
        self.assertEqual(len(new_picking_return.move_lines), 2)
        move_return_product1 = new_picking_return.move_lines.filtered(
            lambda m: m.product_id == self.product1)
        self.assertEqual(move_return_product1.product_id, self.product1)
        self.assertEqual(move_return_product1.product_uom_qty, 2)
        self.assertEqual(move_return_product1.location_id, self.customer_loc)
        self.assertEqual(move_return_product1.location_dest_id, deposit_loc1)
        self.assertEqual(
            move_return_product1.move_line_ids.location_id, self.customer_loc)
        self.assertEqual(
            move_return_product1.move_line_ids.location_dest_id, deposit_loc1)
        self.assertEqual(
            move_return_product1.sale_line_id,
            new_sale.order_line.filtered(
                lambda ln: ln.product_id == self.product1))
        self.assertEqual(
            move_return_product1.sale_line_id.qty_delivered, 7 - 2)
        move_return_product2 = new_picking_return.move_lines.filtered(
            lambda m: m.product_id == self.product2)
        self.assertEqual(move_return_product2.product_id, self.product2)
        self.assertEqual(move_return_product2.product_uom_qty, 12)
        self.assertEqual(move_return_product2.location_id, self.customer_loc)
        self.assertEqual(move_return_product2.location_dest_id, deposit_loc1)
        self.assertEqual(
            move_return_product2.move_line_ids.location_id, self.customer_loc)
        self.assertEqual(
            move_return_product2.move_line_ids.location_dest_id, deposit_loc1)
        self.assertEqual(
            move_return_product2.sale_line_id,
            new_sale.order_line.filtered(
                lambda ln: ln.product_id == self.product2))
        self.assertEqual(
            move_return_product2.sale_line_id.qty_delivered, 11 - 12)
        self.assertEqual(new_picking_return.state, 'done')
        self.assertEqual(len(new_sale.invoice_ids), 2)
        new_invoice_return = new_sale.invoice_ids.filtered(
            lambda inv: inv.type == 'out_refund')
        self.assertEqual(len(new_invoice_return), 1)
        self.assertEqual(len(new_invoice_return.invoice_line_ids), 2)
        invline_return_product1 = new_invoice_return.invoice_line_ids.filtered(
            lambda m: m.product_id == self.product1)
        self.assertEqual(invline_return_product1.product_id, self.product1)
        self.assertEqual(invline_return_product1.quantity, 2)
        self.assertEqual(invline_return_product1.price_unit, 20)
        self.assertEqual(
            invline_return_product1.sale_line_ids,
            new_sale.order_line.filtered(
                lambda ln: ln.product_id == self.product1))
        invline_return_product2 = new_invoice_return.invoice_line_ids.filtered(
            lambda m: m.product_id == self.product2)
        self.assertEqual(invline_return_product2.product_id, self.product2)
        self.assertEqual(invline_return_product2.quantity, 12)
        self.assertEqual(invline_return_product2.price_unit, 200)
        self.assertEqual(
            invline_return_product2.sale_line_ids,
            new_sale.order_line.filtered(
                lambda ln: ln.product_id == self.product2))
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 48 + 2)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7 - 2)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 12)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11 - 12)
        new_sale = new_picking_return.move_lines[0].sale_line_id.order_id
        self.assertEqual(len(new_sale), 1)
        order_line_product1 = (
            new_sale.order_line.filtered(
                lambda ln: ln.product_id == self.product1))
        self.assertEqual(len(order_line_product1), 1)
        self.assertEqual(order_line_product1.product_id, self.product1)
        self.assertEqual(order_line_product1.product_uom_qty, 7)
        self.assertEqual(order_line_product1.price_unit, 20)
        self.assertEqual(order_line_product1.qty_delivered, 7 - 2)
        self.assertEqual(order_line_product1.qty_to_invoice, 0)
        self.assertEqual(order_line_product1.qty_invoiced, 7 - 2)
        order_line_product2 = (
            new_sale.order_line.filtered(
                lambda ln: ln.product_id == self.product2))
        self.assertEqual(len(order_line_product2), 1)
        self.assertEqual(order_line_product2.product_id, self.product2)
        self.assertEqual(order_line_product2.product_uom_qty, 11)
        self.assertEqual(order_line_product2.price_unit, 200)
        self.assertEqual(order_line_product2.qty_delivered, 11 - 12)
        self.assertEqual(order_line_product2.qty_to_invoice, 0)
        self.assertEqual(order_line_product2.qty_invoiced, 11 - 12)

    def test_deposit_return_customer_return_not_sale_lines(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': False,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale_return_customer',
                'product_id': self.product1.id,
                'qty': 8,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 8)
        self.assertEqual(wizard.line_ids.qty_finish, 8)
        with self.assertRaises(UserError):
            wizard.action_confirm()

    def test_deposit_return_stock(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 3)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.move_line_ids.location_dest_id,
            self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale_return_stock',
                'product_id': self.product1.id,
                'qty': 1,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 1)
        self.assertEqual(wizard.line_ids.qty_finish, 3 - 1)
        wizard.action_confirm()
        new_picking_return_stock = self.env['stock.picking'].search(
            [], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return_stock), 1)
        self.assertEqual(new_picking_return_stock.location_id, deposit_loc1)
        self.assertEqual(
            new_picking_return_stock.location_dest_id,
            self.stock_wh.lot_stock_id)
        self.assertEqual(len(new_picking_return_stock.move_lines), 1)
        self.assertEqual(
            new_picking_return_stock.move_lines.product_id, self.product1)
        self.assertEqual(
            new_picking_return_stock.move_lines.product_uom_qty, 1)
        self.assertEqual(
            new_picking_return_stock.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking_return_stock.move_lines.location_dest_id,
            self.stock_wh.lot_stock_id)
        self.assertEqual(
            new_picking_return_stock.move_lines.move_line_ids.location_id,
            deposit_loc1)
        self.assertEqual(
            new_picking_return_stock.move_lines.move_line_ids.location_dest_id,
            self.stock_wh.lot_stock_id)
        self.assertFalse(new_picking_return_stock.move_lines.sale_line_id)
        self.assertEqual(new_picking_return_stock.state, 'done')
        self.assertEqual(len(new_sale.invoice_ids.filtered(
            lambda i: i.type == 'out_refund')), 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0 + 1)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3 - 1)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_return_customer_and_return_stock(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 3)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.move_line_ids.location_dest_id,
            self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale_return_customer',
                'product_id': self.product1.id,
                'qty': 2,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 3 + 2)
        wizard.action_confirm()
        new_picking_return = self.env['stock.picking'].search(
            [], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return), 1)
        self.assertEqual(new_picking_return.location_id, self.customer_loc)
        self.assertEqual(new_picking_return.location_dest_id, deposit_loc1)
        self.assertEqual(len(new_picking_return.move_lines), 1)
        self.assertEqual(new_picking_return.move_lines.product_id, self.product1)
        self.assertEqual(new_picking_return.move_lines.product_uom_qty, 2)
        self.assertEqual(
            new_picking_return.move_lines.location_id, self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.location_dest_id, deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_id,
            self.customer_loc)
        self.assertEqual(
            new_picking_return.move_lines.move_line_ids.location_dest_id,
            deposit_loc1)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(
            new_picking_return.move_lines.sale_line_id.qty_delivered, 7 - 2)
        self.assertEqual(new_picking_return.state, 'done')
        self.assertEqual(len(new_sale.invoice_ids), 2)
        new_invoice_return = new_sale.invoice_ids.filtered(
            lambda inv: inv.type == 'out_refund')
        self.assertEqual(len(new_invoice_return), 1)
        self.assertEqual(len(new_invoice_return.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice_return.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice_return.invoice_line_ids.quantity, 2)
        self.assertEqual(new_invoice_return.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice_return.invoice_line_ids.sale_line_ids,
            new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3 + 2)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7 - 2)
        new_sale = new_picking_return.move_lines.sale_line_id.order_id
        self.assertEqual(len(new_sale), 1)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 5)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 5)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale_return_stock',
                'product_id': self.product1.id,
                'qty': 1,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 1)
        self.assertEqual(wizard.line_ids.qty_finish, 5 - 1)
        wizard.action_confirm()
        new_picking_return_stock = self.env['stock.picking'].search(
            [], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return_stock), 1)
        self.assertEqual(new_picking_return_stock.state, 'done')
        self.assertFalse(
            new_sale.invoice_ids.filtered(
                lambda i: i.type == 'out_refund'
            ).invoice_line_ids.quantity == 1)
        self.assertEqual(new_picking_return_stock.location_id, deposit_loc1)
        self.assertEqual(
            new_picking_return_stock.location_dest_id,
            self.stock_wh.lot_stock_id)
        self.assertEqual(len(new_picking_return_stock.move_lines), 1)
        self.assertEqual(
            new_picking_return_stock.move_lines.product_id, self.product1)
        self.assertEqual(
            new_picking_return_stock.move_lines.product_uom_qty, 1)
        self.assertEqual(
            new_picking_return_stock.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking_return_stock.move_lines.location_dest_id,
            self.stock_wh.lot_stock_id)
        self.assertEqual(
            new_picking_return_stock.move_lines.move_line_ids.location_id,
            deposit_loc1)
        self.assertEqual(
            new_picking_return_stock.move_lines.move_line_ids.location_dest_id,
            self.stock_wh.lot_stock_id)
        self.assertFalse(new_picking_return_stock.move_lines.sale_line_id)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0 + 1)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5 - 1)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 5)

    def test_deposit_return_stock_more_qty(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': False,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 12,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 12)
        self.assertEqual(wizard.line_ids.qty_finish, -2)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'to invoice')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 12)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 12)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 12)
        self.assertEqual(new_sale.order_line.qty_invoiced, 0)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 12)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 12)
        self.assertEqual(new_picking.state, 'done')
        self.assertFalse(new_sale.invoice_ids)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale_return_stock',
                'product_id': self.product1.id,
                'qty': 2,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 0 - 2)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 0)
        wizard.action_confirm()
        new_picking_return_stock = self.env['stock.picking'].search(
            [], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return_stock), 1)
        self.assertEqual(new_picking_return_stock.location_id, deposit_loc1)
        self.assertEqual(
            new_picking_return_stock.location_dest_id,
            self.stock_wh.lot_stock_id)
        self.assertEqual(len(new_picking_return_stock.move_lines), 1)
        self.assertEqual(
            new_picking_return_stock.move_lines.product_id, self.product1)
        self.assertEqual(
            new_picking_return_stock.move_lines.product_uom_qty, 2)
        self.assertEqual(
            new_picking_return_stock.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking_return_stock.move_lines.location_dest_id,
            self.stock_wh.lot_stock_id)
        self.assertEqual(
            new_picking_return_stock.move_lines.move_line_ids.location_id,
            deposit_loc1)
        self.assertEqual(
            new_picking_return_stock.move_lines.move_line_ids.location_dest_id,
            self.stock_wh.lot_stock_id)
        self.assertFalse(new_picking_return_stock.move_lines.sale_line_id)
        self.assertEqual(new_picking_return_stock.state, 'done')
        self.assertEqual(len(new_sale.invoice_ids.filtered(
            lambda i: i.type == 'out_refund')), 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0 + 2)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0 - 2)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 12)

    def test_deposit_return_stock_2wizlines(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        sale3 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product2, 10, price_forced=200)
        self.assertEqual(sale3.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale3.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale3.action_confirm()
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(len(sale3.picking_ids), 1)
        picking_int = sale3.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 10
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product1.id,
                    'qty': 7,
                }),
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product2.id,
                    'qty': 11,
                })
            ],
        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 7)
        self.assertEqual(wizard.line_ids[0].qty_finish, 3)
        self.assertEqual(wizard.line_ids[1].qty, 11)
        self.assertEqual(wizard.line_ids[1].qty_finish, -1)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids[1].force_inventory = True
        wizard.line_ids[1].onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids[0].qty_theorical, 10)
        self.assertEqual(wizard.line_ids[1].qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale3.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(sale3.order_line.qty_to_invoice, 0)
        self.assertEqual(sale3.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 2)
        line_qty7 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(line_qty7)
        self.assertEqual(line_qty7.product_id, self.product1)
        self.assertEqual(line_qty7.product_uom_qty, 7)
        self.assertEqual(line_qty7.price_unit, 20)
        self.assertEqual(line_qty7.qty_delivered, 7)
        self.assertEqual(line_qty7.qty_to_invoice, 0)
        self.assertEqual(line_qty7.qty_invoiced, 7)
        line_qty11 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(line_qty11)
        self.assertEqual(line_qty11.product_id, self.product2)
        self.assertEqual(line_qty11.product_uom_qty, 11)
        self.assertEqual(line_qty11.price_unit, 200)
        self.assertEqual(line_qty11.qty_delivered, 11)
        self.assertEqual(line_qty11.qty_to_invoice, 0)
        self.assertEqual(line_qty11.qty_invoiced, 11)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 2)
        move_qty7 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 7)
        self.assertTrue(move_qty7)
        self.assertEqual(move_qty7.product_id, self.product1)
        self.assertEqual(move_qty7.location_id, deposit_loc1)
        self.assertEqual(move_qty7.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty7.sale_line_id, line_qty7)
        self.assertEqual(move_qty7.sale_line_id.qty_delivered, 7)
        move_qty11 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 11)
        self.assertTrue(move_qty11)
        self.assertEqual(move_qty11.product_id, self.product2)
        self.assertEqual(move_qty11.location_id, deposit_loc1)
        self.assertEqual(move_qty11.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty11.sale_line_id, line_qty11)
        self.assertEqual(move_qty11.sale_line_id.qty_delivered, 11)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 2)
        line_inv_qty7 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 7)
        self.assertEqual(line_inv_qty7.product_id, self.product1)
        self.assertEqual(line_inv_qty7.price_unit, 20)
        self.assertEqual(line_inv_qty7.sale_line_ids, line_qty7)
        line_inv_qty11 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 11)
        self.assertEqual(line_inv_qty11.product_id, self.product2)
        self.assertEqual(line_inv_qty11.price_unit, 200)
        self.assertEqual(line_inv_qty11.sale_line_ids, line_qty11)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale_return_stock',
                    'product_id': self.product1.id,
                    'qty': 2,
                }),
            ],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 3 - 2)
        wizard.action_confirm()
        new_picking_return_stock = self.env['stock.picking'].search(
            [], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return_stock), 1)
        self.assertEqual(new_picking_return_stock.location_id, deposit_loc1)
        self.assertEqual(
            new_picking_return_stock.location_dest_id,
            self.stock_wh.lot_stock_id)
        self.assertEqual(len(new_picking_return_stock.move_lines), 1)
        self.assertEqual(
            new_picking_return_stock.move_lines.product_id, self.product1)
        self.assertEqual(
            new_picking_return_stock.move_lines.product_uom_qty, 2)
        self.assertEqual(
            new_picking_return_stock.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking_return_stock.move_lines.location_dest_id,
            self.stock_wh.lot_stock_id)
        self.assertEqual(
            new_picking_return_stock.move_lines.move_line_ids.location_id,
            deposit_loc1)
        self.assertEqual(
            new_picking_return_stock.move_lines.move_line_ids.location_dest_id,
            self.stock_wh.lot_stock_id)
        self.assertFalse(new_picking_return_stock.move_lines.sale_line_id)
        self.assertEqual(new_picking_return_stock.state, 'done')
        self.assertEqual(len(new_sale.invoice_ids.filtered(
            lambda i: i.type == 'out_refund')), 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0 + 2)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3 - 2)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 11)

    def test_deposit_return_customer_stock_no_create_invoice(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': False,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 10 - 7)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'to invoice')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 7)
        self.assertEqual(new_sale.order_line.qty_invoiced, 0)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.move_line_ids.location_dest_id,
            self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': False,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale_return_customer_stock',
                'product_id': self.product1.id,
                'qty': 2,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 3 + 2 - 2)
        wizard.action_confirm()
        new_picking_return_customer = self.env['stock.picking'].search([
            ('location_id', '=', self.customer_loc.id),
            ('location_dest_id', '=', deposit_loc1.id),
        ], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return_customer), 1)
        self.assertEqual(len(new_picking_return_customer.move_lines), 1)
        move_line = new_picking_return_customer.move_lines
        self.assertEqual(move_line.product_id, self.product1)
        self.assertEqual(move_line.product_uom_qty, 2)
        self.assertEqual(move_line.location_id, self.customer_loc)
        self.assertEqual(move_line.location_dest_id, deposit_loc1)
        self.assertEqual(
            move_line.move_line_ids.location_id, self.customer_loc)
        self.assertEqual(
            move_line.move_line_ids.location_dest_id, deposit_loc1)
        self.assertEqual(move_line.sale_line_id, new_sale.order_line)
        self.assertEqual(move_line.sale_line_id.qty_delivered, 7 - 2)
        self.assertEqual(new_picking_return_customer.state, 'done')
        self.assertEqual(len(new_sale.invoice_ids), 0)
        new_sale = new_picking_return_customer.move_lines.sale_line_id.order_id
        self.assertEqual(len(new_sale), 1)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 5)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 5)
        self.assertEqual(new_sale.order_line.qty_invoiced, 0)
        new_picking_return_stock = self.env['stock.picking'].search([
            ('location_id', '=', deposit_loc1.id),
            ('location_dest_id', '=', self.stock_wh.lot_stock_id.id),
        ], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return_stock), 1)
        self.assertEqual(len(new_picking_return_stock.move_lines), 1)
        move_line = new_picking_return_stock.move_lines
        self.assertEqual(move_line.product_id, self.product1)
        self.assertEqual(move_line.product_uom_qty, 2)
        self.assertEqual(move_line.location_id, deposit_loc1)
        self.assertEqual(
            move_line.location_dest_id, self.stock_wh.lot_stock_id)
        self.assertEqual(
            move_line.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            move_line.move_line_ids.location_dest_id,
            self.stock_wh.lot_stock_id)
        self.assertFalse(move_line.sale_line_id)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0 + 2)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3 + 2 - 2)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7 - 2)

    def test_deposit_return_customer_stock_more_qty_create_invoice(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 7,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 7)
        self.assertEqual(wizard.line_ids.qty_finish, 10 - 7)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 10)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.move_line_ids.location_dest_id,
            self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale_return_customer_stock',
                'product_id': self.product1.id,
                'qty': 8,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 8)
        self.assertEqual(wizard.line_ids.qty_finish, 3 + 8 - 8)
        wizard.action_confirm()
        new_picking_return_customer = self.env['stock.picking'].search([
            ('location_id', '=', self.customer_loc.id),
            ('location_dest_id', '=', deposit_loc1.id),
        ], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return_customer), 1)
        self.assertEqual(len(new_picking_return_customer.move_lines), 1)
        move_line = new_picking_return_customer.move_lines
        self.assertEqual(move_line.product_id, self.product1)
        self.assertEqual(move_line.product_uom_qty, 8)
        self.assertEqual(move_line.location_id, self.customer_loc)
        self.assertEqual(move_line.location_dest_id, deposit_loc1)
        self.assertEqual(
            move_line.move_line_ids.location_id, self.customer_loc)
        self.assertEqual(
            move_line.move_line_ids.location_dest_id, deposit_loc1)
        self.assertEqual(move_line.sale_line_id, new_sale.order_line)
        self.assertEqual(move_line.sale_line_id.qty_delivered, 7 - 8)
        self.assertEqual(new_picking_return_customer.state, 'done')
        self.assertEqual(len(new_sale.invoice_ids), 2)
        invoice_refund = new_sale.invoice_ids.filtered(
            lambda i: i.type == 'out_refund')
        self.assertEqual(len(invoice_refund), 1)
        self.assertEqual(len(invoice_refund.invoice_line_ids), 1)
        self.assertEqual(
            invoice_refund.invoice_line_ids.product_id, self.product1)
        self.assertEqual(invoice_refund.invoice_line_ids.quantity, 8)
        self.assertEqual(invoice_refund.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            invoice_refund.invoice_line_ids.sale_line_ids, new_sale.order_line)
        new_sale = new_picking_return_customer.move_lines.sale_line_id.order_id
        self.assertEqual(len(new_sale), 1)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale.order_line.price_unit, 20)
        self.assertEqual(new_sale.order_line.qty_delivered, 7 - 8)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, -1)
        new_picking_return_stock = self.env['stock.picking'].search([
            ('location_id', '=', deposit_loc1.id),
            ('location_dest_id', '=', self.stock_wh.lot_stock_id.id),
        ], order='id desc', limit=1)
        self.assertEqual(len(new_picking_return_stock), 1)
        self.assertEqual(len(new_picking_return_stock.move_lines), 1)
        move_line = new_picking_return_stock.move_lines
        self.assertEqual(move_line.product_id, self.product1)
        self.assertEqual(move_line.product_uom_qty, 8)
        self.assertEqual(move_line.location_id, deposit_loc1)
        self.assertEqual(
            move_line.location_dest_id, self.stock_wh.lot_stock_id)
        self.assertEqual(
            move_line.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            move_line.move_line_ids.location_dest_id,
            self.stock_wh.lot_stock_id)
        self.assertFalse(move_line.sale_line_id)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0 + 8)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 3 + 8 - 8)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7 - 8)

    def test_deposit_inventory(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(
            self.product1, self.stock_wh.lot_stock_id, 1000)
        self.update_qty_on_hand(
            self.product2, self.stock_wh.lot_stock_id, 1000)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 1000)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 1000)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.env['sale.order'].create({
            'partner_id': partner_deposit1.id,
            'partner_invoice_id': partner_deposit1.id,
            'partner_shipping_id': partner_deposit1_ship.id,
            'warehouse_id': self.stock_wh.id,
            'pricelist_id': self.env.ref('product.list0').id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product1.id,
                    'product_uom_qty': 400,
                    'price_unit': 100,
                }),
                (0, 0, {
                    'product_id': self.product2.id,
                    'product_uom_qty': 30,
                    'price_unit': 200,
                }),
            ]
        })
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(
            list(set(sale1.order_line.mapped('qty_delivered'))), [0.0])
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            list(set(sale1.order_line.mapped('qty_delivered'))), [0.0])
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        for move in picking_int.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(
            list(set(sale1.order_line.mapped('qty_delivered'))), [0.0])
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 1000 - 400)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 400)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 1000 - 30)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 30)
        self.assertEqual(self.product1.with_context(
            location=self.inventory_loc.id).qty_available, -1000)
        self.assertEqual(self.product2.with_context(
            location=self.inventory_loc.id).qty_available, -1000)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': False,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [
                (0, 0, {
                    'ttype': 'inventory',
                    'product_id': self.product1.id,
                    'qty': 410,
                }),
                (0, 0, {
                    'ttype': 'inventory',
                    'product_id': self.product2.id,
                    'qty': 28,
                }),
            ],
        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        line_product1 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product1)
        self.assertTrue(line_product1)
        line_product2 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product2)
        self.assertTrue(line_product2)
        self.assertEqual(line_product1.qty, 410)
        self.assertEqual(line_product1.qty_finish, 400 - 410)
        self.assertEqual(line_product2.qty, 28)
        self.assertEqual(line_product2.qty_finish, 30 - 28)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        line_product1.force_inventory = True
        line_product1.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(line_product1.qty_theorical, 400)
        self.assertEqual(line_product2.qty_theorical, 30)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale1.order_line.mapped('qty_delivered'), [0.0, 0.0])
        self.assertEqual(sale1.order_line.mapped('qty_to_invoice'), [0.0, 0.0])
        self.assertEqual(sale1.order_line.mapped('qty_invoiced'), [0.0, 0.0])
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'to invoice')
        self.assertFalse(new_sale.is_sale_deposit)
        self.assertTrue(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Inventory\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 2)
        order_line_product1 = new_sale.order_line.filtered(
            lambda ln: ln.product_id == self.product1)
        self.assertTrue(order_line_product1)
        self.assertEqual(order_line_product1.product_uom_qty, 10)
        self.assertEqual(order_line_product1.price_unit, 100)
        self.assertEqual(order_line_product1.qty_delivered, 10)
        self.assertEqual(order_line_product1.qty_to_invoice, 10)
        self.assertEqual(order_line_product1.qty_invoiced, 0)
        order_line_product2 = new_sale.order_line.filtered(
            lambda ln: ln.product_id == self.product2)
        self.assertTrue(order_line_product2)
        self.assertEqual(order_line_product2.product_uom_qty, 2)
        self.assertEqual(order_line_product2.price_unit, 200)
        self.assertEqual(order_line_product2.qty_delivered, 2)
        self.assertEqual(order_line_product2.qty_to_invoice, 2)
        self.assertEqual(order_line_product2.qty_invoiced, 0)
        new_pickings = new_sale.picking_ids
        self.assertEqual(len(new_pickings), 2)
        self.assertEqual(
            list(set(new_pickings.mapped('picking_type_id'))),
            [self.stock_wh.int_type_id])
        new_picking1 = new_pickings.filtered(
            lambda p: p.location_id == deposit_loc1
            and p.location_dest_id == self.customer_loc)
        self.assertTrue(new_picking1)
        self.assertEqual(len(new_picking1.move_lines), 2)
        move_product1 = new_picking1.move_lines.filtered(
            lambda m: m.product_id == self.product1)
        self.assertTrue(move_product1)
        self.assertEqual(move_product1.product_uom_qty, 10)
        self.assertEqual(move_product1.location_id, deposit_loc1)
        self.assertEqual(move_product1.location_dest_id, self.customer_loc)
        self.assertEqual(move_product1.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            move_product1.move_line_ids.location_dest_id, self.customer_loc)
        self.assertEqual(move_product1.sale_line_id, order_line_product1)
        self.assertEqual(move_product1.sale_line_id.qty_delivered, 10)
        move_product2 = new_picking1.move_lines.filtered(
            lambda m: m.product_id == self.product2)
        self.assertTrue(move_product2)
        self.assertEqual(move_product2.product_uom_qty, 2)
        self.assertEqual(move_product2.location_id, deposit_loc1)
        self.assertEqual(move_product2.location_dest_id, self.customer_loc)
        self.assertEqual(move_product2.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            move_product2.move_line_ids.location_dest_id, self.customer_loc)
        self.assertEqual(move_product2.sale_line_id, order_line_product2)
        self.assertEqual(move_product2.sale_line_id.qty_delivered, 2)
        new_picking2 = new_pickings.filtered(
            lambda p: p.location_id == self.customer_loc
            and p.location_dest_id == self.inventory_loc)
        self.assertTrue(new_picking2)
        self.assertEqual(len(new_picking2.move_lines), 2)
        move_product1 = new_picking2.move_lines.filtered(
            lambda m: m.product_id == self.product1)
        self.assertTrue(move_product1)
        self.assertEqual(move_product1.product_uom_qty, 10)
        self.assertEqual(move_product1.location_id, self.customer_loc)
        self.assertEqual(move_product1.location_dest_id, self.inventory_loc)
        self.assertEqual(
            move_product1.move_line_ids.location_id, self.customer_loc)
        self.assertEqual(
            move_product1.move_line_ids.location_dest_id, self.inventory_loc)
        self.assertEqual(move_product1.sale_line_id, order_line_product1)
        self.assertEqual(move_product1.sale_line_id.qty_delivered, 10)
        move_product2 = new_picking2.move_lines.filtered(
            lambda m: m.product_id == self.product2)
        self.assertTrue(move_product2)
        self.assertEqual(move_product2.product_uom_qty, 2)
        self.assertEqual(move_product2.location_id, self.customer_loc)
        self.assertEqual(move_product2.location_dest_id, self.inventory_loc)
        self.assertEqual(
            move_product2.move_line_ids.location_id, self.customer_loc)
        self.assertEqual(
            move_product2.move_line_ids.location_dest_id, self.inventory_loc)
        self.assertEqual(move_product2.sale_line_id, order_line_product2)
        self.assertEqual(move_product2.sale_line_id.qty_delivered, 2)
        self.assertEqual(list(set(new_pickings.mapped('state'))), ['done'])
        self.assertFalse(new_sale.invoice_ids)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 1000 - 400)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 1000 - 30)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 400 - 10)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 30 - 2)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.inventory_loc.id).qty_available, -1000 + 10)
        self.assertEqual(self.product2.with_context(
            location=self.inventory_loc.id).qty_available, -1000 + 2)

    def test_deposit_inventory_create_invoice(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(
            self.product1, self.stock_wh.lot_stock_id, 1000)
        self.update_qty_on_hand(
            self.product2, self.stock_wh.lot_stock_id, 1000)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 1000)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 1000)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.env['sale.order'].create({
            'partner_id': partner_deposit1.id,
            'partner_invoice_id': partner_deposit1.id,
            'partner_shipping_id': partner_deposit1_ship.id,
            'warehouse_id': self.stock_wh.id,
            'pricelist_id': self.env.ref('product.list0').id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product1.id,
                    'price_unit': 100,
                    'product_uom_qty': 400,
                }),
                (0, 0, {
                    'product_id': self.product2.id,
                    'price_unit': 200,
                    'product_uom_qty': 30,
                }),
            ]
        })
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(
            list(set(sale1.order_line.mapped('qty_delivered'))), [0.0])
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            list(set(sale1.order_line.mapped('qty_delivered'))), [0.0])
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        for move in picking_int.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(
            list(set(sale1.order_line.mapped('qty_delivered'))), [0.0])
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 1000 - 400)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 400)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 1000 - 30)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 30)
        self.assertEqual(self.product1.with_context(
            location=self.inventory_loc.id).qty_available, -1000)
        self.assertEqual(self.product2.with_context(
            location=self.inventory_loc.id).qty_available, -1000)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [
                (0, 0, {
                    'ttype': 'inventory',
                    'product_id': self.product1.id,
                    'qty': 410,
                }),
                (0, 0, {
                    'ttype': 'inventory',
                    'product_id': self.product2.id,
                    'qty': 28,
                }),
            ],
        })
        for wiz_line in wizard.line_ids:
            wiz_line.onchange_qty()
        line_product1 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product1)
        self.assertTrue(line_product1)
        line_product2 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product2)
        self.assertTrue(line_product2)
        self.assertEqual(line_product1.qty, 410)
        self.assertEqual(line_product1.qty_finish, 400 - 410)
        self.assertEqual(line_product2.qty, 28)
        self.assertEqual(line_product2.qty_finish, 30 - 28)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        line_product1.force_inventory = True
        line_product1.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(line_product1.qty_theorical, 400)
        self.assertEqual(line_product2.qty_theorical, 30)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale1.order_line.mapped('qty_delivered'), [0.0, 0.0])
        self.assertEqual(sale1.order_line.mapped('qty_to_invoice'), [0.0, 0.0])
        self.assertEqual(sale1.order_line.mapped('qty_invoiced'), [0.0, 0.0])
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertFalse(new_sale.is_sale_deposit)
        self.assertTrue(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Inventory\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 2)
        order_line_product1 = new_sale.order_line.filtered(
            lambda ln: ln.product_id == self.product1)
        self.assertTrue(order_line_product1)
        self.assertEqual(order_line_product1.product_uom_qty, 10)
        self.assertEqual(order_line_product1.price_unit, 100)
        self.assertEqual(order_line_product1.qty_delivered, 10)
        self.assertEqual(order_line_product1.qty_to_invoice, 0)
        self.assertEqual(order_line_product1.qty_invoiced, 10)
        order_line_product2 = new_sale.order_line.filtered(
            lambda ln: ln.product_id == self.product2)
        self.assertTrue(order_line_product2)
        self.assertEqual(order_line_product2.product_uom_qty, 2)
        self.assertEqual(order_line_product2.price_unit, 200)
        self.assertEqual(order_line_product2.qty_delivered, 2)
        self.assertEqual(order_line_product2.qty_to_invoice, 0)
        self.assertEqual(order_line_product2.qty_invoiced, 2)
        new_pickings = new_sale.picking_ids
        self.assertEqual(len(new_pickings), 2)
        self.assertEqual(
            list(set(new_pickings.mapped('picking_type_id'))),
            [self.stock_wh.int_type_id])
        new_picking1 = new_pickings.filtered(
            lambda p: p.location_id == deposit_loc1
            and p.location_dest_id == self.customer_loc)
        self.assertTrue(new_picking1)
        self.assertEqual(len(new_picking1.move_lines), 2)
        move_product1 = new_picking1.move_lines.filtered(
            lambda m: m.product_id == self.product1)
        self.assertTrue(move_product1)
        self.assertEqual(move_product1.product_uom_qty, 10)
        self.assertEqual(move_product1.location_id, deposit_loc1)
        self.assertEqual(move_product1.location_dest_id, self.customer_loc)
        self.assertEqual(move_product1.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            move_product1.move_line_ids.location_dest_id, self.customer_loc)
        self.assertEqual(move_product1.sale_line_id, order_line_product1)
        self.assertEqual(move_product1.sale_line_id.qty_delivered, 10)
        move_product2 = new_picking1.move_lines.filtered(
            lambda m: m.product_id == self.product2)
        self.assertTrue(move_product2)
        self.assertEqual(move_product2.product_uom_qty, 2)
        self.assertEqual(move_product2.location_id, deposit_loc1)
        self.assertEqual(move_product2.location_dest_id, self.customer_loc)
        self.assertEqual(move_product2.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            move_product2.move_line_ids.location_dest_id, self.customer_loc)
        self.assertEqual(move_product2.sale_line_id, order_line_product2)
        self.assertEqual(move_product2.sale_line_id.qty_delivered, 2)
        new_picking2 = new_pickings.filtered(
            lambda p: p.location_id == self.customer_loc
            and p.location_dest_id == self.inventory_loc)
        self.assertTrue(new_picking2)
        self.assertEqual(len(new_picking2.move_lines), 2)
        move_product1 = new_picking2.move_lines.filtered(
            lambda m: m.product_id == self.product1)
        self.assertTrue(move_product1)
        self.assertEqual(move_product1.product_uom_qty, 10)
        self.assertEqual(move_product1.location_id, self.customer_loc)
        self.assertEqual(move_product1.location_dest_id, self.inventory_loc)
        self.assertEqual(
            move_product1.move_line_ids.location_id, self.customer_loc)
        self.assertEqual(
            move_product1.move_line_ids.location_dest_id, self.inventory_loc)
        self.assertEqual(move_product1.sale_line_id, order_line_product1)
        self.assertEqual(move_product1.sale_line_id.qty_delivered, 10)
        move_product2 = new_picking2.move_lines.filtered(
            lambda m: m.product_id == self.product2)
        self.assertTrue(move_product2)
        self.assertEqual(move_product2.product_uom_qty, 2)
        self.assertEqual(move_product2.location_id, self.customer_loc)
        self.assertEqual(move_product2.location_dest_id, self.inventory_loc)
        self.assertEqual(
            move_product2.move_line_ids.location_id, self.customer_loc)
        self.assertEqual(
            move_product2.move_line_ids.location_dest_id, self.inventory_loc)
        self.assertEqual(move_product2.sale_line_id, order_line_product2)
        self.assertEqual(move_product2.sale_line_id.qty_delivered, 2)
        self.assertEqual(list(set(new_pickings.mapped('state'))), ['done'])
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 2)
        invoice_line_product1 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product1)
        self.assertTrue(invoice_line_product1)
        self.assertEqual(invoice_line_product1.quantity, 10)
        self.assertEqual(invoice_line_product1.price_unit, 100)
        self.assertEqual(
            invoice_line_product1.sale_line_ids, order_line_product1)
        invoice_line_product2 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.product_id == self.product2)
        self.assertTrue(invoice_line_product2)
        self.assertEqual(invoice_line_product2.quantity, 2)
        self.assertEqual(invoice_line_product2.price_unit, 200)
        self.assertEqual(
            invoice_line_product2.sale_line_ids, order_line_product2)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 1000 - 400)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 1000 - 30)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 400 - 10)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 30 - 2)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.inventory_loc.id).qty_available, -1000 + 10)
        self.assertEqual(self.product2.with_context(
            location=self.inventory_loc.id).qty_available, -1000 + 2)

    def test_deposit_inventory_real_fifo_more_qty(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(
            self.product1, self.stock_wh.lot_stock_id, 1000)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 1000)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.env['sale.order'].create({
            'partner_id': partner_deposit1.id,
            'partner_invoice_id': partner_deposit1.id,
            'partner_shipping_id': partner_deposit1_ship.id,
            'warehouse_id': self.stock_wh.id,
            'pricelist_id': self.env.ref('product.list0').id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product1.id,
                    'product_uom_qty': 1,
                    'price_unit': 10,
                }),
            ]
        })
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(
            list(set(sale1.order_line.mapped('qty_delivered'))), [0.0])
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            list(set(sale1.order_line.mapped('qty_delivered'))), [0.0])
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        for move in picking_int.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(
            list(set(sale1.order_line.mapped('qty_delivered'))), [0.0])
        sale2 = self.env['sale.order'].create({
            'partner_id': partner_deposit1.id,
            'partner_invoice_id': partner_deposit1.id,
            'partner_shipping_id': partner_deposit1_ship.id,
            'warehouse_id': self.stock_wh.id,
            'pricelist_id': self.env.ref('product.list0').id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product1.id,
                    'product_uom_qty': 10,
                    'price_unit': 20,
                }),
            ]
        })
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(
            list(set(sale2.order_line.mapped('qty_delivered'))), [0.0])
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            list(set(sale2.order_line.mapped('qty_delivered'))), [0.0])
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        for move in picking_int.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(
            list(set(sale2.order_line.mapped('qty_delivered'))), [0.0])
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id
        ).qty_available, 1000 - 1 - 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 1 + 10)
        self.assertEqual(self.product1.with_context(
            location=self.inventory_loc.id).qty_available, -1000)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': False,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 20,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 20)
        self.assertEqual(wizard.line_ids.qty_finish, -9)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 11)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'to invoice')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 3)
        line_qty1 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertEqual(line_qty1.product_id, self.product1)
        self.assertEqual(line_qty1.product_uom_qty, 1)
        self.assertEqual(line_qty1.price_unit, 10)
        self.assertEqual(line_qty1.qty_delivered, 1)
        self.assertEqual(line_qty1.qty_to_invoice, 1)
        self.assertEqual(line_qty1.qty_invoiced, 0)
        line_qty10 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 10)
        self.assertEqual(line_qty10.product_id, self.product1)
        self.assertEqual(line_qty10.product_uom_qty, 10)
        self.assertEqual(line_qty10.price_unit, 20)
        self.assertEqual(line_qty10.qty_delivered, 10)
        self.assertEqual(line_qty10.qty_to_invoice, 10)
        self.assertEqual(line_qty10.qty_invoiced, 0)
        line_qty9 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 9)
        self.assertEqual(line_qty9.product_id, self.product1)
        self.assertEqual(line_qty9.product_uom_qty, 9)
        self.assertEqual(line_qty9.price_unit, 100)
        self.assertEqual(line_qty9.qty_delivered, 9)
        self.assertEqual(line_qty9.qty_to_invoice, 9)
        self.assertEqual(line_qty9.qty_invoiced, 0)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 3)
        move_qty1 = new_picking.move_lines.filtered(
            lambda m: m.product_uom_qty == 1)
        self.assertTrue(move_qty1)
        self.assertEqual(move_qty1.product_id, self.product1)
        self.assertEqual(move_qty1.location_id, deposit_loc1)
        self.assertEqual(move_qty1.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty1.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            move_qty1.move_line_ids.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty1.sale_line_id, line_qty1)
        self.assertEqual(move_qty1.sale_line_id.qty_delivered, 1)
        move_qty10 = new_picking.move_lines.filtered(
            lambda m: m.product_uom_qty == 10)
        self.assertTrue(move_qty10)
        self.assertEqual(move_qty10.product_id, self.product1)
        self.assertEqual(move_qty10.location_id, deposit_loc1)
        self.assertEqual(move_qty10.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty10.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            move_qty10.move_line_ids.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty10.sale_line_id, line_qty10)
        self.assertEqual(move_qty10.sale_line_id.qty_delivered, 10)
        move_qty9 = new_picking.move_lines.filtered(
            lambda m: m.product_uom_qty == 9)
        self.assertTrue(move_qty9)
        self.assertEqual(move_qty9.product_id, self.product1)
        self.assertEqual(move_qty9.location_id, deposit_loc1)
        self.assertEqual(move_qty9.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty9.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            move_qty9.move_line_ids.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty9.sale_line_id, line_qty9)
        self.assertEqual(move_qty9.sale_line_id.qty_delivered, 9)
        self.assertEqual(new_picking.state, 'done')
        self.assertFalse(new_sale.invoice_ids)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available,
            1000 - 1 - 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 20)
        self.assertEqual(self.product1.with_context(
            location=self.inventory_loc.id).qty_available, -1000 - 9)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': False,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [
                (0, 0, {
                    'ttype': 'inventory',
                    'product_id': self.product1.id,
                    'qty': 15,
                }),
            ],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 15)
        self.assertEqual(wizard.line_ids.qty_finish, 0 - 15)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids.force_inventory = True
        wizard.line_ids.onchange_qty()
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 0)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'to invoice')
        self.assertFalse(new_sale.is_sale_deposit)
        self.assertTrue(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Inventory\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 3)
        line_qty1 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertEqual(line_qty1.product_id, self.product1)
        self.assertEqual(line_qty1.price_unit, 10)
        self.assertEqual(line_qty1.qty_delivered, 1)
        self.assertEqual(line_qty1.qty_to_invoice, 1)
        self.assertEqual(line_qty1.qty_invoiced, 0)
        line_qty10 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 10)
        self.assertEqual(line_qty10.product_id, self.product1)
        self.assertEqual(line_qty10.price_unit, 20)
        self.assertEqual(line_qty10.qty_delivered, 10)
        self.assertEqual(line_qty10.qty_to_invoice, 10)
        self.assertEqual(line_qty10.qty_invoiced, 0)
        line_qty4 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 4)
        self.assertEqual(line_qty4.product_id, self.product1)
        self.assertEqual(line_qty4.price_unit, 100)
        self.assertEqual(line_qty4.qty_delivered, 4)
        self.assertEqual(line_qty4.qty_to_invoice, 4)
        self.assertEqual(line_qty4.qty_invoiced, 0)
        new_pickings = new_sale.picking_ids
        self.assertEqual(len(new_pickings), 2)
        self.assertEqual(
            list(set(new_pickings.mapped('picking_type_id'))),
            [self.stock_wh.int_type_id])
        new_picking1 = new_pickings.filtered(
            lambda p: p.location_id == deposit_loc1
            and p.location_dest_id == self.customer_loc)
        self.assertTrue(new_picking1)
        self.assertEqual(len(new_picking1.move_lines), 3)
        move_qty10 = new_picking1.move_lines.filtered(
            lambda m: m.product_uom_qty == 10)
        self.assertTrue(move_qty10)
        self.assertEqual(move_qty10.product_uom_qty, 10)
        self.assertEqual(move_qty10.location_id, deposit_loc1)
        self.assertEqual(move_qty10.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty10.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            move_qty10.move_line_ids.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty10.sale_line_id, line_qty10)
        self.assertEqual(move_qty10.sale_line_id.qty_delivered, 10)
        move_qty1 = new_picking1.move_lines.filtered(
            lambda m: m.product_uom_qty == 1)
        self.assertTrue(move_qty1)
        self.assertEqual(move_qty1.product_uom_qty, 1)
        self.assertEqual(move_qty1.location_id, deposit_loc1)
        self.assertEqual(move_qty1.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty1.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            move_qty1.move_line_ids.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty1.sale_line_id, line_qty1)
        self.assertEqual(move_qty1.sale_line_id.qty_delivered, 1)
        move_qty4 = new_picking1.move_lines.filtered(
            lambda m: m.product_uom_qty == 4)
        self.assertTrue(move_qty4)
        self.assertEqual(move_qty4.product_uom_qty, 4)
        self.assertEqual(move_qty4.location_id, deposit_loc1)
        self.assertEqual(move_qty4.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty4.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            move_qty4.move_line_ids.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty4.sale_line_id, line_qty4)
        self.assertEqual(move_qty4.sale_line_id.qty_delivered, 4)
        new_picking2 = new_pickings.filtered(
            lambda p: p.location_id == self.customer_loc
            and p.location_dest_id == self.inventory_loc)
        self.assertTrue(new_picking2)
        self.assertEqual(len(new_picking2.move_lines), 3)
        move_qty10 = new_picking2.move_lines.filtered(
            lambda m: m.product_uom_qty == 10)
        self.assertTrue(move_qty10)
        self.assertEqual(move_qty10.product_uom_qty, 10)
        self.assertEqual(move_qty10.location_id, self.customer_loc)
        self.assertEqual(move_qty10.location_dest_id, self.inventory_loc)
        self.assertEqual(
            move_qty10.move_line_ids.location_id, self.customer_loc)
        self.assertEqual(
            move_qty10.move_line_ids.location_dest_id, self.inventory_loc)
        self.assertEqual(move_qty10.sale_line_id, line_qty10)
        self.assertEqual(move_qty10.sale_line_id.qty_delivered, 10)
        move_qty1 = new_picking2.move_lines.filtered(
            lambda m: m.product_uom_qty == 1)
        self.assertTrue(move_qty1)
        self.assertEqual(move_qty1.product_uom_qty, 1)
        self.assertEqual(move_qty1.location_id, self.customer_loc)
        self.assertEqual(move_qty1.location_dest_id, self.inventory_loc)
        self.assertEqual(
            move_qty1.move_line_ids.location_id, self.customer_loc)
        self.assertEqual(
            move_qty1.move_line_ids.location_dest_id, self.inventory_loc)
        self.assertEqual(move_qty1.sale_line_id, line_qty1)
        self.assertEqual(move_qty1.sale_line_id.qty_delivered, 1)
        move_qty4 = new_picking2.move_lines.filtered(
            lambda m: m.product_uom_qty == 4)
        self.assertTrue(move_qty4)
        self.assertEqual(move_qty4.product_uom_qty, 4)
        self.assertEqual(move_qty4.location_id, self.customer_loc)
        self.assertEqual(move_qty4.location_dest_id, self.inventory_loc)
        self.assertEqual(
            move_qty4.move_line_ids.location_id, self.customer_loc)
        self.assertEqual(
            move_qty4.move_line_ids.location_dest_id, self.inventory_loc)
        self.assertEqual(move_qty4.sale_line_id, line_qty4)
        self.assertEqual(move_qty4.sale_line_id.qty_delivered, 4)
        self.assertEqual(list(set(new_pickings.mapped('state'))), ['done'])
        self.assertFalse(new_sale.invoice_ids)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available,
            1000 - 1 - 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0 - 15)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 20)
        self.assertEqual(self.product1.with_context(
            location=self.inventory_loc.id).qty_available,
            -1000 - 9 + 10 + 1 + 4)

    def test_deposit_error_one_line_for_each_product(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        with self.assertRaises(ValidationError):
            wizard = self.env['stock.deposit'].create({
                'create_invoice': True,
                'warehouse_id': self.wh_stock.id,
                'location_id': deposit_loc1.id,
                'partner_id': partner_deposit1_ship.id,
                'price_option': 'last_price',
                'line_ids': [
                    (0, 0, {
                        'ttype': 'sale',
                        'product_id': self.product1.id,
                        'qty': 7,
                    }),
                    (0, 0, {
                        'ttype': 'inventory',
                        'product_id': self.product1.id,
                        'qty': 4,
                    }),
                ],
            })

    def test_deposit_several_types(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.update_qty_on_hand(self.product2, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product2, 5, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 5)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [
                (0, 0, {
                    'ttype': 'sale',
                    'product_id': self.product1.id,
                    'qty': 7,
                }),
                (0, 0, {
                    'ttype': 'inventory',
                    'product_id': self.product2.id,
                    'qty': 4,
                }),
            ],
        })
        for line in wizard.line_ids:
            line.onchange_qty()
        self.assertEqual(wizard.line_ids[0].qty, 7)
        self.assertEqual(wizard.line_ids[0].qty_finish, 5 - 7)
        self.assertEqual(wizard.line_ids[1].qty, 4)
        self.assertEqual(wizard.line_ids[1].qty_finish, 5 - 4)
        with self.assertRaises(UserError):
            wizard.action_confirm()
        wizard.line_ids[0].force_inventory = True
        wizard.line_ids[0].onchange_qty()
        wizard.action_confirm()
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale_type_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
            ('note', 'ilike', 'Type: \'Sale\''),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale_type_sale)
        self.assertEqual(new_sale_type_sale.state, 'sale')
        self.assertEqual(new_sale_type_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale_type_sale.is_sale_deposit)
        self.assertFalse(new_sale_type_sale.is_inventory_deposit)
        self.assertEqual(len(new_sale_type_sale.order_line), 1)
        self.assertEqual(
            new_sale_type_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale_type_sale.order_line.product_uom_qty, 7)
        self.assertEqual(new_sale_type_sale.order_line.price_unit, 10)
        self.assertEqual(new_sale_type_sale.order_line.qty_delivered, 7)
        self.assertEqual(new_sale_type_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale_type_sale.order_line.qty_invoiced, 7)
        new_picking = new_sale_type_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 7)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.move_line_ids.location_dest_id,
            self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale_type_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 7)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale_type_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 7)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 10)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids,
            new_sale_type_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)
        new_sale_type_inv = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
            ('note', 'ilike', 'Type: \'Inventory\''),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale_type_inv)
        self.assertEqual(new_sale_type_inv.state, 'sale')
        self.assertEqual(new_sale_type_inv.invoice_status, 'invoiced')
        self.assertFalse(new_sale_type_inv.is_sale_deposit)
        self.assertTrue(new_sale_type_inv.is_inventory_deposit)
        self.assertEqual(len(new_sale_type_inv.order_line), 1)
        self.assertEqual(
            new_sale_type_inv.order_line.product_id, self.product2)
        self.assertEqual(new_sale_type_inv.order_line.product_uom_qty, 1)
        self.assertEqual(new_sale_type_inv.order_line.price_unit, 20)
        self.assertEqual(new_sale_type_inv.order_line.qty_delivered, 1)
        self.assertEqual(new_sale_type_inv.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale_type_inv.order_line.qty_invoiced, 1)
        new_pickings = new_sale_type_inv.picking_ids
        self.assertEqual(len(new_pickings), 2)
        new_picking1 = new_pickings.filtered(
            lambda p: p.location_id == deposit_loc1
            and p.location_dest_id == self.customer_loc)
        self.assertTrue(new_picking1)
        self.assertEqual(len(new_picking1.move_lines), 1)
        self.assertEqual(new_picking1.move_lines.product_id, self.product2)
        self.assertEqual(new_picking1.move_lines.product_uom_qty, 1)
        self.assertEqual(new_picking1.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking1.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking1.move_lines.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            new_picking1.move_lines.move_line_ids.location_dest_id,
            self.customer_loc)
        self.assertEqual(
            new_picking1.move_lines.sale_line_id, new_sale_type_inv.order_line)
        self.assertEqual(new_picking1.move_lines.sale_line_id.qty_delivered, 1)
        new_picking2 = new_pickings.filtered(
            lambda p: p.location_id == self.customer_loc
            and p.location_dest_id == self.inventory_loc)
        self.assertTrue(new_picking2)
        self.assertEqual(len(new_picking2.move_lines), 1)
        self.assertEqual(new_picking2.move_lines.product_id, self.product2)
        self.assertEqual(new_picking2.move_lines.product_uom_qty, 1)
        self.assertEqual(
            new_picking2.move_lines.location_id, self.customer_loc)
        self.assertEqual(
            new_picking2.move_lines.location_dest_id, self.inventory_loc)
        self.assertEqual(
            new_picking2.move_lines.move_line_ids.location_id,
            self.customer_loc)
        self.assertEqual(
            new_picking2.move_lines.move_line_ids.location_dest_id,
            self.inventory_loc)
        self.assertEqual(
            new_picking2.move_lines.sale_line_id, new_sale_type_inv.order_line)
        self.assertEqual(new_picking2.move_lines.sale_line_id.qty_delivered, 1)
        self.assertEqual(list(set(new_pickings.mapped('state'))), ['done'])
        new_invoice = new_sale_type_inv.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product2)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 1)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 20)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids,
            new_sale_type_inv.order_line)
        self.assertEqual(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product2.with_context(
            location=deposit_loc1.id).qty_available, 5 - 1)
        self.assertEqual(self.product2.with_context(
            location=self.customer_loc.id).qty_available, 0)
        self.assertEqual(self.product2.with_context(
            location=self.inventory_loc.id).qty_available, - 10 + 1)

    def test_deposit_manual_sale_order_boolean_error(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        with self.assertRaises(ValidationError):
            sale1.write({
                'is_sale_deposit': True,
                'is_inventory_deposit': True,
            })

    def test_deposit_manual_sale_order_not_deposit_error(self):
        sale1 = self.create_sale_order(
            self.partner_common, self.partner_common, self.stock_wh,
            self.product1, 5, price_forced=10)
        with self.assertRaises(ValidationError):
            sale1.is_sale_deposit = True

    def test_deposit_manual_sale_order_is_sale_without_stock_ok(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        sale1.is_sale_deposit = True
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 5)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'done')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(picking_int.location_id, deposit_loc1)
        self.assertEqual(picking_int.location_dest_id, self.customer_loc)
        self.assertEqual(sale1.order_line.qty_delivered, 5)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, -5)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 5)
        self.assertFalse(sale1.invoice_ids)
        sale1.action_invoice_create()
        invoice = sale1.invoice_ids
        self.assertEqual(len(invoice), 1)
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(invoice.invoice_line_ids.quantity, 5)
        self.assertEqual(invoice.invoice_line_ids.price_unit, 10)
        self.assertEqual(
            invoice.invoice_line_ids.sale_line_ids, sale1.order_line)

    def test_deposit_manual_sale_order_is_sale_with_stock_ok(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        sale1.is_sale_deposit = True
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 5)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'done')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(picking_int.location_id, deposit_loc1)
        self.assertEqual(picking_int.location_dest_id, self.customer_loc)
        self.assertEqual(sale1.order_line.qty_delivered, 5)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, -5)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 5)
        self.assertFalse(sale1.invoice_ids)
        sale1.action_invoice_create()
        invoice = sale1.invoice_ids
        self.assertEqual(len(invoice), 1)
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(invoice.invoice_line_ids.quantity, 5)
        self.assertEqual(invoice.invoice_line_ids.price_unit, 10)
        self.assertEqual(
            invoice.invoice_line_ids.sale_line_ids, sale1.order_line)

    def test_deposit_manual_sale_order_is_inventory_without_stock_ok(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        sale1.is_inventory_deposit = True
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 5)
        self.assertEqual(len(sale1.picking_ids), 2)
        pickings = sale1.picking_ids
        self.assertEqual(
            list(set(pickings.mapped('picking_type_id'))),
            [self.stock_wh.int_type_id])
        new_picking1 = pickings.filtered(
            lambda p: p.location_id == deposit_loc1
            and p.location_dest_id == self.customer_loc)
        self.assertTrue(new_picking1)
        self.assertEqual(len(new_picking1.move_lines), 1)
        self.assertEqual(new_picking1.move_lines.product_id, self.product1)
        self.assertEqual(new_picking1.move_lines.product_uom_qty, 5)
        self.assertEqual(new_picking1.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking1.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking1.move_lines.move_line_ids.location_id, deposit_loc1)
        self.assertEqual(
            new_picking1.move_lines.move_line_ids.location_dest_id,
            self.customer_loc)
        self.assertEqual(
            new_picking1.move_lines.sale_line_id, sale1.order_line)
        self.assertEqual(new_picking1.move_lines.sale_line_id.qty_delivered, 5)
        new_picking2 = pickings.filtered(
            lambda p: p.location_id == self.customer_loc
            and p.location_dest_id == self.inventory_loc)
        self.assertTrue(new_picking2)
        self.assertEqual(len(new_picking2.move_lines), 1)
        self.assertEqual(new_picking2.move_lines.product_id, self.product1)
        self.assertEqual(new_picking2.move_lines.product_uom_qty, 5)
        self.assertEqual(
            new_picking2.move_lines.location_id, self.customer_loc)
        self.assertEqual(
            new_picking2.move_lines.location_dest_id, self.inventory_loc)
        self.assertEqual(
            new_picking2.move_lines.move_line_ids.location_id,
            self.customer_loc)
        self.assertEqual(
            new_picking2.move_lines.move_line_ids.location_dest_id,
            self.inventory_loc)
        self.assertEqual(
            new_picking2.move_lines.sale_line_id, sale1.order_line)
        self.assertEqual(new_picking2.move_lines.sale_line_id.qty_delivered, 5)
        self.assertEqual(list(set(pickings.mapped('state'))), ['done'])
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0 - 5)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.inventory_loc.id).qty_available, -10 + 5)
        self.assertFalse(sale1.invoice_ids)
        sale1.action_invoice_create()
        invoice = sale1.invoice_ids
        self.assertEqual(len(invoice), 1)
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(invoice.invoice_line_ids.quantity, 5)
        self.assertEqual(invoice.invoice_line_ids.price_unit, 10)
        self.assertEqual(
            invoice.invoice_line_ids.sale_line_ids, sale1.order_line)

    def test_deposit_manual_sale_order_is_inventory_with_stock_ok(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.update_qty_on_hand(self.product1, deposit_loc1, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        sale1.is_sale_deposit = True
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 5)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'done')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(picking_int.location_id, deposit_loc1)
        self.assertEqual(picking_int.location_dest_id, self.customer_loc)
        self.assertEqual(sale1.order_line.qty_delivered, 5)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10 - 5)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 5)
        self.assertFalse(sale1.invoice_ids)
        sale1.action_invoice_create()
        invoice = sale1.invoice_ids
        self.assertEqual(len(invoice), 1)
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(invoice.invoice_line_ids.quantity, 5)
        self.assertEqual(invoice.invoice_line_ids.price_unit, 10)
        self.assertEqual(
            invoice.invoice_line_ids.sale_line_ids, sale1.order_line)

    def test_deposit_sale_real_fifo_inv_sale_line_two_sales_01(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 20)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 20)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 15)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 4,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 4)
        self.assertEqual(wizard.line_ids.qty_finish, 1)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 5)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 6, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 6
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 9)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 7)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 4)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 3,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 3)
        self.assertEqual(wizard.line_ids.qty_finish, 4)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 7)
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 2)
        line_qty1 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertEqual(line_qty1.product_id, self.product1)
        self.assertEqual(line_qty1.price_unit, 10)
        self.assertEqual(line_qty1.qty_delivered, 1)
        self.assertEqual(line_qty1.qty_to_invoice, 0)
        self.assertEqual(line_qty1.qty_invoiced, 1)
        line_qty2 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 2)
        self.assertEqual(line_qty2.product_id, self.product1)
        self.assertEqual(line_qty2.price_unit, 20)
        self.assertEqual(line_qty2.qty_delivered, 2)
        self.assertEqual(line_qty2.qty_to_invoice, 0)
        self.assertEqual(line_qty2.qty_invoiced, 2)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 2)
        move_qty1 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertEqual(move_qty1.product_id, self.product1)
        self.assertEqual(move_qty1.location_id, deposit_loc1)
        self.assertEqual(move_qty1.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty1.sale_line_id, line_qty1)
        self.assertEqual(move_qty1.sale_line_id.qty_delivered, 1)
        move_qty2 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 2)
        self.assertEqual(move_qty2.product_id, self.product1)
        self.assertEqual(move_qty2.location_id, deposit_loc1)
        self.assertEqual(move_qty2.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty2.sale_line_id, line_qty2)
        self.assertEqual(move_qty2.sale_line_id.qty_delivered, 2)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 2)
        line_inv_qty1 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 1)
        self.assertEqual(line_inv_qty1.product_id, self.product1)
        self.assertEqual(line_inv_qty1.price_unit, 10)
        self.assertEqual(line_inv_qty1.sale_line_ids, line_qty1)
        line_inv_qty2 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 2)
        self.assertEqual(line_inv_qty2.product_id, self.product1)
        self.assertEqual(line_inv_qty2.price_unit, 20)
        self.assertEqual(line_inv_qty2.sale_line_ids, line_qty2)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 9)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 4)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_real_fifo_inv_sale_line_two_sales_02(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 20)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 20)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 15)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 4,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 4)
        self.assertEqual(wizard.line_ids.qty_finish, 1)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 5)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 6, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 6
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 9)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 7)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 4)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 1,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 1)
        self.assertEqual(wizard.line_ids.qty_finish, 6)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 7)
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 1)
        self.assertEqual(new_sale.order_line.product_id, self.product1)
        self.assertEqual(new_sale.order_line.product_uom_qty, 1)
        self.assertEqual(new_sale.order_line.price_unit, 10)
        self.assertEqual(new_sale.order_line.qty_delivered, 1)
        self.assertEqual(new_sale.order_line.qty_to_invoice, 0)
        self.assertEqual(new_sale.order_line.qty_invoiced, 1)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product1)
        self.assertEqual(new_picking.move_lines.product_uom_qty, 1)
        self.assertEqual(new_picking.move_lines.location_id, deposit_loc1)
        self.assertEqual(
            new_picking.move_lines.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.move_lines.sale_line_id, new_sale.order_line)
        self.assertEqual(new_picking.move_lines.sale_line_id.qty_delivered, 1)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 1)
        self.assertEqual(
            new_invoice.invoice_line_ids.product_id, self.product1)
        self.assertEqual(new_invoice.invoice_line_ids.quantity, 1)
        self.assertEqual(new_invoice.invoice_line_ids.price_unit, 10)
        self.assertEqual(
            new_invoice.invoice_line_ids.sale_line_ids, new_sale.order_line)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 9)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 6)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 5)

    def test_deposit_sale_real_fifo_inv_sale_line_two_sales_03(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 20)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 20)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 5, price_forced=10)
        self.assertEqual(sale1.warehouse_id, self.stock_wh)
        self.assertEqual(sale1.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale1.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale1.action_confirm()
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(len(sale1.picking_ids), 1)
        picking_int = sale1.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 15)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 5)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 4,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 4)
        self.assertEqual(wizard.line_ids.qty_finish, 1)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 5)
        self.assertEqual(sale1.invoice_status, 'no')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(sale1.order_line.qty_to_invoice, 0)
        self.assertEqual(sale1.order_line.qty_invoiced, 0)
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 6, price_forced=20)
        self.assertEqual(sale2.warehouse_id, self.stock_wh)
        self.assertEqual(sale2.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale2.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale2.action_confirm()
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(len(sale2.picking_ids), 1)
        picking_int = sale2.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 6
        picking_int.action_done()
        sale3 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 8, price_forced=33)
        self.assertEqual(sale3.warehouse_id, self.stock_wh)
        self.assertEqual(sale3.partner_shipping_id, partner_deposit1_ship)
        self.assertEqual(
            sale3.partner_shipping_id.property_stock_customer, deposit_loc1)
        sale3.action_confirm()
        self.assertEqual(sale3.order_line.qty_delivered, 0)
        self.assertEqual(len(sale3.picking_ids), 1)
        picking_int = sale3.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 8
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 1)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 15)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 4)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product1.id,
                'qty': 3,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 3)
        self.assertEqual(wizard.line_ids.qty_finish, 12)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 15)
        self.assertEqual(sale2.invoice_status, 'no')
        self.assertEqual(sale2.order_line.qty_delivered, 0)
        self.assertEqual(sale2.order_line.qty_to_invoice, 0)
        self.assertEqual(sale2.order_line.qty_invoiced, 0)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit1.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')
        self.assertTrue(new_sale.is_sale_deposit)
        self.assertFalse(new_sale.is_inventory_deposit)
        self.assertIn('Type: \'Sale\'', new_sale.note)
        self.assertEqual(len(new_sale.order_line), 2)
        line_qty1 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertEqual(line_qty1.product_id, self.product1)
        self.assertEqual(line_qty1.price_unit, 10)
        self.assertEqual(line_qty1.qty_delivered, 1)
        self.assertEqual(line_qty1.qty_to_invoice, 0)
        self.assertEqual(line_qty1.qty_invoiced, 1)
        line_qty2 = new_sale.order_line.filtered(
            lambda ln: ln.product_uom_qty == 2)
        self.assertEqual(line_qty2.product_id, self.product1)
        self.assertEqual(line_qty2.price_unit, 20)
        self.assertEqual(line_qty2.qty_delivered, 2)
        self.assertEqual(line_qty2.qty_to_invoice, 0)
        self.assertEqual(line_qty2.qty_invoiced, 2)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(len(new_picking.move_lines), 2)
        move_qty1 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 1)
        self.assertEqual(move_qty1.product_id, self.product1)
        self.assertEqual(move_qty1.location_id, deposit_loc1)
        self.assertEqual(move_qty1.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty1.sale_line_id, line_qty1)
        self.assertEqual(move_qty1.sale_line_id.qty_delivered, 1)
        move_qty2 = new_picking.move_lines.filtered(
            lambda ln: ln.product_uom_qty == 2)
        self.assertEqual(move_qty2.product_id, self.product1)
        self.assertEqual(move_qty2.location_id, deposit_loc1)
        self.assertEqual(move_qty2.location_dest_id, self.customer_loc)
        self.assertEqual(move_qty2.sale_line_id, line_qty2)
        self.assertEqual(move_qty2.sale_line_id.qty_delivered, 2)
        self.assertEqual(new_picking.state, 'done')
        new_invoice = new_sale.invoice_ids
        self.assertEqual(len(new_invoice), 1)
        self.assertEqual(len(new_invoice.invoice_line_ids), 2)
        line_inv_qty1 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 1)
        self.assertEqual(line_inv_qty1.product_id, self.product1)
        self.assertEqual(line_inv_qty1.price_unit, 10)
        self.assertEqual(line_inv_qty1.sale_line_ids, line_qty1)
        line_inv_qty2 = new_invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 2)
        self.assertEqual(line_inv_qty2.product_id, self.product1)
        self.assertEqual(line_inv_qty2.price_unit, 20)
        self.assertEqual(line_inv_qty2.sale_line_ids, line_qty2)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 1)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 12)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 7)

    def test_deposit_sale_real_fifo_inventory(self):
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 20)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 9, price_forced=10)
        sale1.action_confirm()
        picking_int = sale1.picking_ids
        picking_int.move_lines.quantity_done = 9
        picking_int.action_done()
        sale2 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 1, price_forced=10)
        sale2.action_confirm()
        picking_int = sale2.picking_ids
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'inventory',
                'product_id': self.product1.id,
                'qty': 9,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 9)
        self.assertEqual(wizard.line_ids.qty_finish, 1)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 10)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 9)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'inventory',
                'product_id': self.product1.id,
                'qty': -1,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, -1)
        self.assertEqual(wizard.line_ids.qty_finish, 10)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 9)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.wh_stock.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'real_fifo',
            'line_ids': [(0, 0, {
                'ttype': 'inventory',
                'product_id': self.product1.id,
                'qty': 0,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 0)
        self.assertEqual(wizard.line_ids.qty_finish, 10)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 10)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=deposit_loc1.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.customer_loc.id).qty_available, 0)

    def test_sale_is_sale_deposit_with_partner_shipping_not_deposit(self):
        deposit1_name = 'Deposit bad 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 20)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 9, price_forced=10)
        sale1.is_sale_deposit = True
        self.assertTrue(sale1.is_sale_deposit)
        partner_deposit1_ship.property_stock_customer = self.customer_loc.id
        self.assertEquals(
            partner_deposit1_ship.property_stock_customer, self.customer_loc)
        with self.assertRaises(ValidationError):
            sale1.action_confirm()
        self.assertEquals(sale1.state, 'draft')

    def test_sale_is_inventory_deposit_with_partner_shipping_not_deposit(self):
        deposit1_name = 'Deposit bad 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 20)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product1, 9, price_forced=10)
        sale1.is_inventory_deposit = True
        self.assertTrue(sale1.is_inventory_deposit)
        partner_deposit1_ship.property_stock_customer = self.customer_loc.id
        self.assertEquals(
            partner_deposit1_ship.property_stock_customer, self.customer_loc)
        with self.assertRaises(ValidationError):
            sale1.action_confirm()
        self.assertEquals(sale1.state, 'draft')
