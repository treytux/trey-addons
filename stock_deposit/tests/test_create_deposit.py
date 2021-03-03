###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestCreateDeposit(TransactionCase):

    def setUp(self):
        super().setUp()
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
        self.customer_loc = self.env.ref(
            'stock.stock_location_locations_partner')
        self.product1 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
            'route_ids': [(6, 0, [self.buy_route.id])],
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

    def create_orderpoint(self, key, product, warehouse):
        return self.env['stock.warehouse.orderpoint'].create({
            'name': 'Orderpoint %s' % key,
            'product_id': product.id,
            'warehouse_id': warehouse.id,
            'location_id': warehouse.out_type_id.default_location_src_id.id,
            'product_min_qty': 5,
            'product_max_qty': 20,
        })

    def create_partner_deposit(self, location):
        self.partner_deposit = self.env['res.partner'].create({
            'name': 'Test deposit partner',
            'customer': True,
        })
        self.partner_deposit_ship = self.env['res.partner'].create({
            'name': 'Test deposit shipping partner',
            'parent_id': self.partner_deposit.id,
            'type': 'delivery',
            'property_stock_customer': location.id,
        })

    def create_sale_order(self, partner, partner_shipping, warehouse, qty):
        order_line = {
            'name': self.product1.name,
            'product_id': self.product1.id,
            'product_uom_qty': qty,
            'product_uom': self.product1.uom_id.id,
            'price_unit': self.product1.list_price,
        }
        return self.env['sale.order'].create({
            'partner_id': partner.id,
            'partner_invoice_id': partner.id,
            'partner_shipping_id': partner_shipping.id,
            'order_line': [(0, 0, order_line)],
            'warehouse_id': warehouse.id,
            'pricelist_id': self.env.ref('product.list0').id,
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

    def check_and_assign_action_create_deposit(self):
        deposits_view_loc = self.stock_wh.deposit_parent_id
        deposits_loc = self.env['stock.location'].search([
            ('name', '=', 'Deposit test'),
        ])
        self.deposit_loc = deposits_loc[0]
        self.assertEquals(len(self.deposit_loc), 1)
        self.assertEquals(self.deposit_loc.usage, 'internal')
        self.assertEquals(self.deposit_loc.location_id, deposits_view_loc)
        self.assertEquals(self.stock_wh.int_type_id.active, True)
        wh2deposit_route = self.env['stock.location.route'].search([
            ('name', '=', '%s -> Deposit test' % self.stock_wh.name),
        ])
        self.assertEquals(len(wh2deposit_route), 1)
        self.assertEquals(wh2deposit_route.warehouse_selectable, True)
        self.assertEquals(wh2deposit_route.product_selectable, False)
        domain_rule = [
            ('name', '=', '%s -> Deposit test' % (
                self.stock_wh.lot_stock_id.name)),
            ('action', '=', 'pull'),
            ('picking_type_id', '=', self.stock_wh.int_type_id.id),
            ('location_src_id', '=', self.stock_wh.lot_stock_id.id),
            ('location_id', '=', self.deposit_loc.id),
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

    def test_create_deposit_and_so_common_with_stock_in_wh(self):
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': 'Deposit test',
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        self.check_and_assign_action_create_deposit()
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.assertEquals(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        sale = self.create_sale_order(
            self.partner_common, self.partner_common, self.stock_wh, 1)
        self.assertEquals(sale.warehouse_id, self.stock_wh)
        self.assertEquals(sale.partner_shipping_id, self.partner_common)
        self.assertEquals(
            sale.partner_shipping_id.property_stock_customer.usage, 'customer')
        sale.action_confirm()
        self.assertEquals(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids
        self.assertEquals(picking_out.state, 'assigned')
        self.assertEquals(
            picking_out.picking_type_id, self.stock_wh.out_type_id)
        self.assertEquals(
            picking_out.location_id.complete_name,
            'Physical Locations/%s/Stock' % self.stock_wh.code)
        self.assertEquals(
            picking_out.location_dest_id.complete_name,
            'Partner Locations/Customers')
        picking_out.move_lines.quantity_done = 1
        picking_out.action_done()
        self.assertEquals(picking_out.state, 'done')
        self.assertEquals(
            self.product1.with_context(
                location=self.stock_wh.lot_stock_id.id).qty_available, 9)

    def test_create_deposit_and_so_common_without_stock_in_wh(self):
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': 'Deposit test',
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        self.check_and_assign_action_create_deposit()
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 0)
        self.assertEquals(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        sale = self.create_sale_order(
            self.partner_common, self.partner_common, self.stock_wh, 1)
        self.assertEquals(sale.warehouse_id, self.stock_wh)
        self.assertEquals(sale.partner_shipping_id, self.partner_common)
        self.assertEquals(
            sale.partner_shipping_id.property_stock_customer.usage, 'customer')
        sale.action_confirm()
        self.assertEquals(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids
        self.assertEquals(picking_out.state, 'confirmed')
        picking_out.action_assign()
        self.assertEquals(picking_out.state, 'confirmed')
        self.assertEquals(
            picking_out.picking_type_id, self.stock_wh.out_type_id)
        self.assertEquals(
            picking_out.location_id.complete_name,
            'Physical Locations/%s/Stock' % self.stock_wh.code)
        self.assertEquals(
            picking_out.location_dest_id.complete_name,
            'Partner Locations/Customers')
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('state', '=', 'draft'),
            ('origin', 'ilike', self.orderpoint.name),
        ])
        self.assertEqual(len(purchases), 1)
        purchase = purchases[0]
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_id, self.product1)
        self.assertEqual(purchase.order_line.orderpoint_id, self.orderpoint)
        self.assertEqual(purchase.order_line.product_qty, 21)
        purchase.button_confirm()
        self.assertEqual(len(purchase.picking_ids), 1)
        picking_in = purchase.picking_ids[0]
        self.assertEqual(picking_in.state, 'assigned')
        self.assertEqual(picking_in.picking_type_id, self.stock_wh.in_type_id)
        self.assertEqual(
            picking_in.location_id.complete_name, 'Partner Locations/Vendors')
        self.assertEqual(
            picking_in.location_dest_id.complete_name,
            'Physical Locations/WH/Stock')
        picking_in.move_lines.quantity_done = 21
        picking_in.action_done()
        self.assertEqual(picking_in.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 21)
        picking_out.move_lines.quantity_done = 1
        picking_out.action_done()
        self.assertEqual(picking_out.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 20)

    def test_create_deposit_and_so_deposit_with_stock_in_wh(self):
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': 'Deposit test',
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        self.check_and_assign_action_create_deposit()
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 10)
        self.create_partner_deposit(self.deposit_loc)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product1.with_context(
            location=self.deposit_loc.id).qty_available, 0)
        sale = self.create_sale_order(
            self.partner_deposit, self.partner_deposit_ship,
            self.stock_wh, 1)
        self.assertEqual(sale.warehouse_id, self.stock_wh)
        self.assertEqual(sale.partner_shipping_id, self.partner_deposit_ship)
        self.assertEqual(
            sale.partner_shipping_id.property_stock_customer,
            self.deposit_loc)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking_int = sale.picking_ids
        self.assertEquals(picking_int.state, 'assigned')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test')
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 9)
        self.assertEqual(self.product1.with_context(
            location=self.deposit_loc.id).qty_available, 1)

    def test_create_deposit_and_so_deposit_without_stock_in_wh(self):
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': 'Deposit test',
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        self.check_and_assign_action_create_deposit()
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 0)
        self.create_partner_deposit(self.deposit_loc)
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product1.with_context(
            location=self.deposit_loc.id).qty_available, 0)
        sale = self.create_sale_order(
            self.partner_deposit, self.partner_deposit_ship,
            self.stock_wh, 1)
        self.assertEqual(sale.warehouse_id, self.stock_wh)
        self.assertEqual(sale.partner_shipping_id, self.partner_deposit_ship)
        self.assertEqual(
            sale.partner_shipping_id.property_stock_customer, self.deposit_loc)
        sale.action_confirm()
        self.assertEqual(len(sale.picking_ids), 1)
        picking_int = sale.picking_ids
        self.assertEqual(picking_int.state, 'confirmed')
        self.assertEqual(
            picking_int.picking_type_id, self.stock_wh.int_type_id)
        self.assertEqual(
            picking_int.location_id.complete_name,
            'Physical Locations/WH/Stock')
        self.assertEqual(
            picking_int.location_dest_id.complete_name,
            'Parent deposits/Deposit test')
        picking_int.action_assign()
        self.assertEqual(picking_int.state, 'confirmed')
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('state', '=', 'draft'),
            ('origin', 'ilike', self.orderpoint.name),
        ])
        self.assertEqual(len(purchases), 1)
        purchase = purchases[0]
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_id, self.product1)
        self.assertEqual(purchase.order_line.orderpoint_id, self.orderpoint)
        self.assertEqual(purchase.order_line.product_qty, 21)
        purchase.button_confirm()
        self.assertEqual(len(purchase.picking_ids), 1)
        picking_in = purchase.picking_ids[0]
        self.assertEqual(picking_in.state, 'assigned')
        self.assertEqual(picking_in.picking_type_id, self.stock_wh.in_type_id)
        self.assertEqual(
            picking_in.location_id.complete_name, 'Partner Locations/Vendors')
        self.assertEqual(
            picking_in.location_dest_id.complete_name,
            'Physical Locations/WH/Stock')
        picking_in.move_lines.quantity_done = 21
        picking_in.action_done()
        self.assertEqual(picking_in.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 21)
        picking_int.move_lines.quantity_done = 1
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 20)
        self.assertEqual(self.product1.with_context(
            location=self.deposit_loc.id).qty_available, 1)

    def test_create_deposit_name_unique(self):
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': 'Deposit test',
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        self.check_and_assign_action_create_deposit()
        with self.assertRaises(ValidationError):
            wizard = self.env['create.deposit'].create({
                'name': 'Deposit test',
                'warehouse_id': self.stock_wh.id,
            })

    def test_create_deposit_without_deposit_parent_id(self):
        self.stock_wh.deposit_parent_id = None
        with self.assertRaises(ValidationError):
            self.env['create.deposit'].create({
                'name': 'Deposit test',
                'warehouse_id': self.stock_wh.id,
            })

    def test_create_deposit_no_view_type(self):
        deposits_no_view_loc = self.env['stock.location'].create({
            'name': 'No view parent deposits',
            'usage': 'internal',
        })
        with self.assertRaises(ValidationError):
            self.stock_wh.deposit_parent_id = deposits_no_view_loc.id
