###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)


class TestIndustryWarehouseOrderpoint(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product = self.env['product.template'].create({
            'name': 'Test Product',
            'purchase_method': 'purchase',
            'type': 'product',
            'standard_price': 10.00,
            'list_price': 100.00,
        }).product_variant_id
        self.stock_wh = self.env.ref('stock.warehouse0')
        self.orderpoint = self.env['stock.warehouse.orderpoint'].create({
            'warehouse_id': self.stock_wh.id,
            'location_id': self.stock_wh.lot_stock_id.id,
            'product_id': self.product.id,
            'product_min_qty': 25.00,
            'product_max_qty': 50.00,
        })
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.customer_loc = self.env.ref('stock.stock_location_customers')
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
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

    def create_inventory(self, location, product, qty):
        self.env['stock.quant']._update_available_quantity(
            product, location, qty)

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

    def create_parent_deposit_location(self):
        return self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
            'location_id': self.stock_wh.view_location_id.id,
        })

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

    def test_annual_without_deposit(self):
        self.assertEqual(self.env.user.company_id.period_min_qty, 'annual')
        self.create_inventory(self.stock_location, self.product, 25)
        self.assertEqual(
            self.env['stock.quant']._get_available_quantity(
                self.product, self.stock_location), 25.0)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).qty_available, 25)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 25)
        self.assertEqual(self.orderpoint.product_location_qty, 25)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 25)
        self.orderpoint.compute_product_min_qty_period()
        self.assertEqual(self.orderpoint.product_min_qty_period, 0)
        self.assertEqual(self.orderpoint.product_suggested_qty, -25)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 10,
                }),
            ],
        })
        sale.action_confirm()
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).qty_available, 15)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 15)
        self.assertEqual(self.orderpoint.product_location_qty, 25)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 25)
        self.orderpoint.compute_product_min_qty_period()
        # round(sum(out)-sum(in))
        # round(10-0)/12 = 1
        self.assertEqual(self.orderpoint.product_min_qty_period, 1)
        # (op.product_min_qty_period - op.virtual_location_qty)
        # (1 - 25)=-24
        self.assertEqual(self.orderpoint.product_suggested_qty, -24)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.quantity = 6
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.quantity_done = 6
        return_pick.move_lines.to_refund = True
        return_pick.action_done()
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).qty_available, 21)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 21)
        self.assertEqual(self.orderpoint.product_location_qty, 25)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 25)
        self.orderpoint.compute_product_min_qty_period()
        # round(sum(out)-sum(in))
        # round(10-6)/12 = 0
        self.assertEqual(self.orderpoint.product_min_qty_period, 0)
        # (op.product_min_qty_period - op.virtual_location_qty)
        # (0 - 25)=-25
        self.assertEqual(self.orderpoint.product_suggested_qty, -25)

    def test_annual_with_deposit_sale_deposit_and_move_deposit_to_customer(
            self):
        self.assertEqual(self.env.user.company_id.period_min_qty, 'annual')
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.create_parent_deposit_location()
        self.assertTrue(deposits_view_loc.get_warehouse())
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.create_inventory(self.stock_location, self.product, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.orderpoint.product_location_qty, 10)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 10)
        self.orderpoint.compute_product_min_qty_period()
        self.assertEqual(self.orderpoint.product_min_qty_period, 0)
        self.assertEqual(self.orderpoint.product_suggested_qty, -10)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product, 5, price_forced=10)
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
            'Physical Locations/WH/Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product.with_context(
            location=deposit_loc1.id).qty_available, 5)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 5)
        self.assertEqual(self.orderpoint.product_location_qty, 10)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 10)
        self.orderpoint.compute_product_min_qty_period()
        # round(sum(out)-sum(in))
        # round(5-0)/12 = 0
        self.assertEqual(self.orderpoint.product_min_qty_period, 0)
        # (op.product_min_qty_period - op.virtual_location_qty)
        # (0 - 10)=-10
        self.assertEqual(self.orderpoint.product_suggested_qty, -10)
        # Consigna => Cliente = NADA, ni IN ni OUT
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.stock_wh.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product.id,
                'qty': 2,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 3)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 5)
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
        self.assertEqual(new_sale.order_line.product_id, self.product)
        self.assertEqual(new_sale.order_line.product_uom_qty, 2)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.picking_type_id, self.stock_wh.out_type_id)
        self.assertIn('OUT', new_picking.name)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product)
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
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).qty_available, 5)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 5)
        self.assertEqual(self.orderpoint.product_location_qty, 5)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 5)
        self.orderpoint.compute_product_min_qty_period()
        # round(sum(out)-sum(in))
        # round(10-0)/12 = 1
        self.assertEqual(self.orderpoint.product_min_qty_period, 0)
        # (op.product_min_qty_period - op.virtual_location_qty)
        # (0 - 55)=-5
        self.assertEqual(self.orderpoint.product_suggested_qty, -5)

    def test_annual_with_deposit_sale_deposit_and_return_deposit_to_stock(
            self):
        self.assertEqual(self.env.user.company_id.period_min_qty, 'annual')
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.create_parent_deposit_location()
        self.assertTrue(deposits_view_loc.get_warehouse())
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.create_inventory(self.stock_location, self.product, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.orderpoint.product_location_qty, 10)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 10)
        self.orderpoint.compute_product_min_qty_period()
        self.assertEqual(self.orderpoint.product_min_qty_period, 0)
        self.assertEqual(self.orderpoint.product_suggested_qty, -10)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product, 5, price_forced=10)
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
            'Physical Locations/WH/Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product.with_context(
            location=deposit_loc1.id).qty_available, 5)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 5)
        self.assertEqual(self.orderpoint.product_location_qty, 10)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 10)
        self.orderpoint.compute_product_min_qty_period()
        # round(sum(out)-sum(in))
        # round(5-0)/12 = 0
        self.assertEqual(self.orderpoint.product_min_qty_period, 0)
        # (op.product_min_qty_period - op.virtual_location_qty)
        # (0 - 10)=-10
        self.assertEqual(self.orderpoint.product_suggested_qty, -10)
        # Devolución Consigna=>stock = IN
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_int.ids,
            active_id=picking_int.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.quantity = 5
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.quantity_done = 5
        return_pick.move_lines.to_refund = True
        return_pick.action_done()
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).qty_available, 10)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 10)
        self.assertEqual(self.orderpoint.product_location_qty, 10)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 10)
        self.orderpoint.compute_product_min_qty_period()
        # round(sum(out)-sum(in))
        # round(5-5)/12 = 0
        self.assertEqual(self.orderpoint.product_min_qty_period, 0)
        # (op.product_min_qty_period - op.virtual_location_qty)
        # (0 - 10)=-10
        self.assertEqual(self.orderpoint.product_suggested_qty, -10)

    def test_annual_with_and_without_deposit(self):
        self.assertEqual(self.env.user.company_id.period_min_qty, 'annual')
        self.create_inventory(self.stock_location, self.product, 25)
        self.assertEqual(
            self.env['stock.quant']._get_available_quantity(
                self.product, self.stock_location), 25.0)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).qty_available, 25)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 25)
        self.assertEqual(self.orderpoint.product_location_qty, 25)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 25)
        self.orderpoint.compute_product_min_qty_period()
        self.assertEqual(self.orderpoint.product_min_qty_period, 0)
        self.assertEqual(self.orderpoint.product_suggested_qty, -25)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 10,
                }),
            ],
        })
        sale.action_confirm()
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).qty_available, 15)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 15)
        self.assertEqual(self.orderpoint.product_location_qty, 25)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 25)
        self.orderpoint.compute_product_min_qty_period()
        # round(sum(out)-sum(in))
        # round(10-0)/12 = 1
        self.assertEqual(self.orderpoint.product_min_qty_period, 1)
        # (op.product_min_qty_period - op.virtual_location_qty)
        # (1 - 25)=-24
        self.assertEqual(self.orderpoint.product_suggested_qty, -24)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.quantity = 6
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.quantity_done = 6
        return_pick.move_lines.to_refund = True
        return_pick.action_done()
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).qty_available, 21)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 21)
        self.assertEqual(self.orderpoint.product_location_qty, 25)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 25)
        self.orderpoint.compute_product_min_qty_period()
        # round(sum(out)-sum(in))
        # round(10-6)/12 = 0
        self.assertEqual(self.orderpoint.product_min_qty_period, 0)
        # (op.product_min_qty_period - op.virtual_location_qty)
        # (0 - 25)=-25
        self.assertEqual(self.orderpoint.product_suggested_qty, -25)
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.create_parent_deposit_location()
        self.assertTrue(deposits_view_loc.get_warehouse())
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
        self.assertEqual(self.product.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 21)
        self.assertEqual(self.product.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.orderpoint.product_location_qty, 25)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 25)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product, 5, price_forced=10)
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
            'Physical Locations/WH/Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 16)
        self.assertEqual(self.product.with_context(
            location=deposit_loc1.id).qty_available, 5)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 16)
        self.assertEqual(self.orderpoint.product_location_qty, 25)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 25)
        self.orderpoint.compute_product_min_qty_period()
        # round(sum(out)-sum(in))
        # round(15-6)/12 = 1
        self.assertEqual(self.orderpoint.product_min_qty_period, 1)
        # (op.product_min_qty_period - op.virtual_location_qty)
        # (1 - 25)=-24
        self.assertEqual(self.orderpoint.product_suggested_qty, -24)

    def test_semester_without_deposit(self):
        self.env.user.company_id.period_min_qty = 'semester'
        self.create_inventory(self.stock_location, self.product, 25)
        self.assertEqual(
            self.env['stock.quant']._get_available_quantity(
                self.product, self.stock_location), 25.0)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).qty_available, 25)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 25)
        self.assertEqual(self.orderpoint.product_location_qty, 25)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 25)
        self.orderpoint.compute_product_min_qty_period()
        self.assertEqual(self.orderpoint.product_min_qty_period, 0)
        self.assertEqual(self.orderpoint.product_suggested_qty, -25)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 10,
                }),
            ],
        })
        sale.action_confirm()
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).qty_available, 15)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 15)
        self.assertEqual(self.orderpoint.product_location_qty, 25)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 25)
        self.orderpoint.compute_product_min_qty_period()
        # round(sum(out)-sum(in))
        # round(10-0)/6 = 2
        self.assertEqual(self.orderpoint.product_min_qty_period, 2)
        # (op.product_min_qty_period - op.virtual_location_qty)
        # (2 - 25)=-23
        self.assertEqual(self.orderpoint.product_suggested_qty, -23)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.quantity = 6
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.quantity_done = 6
        return_pick.move_lines.to_refund = True
        return_pick.action_done()
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).qty_available, 21)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 21)
        self.assertEqual(self.orderpoint.product_location_qty, 25)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 25)
        self.orderpoint.compute_product_min_qty_period()
        # round(sum(out)-sum(in))
        # round(10-6)/4 = 1
        self.assertEqual(self.orderpoint.product_min_qty_period, 1)
        # (op.product_min_qty_period - op.virtual_location_qty)
        # (1 - 25)=-24
        self.assertEqual(self.orderpoint.product_suggested_qty, -24)

    def test_semester_with_deposit_sale_deposit_and_move_deposit_to_customer(
            self):
        self.env.user.company_id.period_min_qty = 'semester'
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.create_parent_deposit_location()
        self.assertTrue(deposits_view_loc.get_warehouse())
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.create_inventory(self.stock_location, self.product, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.orderpoint.product_location_qty, 10)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 10)
        self.orderpoint.compute_product_min_qty_period()
        self.assertEqual(self.orderpoint.product_min_qty_period, 0)
        self.assertEqual(self.orderpoint.product_suggested_qty, -10)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product, 5, price_forced=10)
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
            'Physical Locations/WH/Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product.with_context(
            location=deposit_loc1.id).qty_available, 5)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 5)
        self.assertEqual(self.orderpoint.product_location_qty, 10)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 10)
        self.orderpoint.compute_product_min_qty_period()
        # round(sum(out)-sum(in))
        # round(5-0)/6 = 1
        self.assertEqual(self.orderpoint.product_min_qty_period, 1)
        # (op.product_min_qty_period - op.virtual_location_qty)
        # (1 - 10)=-9
        self.assertEqual(self.orderpoint.product_suggested_qty, -9)
        # Consigna => Cliente = NADA, ni IN ni OUT
        wizard = self.env['stock.deposit'].create({
            'create_invoice': True,
            'warehouse_id': self.stock_wh.id,
            'location_id': deposit_loc1.id,
            'partner_id': partner_deposit1_ship.id,
            'price_option': 'last_price',
            'line_ids': [(0, 0, {
                'ttype': 'sale',
                'product_id': self.product.id,
                'qty': 2,
            })],
        })
        wizard.line_ids.onchange_qty()
        self.assertEqual(wizard.line_ids.qty, 2)
        self.assertEqual(wizard.line_ids.qty_finish, 3)
        wizard.action_confirm()
        self.assertEqual(wizard.line_ids.qty_theorical, 5)
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
        self.assertEqual(new_sale.order_line.product_id, self.product)
        self.assertEqual(new_sale.order_line.product_uom_qty, 2)
        new_picking = new_sale.picking_ids
        self.assertEqual(len(new_picking), 1)
        self.assertEqual(new_picking.location_id, deposit_loc1)
        self.assertEqual(new_picking.location_dest_id, self.customer_loc)
        self.assertEqual(
            new_picking.picking_type_id, self.stock_wh.out_type_id)
        self.assertIn('OUT', new_picking.name)
        self.assertEqual(len(new_picking.move_lines), 1)
        self.assertEqual(new_picking.move_lines.product_id, self.product)
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
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).qty_available, 5)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 5)
        self.assertEqual(self.orderpoint.product_location_qty, 5)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 5)
        self.orderpoint.compute_product_min_qty_period()
        # round(sum(out)-sum(in))
        # round(5-0)/6 = 1
        self.assertEqual(self.orderpoint.product_min_qty_period, 1)
        # (op.product_min_qty_period - op.virtual_location_qty)
        # (1 - 5)=-4
        self.assertEqual(self.orderpoint.product_suggested_qty, -4)

    def test_semester_with_deposit_sale_deposit_and_return_deposit_to_stock(
            self):
        self.env.user.company_id.period_min_qty = 'semester'
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.create_parent_deposit_location()
        self.assertTrue(deposits_view_loc.get_warehouse())
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit1_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc1 = self.check_and_assign_action_create_deposit(
            deposit1_name)
        self.create_inventory(self.stock_location, self.product, 10)
        partner_deposit1, partner_deposit1_ship = self.create_partner_deposit(
            deposit1_name, deposit_loc1)
        self.assertEqual(self.product.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 10)
        self.assertEqual(self.product.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.orderpoint.product_location_qty, 10)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 10)
        self.orderpoint.compute_product_min_qty_period()
        self.assertEqual(self.orderpoint.product_min_qty_period, 0)
        self.assertEqual(self.orderpoint.product_suggested_qty, -10)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product, 5, price_forced=10)
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
            'Physical Locations/WH/Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 5)
        self.assertEqual(self.product.with_context(
            location=deposit_loc1.id).qty_available, 5)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 5)
        self.assertEqual(self.orderpoint.product_location_qty, 10)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 10)
        self.orderpoint.compute_product_min_qty_period()
        # round(sum(out)-sum(in))
        # round(5-0)/6 = 1
        self.assertEqual(self.orderpoint.product_min_qty_period, 1)
        # (op.product_min_qty_period - op.virtual_location_qty)
        # (1 - 10)=-9
        self.assertEqual(self.orderpoint.product_suggested_qty, -9)
        # Devolución Consigna=>stock = IN
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_int.ids,
            active_id=picking_int.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.quantity = 5
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.quantity_done = 5
        return_pick.move_lines.to_refund = True
        return_pick.action_done()
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).qty_available, 10)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 10)
        self.assertEqual(self.orderpoint.product_location_qty, 10)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 10)
        self.orderpoint.compute_product_min_qty_period()
        # round(sum(out)-sum(in))
        # round(5-5)/6 = 0
        self.assertEqual(self.orderpoint.product_min_qty_period, 0)
        # (op.product_min_qty_period - op.virtual_location_qty)
        # (0 - 10)=-10
        self.assertEqual(self.orderpoint.product_suggested_qty, -10)

    def test_semester_with_and_without_deposit(self):
        self.env.user.company_id.period_min_qty = 'semester'
        self.create_inventory(self.stock_location, self.product, 25)
        self.assertEqual(
            self.env['stock.quant']._get_available_quantity(
                self.product, self.stock_location), 25.0)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).qty_available, 25)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 25)
        self.assertEqual(self.orderpoint.product_location_qty, 25)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 25)
        self.orderpoint.compute_product_min_qty_period()
        self.assertEqual(self.orderpoint.product_min_qty_period, 0)
        self.assertEqual(self.orderpoint.product_suggested_qty, -25)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 10,
                }),
            ],
        })
        sale.action_confirm()
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).qty_available, 15)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 15)
        self.assertEqual(self.orderpoint.product_location_qty, 25)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 25)
        self.orderpoint.compute_product_min_qty_period()
        # round(sum(out)-sum(in))
        # round(10-0)/6 = 2
        self.assertEqual(self.orderpoint.product_min_qty_period, 2)
        # (op.product_min_qty_period - op.virtual_location_qty)
        # (2 - 25)=-23
        self.assertEqual(self.orderpoint.product_suggested_qty, -23)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.quantity = 6
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.quantity_done = 6
        return_pick.move_lines.to_refund = True
        return_pick.action_done()
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).qty_available, 21)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 21)
        self.assertEqual(self.orderpoint.product_location_qty, 25)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 25)
        self.orderpoint.compute_product_min_qty_period()
        # round(sum(out)-sum(in))
        # round(10-6)/6 = 1
        self.assertEqual(self.orderpoint.product_min_qty_period, 1)
        # (op.product_min_qty_period - op.virtual_location_qty)
        # (1 - 25)=-24
        self.assertEqual(self.orderpoint.product_suggested_qty, -24)
        deposit1_name = 'Deposit test 1'
        deposits_view_loc = self.create_parent_deposit_location()
        self.assertTrue(deposits_view_loc.get_warehouse())
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
        self.assertEqual(self.product.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 21)
        self.assertEqual(self.product.with_context(
            location=deposit_loc1.id).qty_available, 0)
        self.assertEqual(self.orderpoint.product_location_qty, 25)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 25)
        sale1 = self.create_sale_order(
            partner_deposit1, partner_deposit1_ship, self.stock_wh,
            self.product, 5, price_forced=10)
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
            'Physical Locations/WH/Parent deposits/Deposit test 1')
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        self.assertEqual(picking_int.state, 'done')
        self.assertEqual(sale1.order_line.qty_delivered, 0)
        self.assertEqual(self.product.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 16)
        self.assertEqual(self.product.with_context(
            location=deposit_loc1.id).qty_available, 5)
        self.assertEquals(self.product.with_context(
            location=self.stock_location.id).virtual_available, 16)
        self.assertEqual(self.orderpoint.product_location_qty, 25)
        self.assertEqual(self.orderpoint.incoming_location_qty, 0)
        self.assertEqual(self.orderpoint.outgoing_location_qty, 0)
        self.assertEqual(self.orderpoint.virtual_location_qty, 25)
        self.orderpoint.compute_product_min_qty_period()
        # round(sum(out)-sum(in))
        # round(15-6)/6 = 2
        self.assertEqual(self.orderpoint.product_min_qty_period, 2)
        # (op.product_min_qty_period - op.virtual_location_qty)
        # (2 - 25)=-23
        self.assertEqual(self.orderpoint.product_suggested_qty, -23)
