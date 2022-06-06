###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestStockRulePurchaseFix(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.ref('base.main_company')
        self.warehouse = self.env.ref('stock.warehouse0')
        self.warehouse.mto_mts_management = True
        self.stock_loc = self.warehouse.lot_stock_id
        self.customer_loc = self.env.ref('stock.stock_location_customers')
        self.supplier_loc = self.env.ref('stock.stock_location_suppliers')
        self.picking_type_out = self.warehouse.out_type_id
        self.picking_type_in = self.warehouse.in_type_id
        self.buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        module = self.env['ir.module.module'].search([
            ('name', '=', 'stock_mts_mto_rule'),
        ])
        if module.state == 'installed':
            self.mts_mto_route = self.env.ref(
                'stock_mts_mto_rule.route_mto_mts')
        self.mto_route = self.env.ref('stock.route_warehouse0_mto')
        self.customer = self.env['res.partner'].create({
            'name': 'Test customer',
            'customer': True,
            'company_id': self.company.id,
        })
        self.supplier = self.env['res.partner'].create({
            'name': 'Test supplier',
            'supplier': True,
            'company_id': self.company.id,
        })

    def update_qty_on_hand(self, product, location, new_qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': new_qty,
            'location_id': location.id,
        })
        wizard.change_product_qty()

    def create_orderpoint(self, warehouse, product, min_qty=0, max_qty=0):
        return self.env['stock.warehouse.orderpoint'].create({
            'name': 'OP/%s' % product.name,
            'product_id': product.id,
            'warehouse_id': warehouse.id,
            'location_id': warehouse.out_type_id.default_location_src_id.id,
            'product_min_qty': min_qty,
            'product_max_qty': max_qty,
        })

    def create_sale(self, product, quantity, warehouse):
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'company_id': self.company.id,
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
        picking.action_assign()
        picking.action_confirm()
        for move in picking.move_lines:
            move.quantity_done = qty
        picking.action_done()

    def test_standard_buy_route(self):
        product_buy = self.env['product.product'].create({
            'name': 'Test product buy',
            'type': 'product',
            'company_id': self.company.id,
            'route_ids': [(6, 0, [self.buy_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'price': 10,
            })],
        })
        self.create_orderpoint(self.warehouse, product_buy)
        self.update_qty_on_hand(product_buy, self.warehouse.lot_stock_id, 10)
        self.assertEquals(product_buy.with_context(
            location=self.warehouse.lot_stock_id.id).qty_available, 10)
        sale = self.create_sale(product_buy, 10, self.warehouse)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(picking.location_id, self.stock_loc)
        self.assertEquals(picking.location_dest_id, self.customer_loc)
        self.picking_transfer(picking, 10)
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEquals(len(purchases), 0)
        self.assertEquals(product_buy.qty_available, 0)
        sale = self.create_sale(product_buy, 10, self.warehouse)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(picking.location_id, self.stock_loc)
        self.assertEquals(picking.location_dest_id, self.customer_loc)
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEquals(len(purchases), 1)
        self.assertEquals(purchases.order_line.product_uom_qty, 10)

    def test_standard_buy_and_mto_route(self):
        product_buy_mto = self.env['product.product'].create({
            'name': 'Test product buy MTO',
            'type': 'product',
            'company_id': self.company.id,
            'route_ids': [(6, 0, [self.buy_route.id, self.mto_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'price': 10,
            })],
        })
        self.create_orderpoint(self.warehouse, product_buy_mto)
        self.update_qty_on_hand(
            product_buy_mto, self.warehouse.lot_stock_id, 99)
        self.assertEquals(product_buy_mto.with_context(
            location=self.warehouse.lot_stock_id.id).qty_available, 99)
        sale = self.create_sale(product_buy_mto, 10, self.warehouse)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(picking.location_id, self.stock_loc)
        self.assertEquals(picking.location_dest_id, self.customer_loc)
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEquals(len(purchases), 1)
        self.assertEquals(purchases.order_line.product_uom_qty, 10)
        purchases.button_confirm()
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEquals(len(purchases), 1)
        self.assertEquals(purchases.order_line.product_uom_qty, 10)
        self.assertEquals(product_buy_mto.qty_available, 99)
        sale = self.create_sale(product_buy_mto, 10, self.warehouse)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(picking.location_id, self.stock_loc)
        self.assertEquals(picking.location_dest_id, self.customer_loc)
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
            ('state', '=', 'draft'),
        ])
        self.assertEquals(len(purchases), 1)
        self.assertEquals(purchases.order_line.product_uom_qty, 10)
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
            ('state', '=', 'draft'),
        ])
        self.assertEquals(len(purchases), 1)
        self.assertEquals(purchases.order_line.product_uom_qty, 10)

    def test_mts_mto_and_buy_route_mts_only(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'stock_mts_mto_rule'),
        ])
        if module.state != 'installed':
            self.skipTest('stock_mts_mto_rule not installed, ignore test.')
        product_mts_mto = self.env['product.product'].create({
            'name': 'Test product mts+mto',
            'type': 'product',
            'company_id': self.company.id,
            'route_ids': [(6, 0, [self.mts_mto_route.id, self.buy_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'delay': 1,
                'price': 5,
            })],
        })
        self.create_orderpoint(self.warehouse, product_mts_mto)
        self.update_qty_on_hand(
            product_mts_mto, self.warehouse.lot_stock_id, 100)
        sale = self.create_sale(product_mts_mto, 10, self.warehouse)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(picking.picking_type_id, self.picking_type_out)
        self.assertEquals(picking.location_id, self.stock_loc)
        self.assertEquals(picking.location_dest_id, self.customer_loc)
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.move_lines.product_uom_qty, 10)
        self.picking_transfer(picking, qty=10)
        purchase = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
        ])
        self.assertEquals(len(purchase), 0)
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEquals(len(purchases), 0)

    def test_mts_mto_and_buy_route_mto_only_duplicate_qty(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'stock_mts_mto_rule'),
        ])
        if module.state != 'installed':
            self.skipTest('stock_mts_mto_rule not installed, ignore test.')
        product_mts_mto = self.env['product.product'].create({
            'name': 'Test product mts+mto',
            'type': 'product',
            'company_id': self.company.id,
            'route_ids': [(6, 0, [self.mts_mto_route.id, self.buy_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'delay': 1,
                'price': 5,
            })],
        })
        self.create_orderpoint(self.warehouse, product_mts_mto, 3)
        sale = self.create_sale(product_mts_mto, 10, self.warehouse)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(picking.state, 'waiting')
        self.assertEquals(picking.picking_type_id, self.picking_type_out)
        self.assertEquals(picking.location_id, self.stock_loc)
        self.assertEquals(picking.location_dest_id, self.customer_loc)
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.move_lines.product_uom_qty, 10)
        purchase = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
        ])
        self.assertEquals(len(purchase), 1)
        self.assertEquals(purchase.state, 'draft')
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.order_line[0].product_uom_qty, 10)
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEquals(len(purchases), 1)
        self.assertEquals(purchases.order_line.product_uom_qty, 13)
        purchase.button_confirm()
        self.assertEquals(len(purchase.picking_ids), 1)
        purchase_picking = purchase.picking_ids
        self.picking_transfer(purchase_picking, qty=13)
        self.assertEquals(
            purchase_picking.picking_type_id, self.picking_type_in)
        self.assertEquals(purchase_picking.location_id, self.supplier_loc)
        self.assertEquals(purchase_picking.location_dest_id, self.stock_loc)

    def test_mts_mto_and_buy_route_mto_only(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'stock_mts_mto_rule'),
        ])
        if module.state != 'installed':
            self.skipTest('stock_mts_mto_rule not installed, ignore test.')
        product_mts_mto = self.env['product.product'].create({
            'name': 'Product mts+mto',
            'type': 'product',
            'company_id': self.company.id,
            'route_ids': [(6, 0, [self.mts_mto_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'delay': 1,
                'price': 5,
            })],
        })
        self.create_orderpoint(self.warehouse, product_mts_mto, 3)
        sale = self.create_sale(product_mts_mto, 10, self.warehouse)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(picking.state, 'waiting')
        self.assertEquals(picking.picking_type_id, self.picking_type_out)
        self.assertEquals(picking.location_id, self.stock_loc)
        self.assertEquals(picking.location_dest_id, self.customer_loc)
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.move_lines.product_uom_qty, 10)
        purchase = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
        ])
        self.assertEquals(len(purchase), 1)
        self.assertEquals(purchase.state, 'draft')
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.order_line[0].product_uom_qty, 10)
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
            ('state', '=', 'draft'),
        ])
        self.assertEquals(len(purchases), 1)
        self.assertEquals(purchases.order_line.product_uom_qty, 13)
        product_mts_mto.orderpoint_ids.product_min_qty = 5
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
            ('state', '=', 'draft'),
        ])
        self.assertEquals(len(purchases), 1)
        self.assertEquals(purchases.order_line.product_uom_qty, 15)
        product_mts_mto.orderpoint_ids.product_min_qty = 0
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
            ('state', '=', 'draft'),
        ])
        self.assertEquals(len(purchases), 1)
        self.assertEquals(purchases.order_line.product_uom_qty, 15)
        purchase.button_confirm()
        self.assertEquals(len(purchase.picking_ids), 1)
        purchase_picking = purchase.picking_ids
        self.picking_transfer(purchase_picking, qty=15)
        self.assertEquals(
            purchase_picking.picking_type_id, self.picking_type_in)
        self.assertEquals(purchase_picking.location_id, self.supplier_loc)
        self.assertEquals(purchase_picking.location_dest_id, self.stock_loc)

    def test_mts_mto_and_buy_route_split(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'stock_mts_mto_rule'),
        ])
        if module.state != 'installed':
            self.skipTest('stock_mts_mto_rule not installed, ignore test.')
        product_mts_mto = self.env['product.product'].create({
            'name': 'Test product mts+mto',
            'type': 'product',
            'company_id': self.company.id,
            'route_ids': [(6, 0, [self.mts_mto_route.id, self.buy_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'delay': 1,
                'price': 5,
            })],
        })
        self.create_orderpoint(self.warehouse, product_mts_mto)
        self.update_qty_on_hand(
            product_mts_mto, self.warehouse.lot_stock_id, 7)
        sale = self.create_sale(product_mts_mto, 10, self.warehouse)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        sale_picking = sale.picking_ids[0]
        self.assertEquals(sale_picking.picking_type_id, self.picking_type_out)
        self.assertEquals(sale_picking.location_id, self.stock_loc)
        self.assertEquals(sale_picking.location_dest_id, self.customer_loc)
        self.assertEquals(len(sale_picking.move_lines), 2)
        move_qty_7 = sale_picking.move_lines.filtered(
            lambda m: m.product_uom_qty == 7)
        self.assertTrue(move_qty_7)
        move_qty_3 = sale_picking.move_lines.filtered(
            lambda m: m.product_uom_qty == 3)
        self.assertTrue(move_qty_3)
        purchase = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
        ])
        self.assertEquals(len(purchase), 1)
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.order_line.product_uom_qty, 3)
        self.assertEquals(purchase.state, 'draft')
        purchase.button_confirm()
        self.assertEquals(len(purchase.picking_ids), 1)
        purchase_picking = purchase.picking_ids
        self.picking_transfer(purchase_picking, qty=3)
        self.assertEquals(
            purchase_picking.picking_type_id, self.picking_type_in)
        self.assertEquals(purchase_picking.location_id, self.supplier_loc)
        self.assertEquals(purchase_picking.location_dest_id, self.stock_loc)
        self.assertEquals(purchase_picking.location_id, self.supplier_loc)
        self.assertEquals(purchase_picking.location_dest_id, self.stock_loc)
        self.assertEquals(len(purchase_picking.move_lines), 1)
        self.assertEquals(purchase_picking.move_lines.product_uom_qty, 3)
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEquals(len(purchases), 1)

    def test_standard_buy_route_multi_warehouses(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'stock_mts_mto_rule'),
        ])
        if module.state != 'installed':
            self.skipTest('stock_mts_mto_rule not installed, ignore test.')
        warehouse2 = self.env['stock.warehouse'].create({
            'code': 'WH2',
            'name': 'Warehouse 2',
        })
        rule_wh2 = self.env['stock.rule'].search([
            ('location_id', '=', warehouse2.lot_stock_id.id),
            ('route_id', '=', self.mts_mto_route.id),
            ('action', '=', 'buy'),
        ])
        self.assertEquals(len(rule_wh2), 0)
        warehouse2.mto_mts_management = True
        rule_wh1 = self.env['stock.rule'].search([
            ('location_id', '=', self.warehouse.lot_stock_id.id),
            ('route_id', '=', self.mts_mto_route.id),
            ('action', '=', 'buy'),
        ])
        self.assertEquals(len(rule_wh1), 1)
        rule_wh2 = self.env['stock.rule'].search([
            ('location_id', '=', warehouse2.lot_stock_id.id),
            ('route_id', '=', self.mts_mto_route.id),
            ('action', '=', 'buy'),
        ])
        self.assertEquals(len(rule_wh2), 1)
        product_buy = self.env['product.product'].create({
            'name': 'Test product buy',
            'type': 'product',
            'company_id': self.company.id,
            'route_ids': [(6, 0, [self.buy_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'price': 10,
            })],
        })
        self.create_orderpoint(warehouse2, product_buy)
        self.update_qty_on_hand(product_buy, warehouse2.lot_stock_id, 10)
        self.assertEquals(product_buy.with_context(
            location=warehouse2.lot_stock_id.id).qty_available, 10)
        sale = self.create_sale(product_buy, 10, warehouse2)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(picking.location_id, warehouse2.lot_stock_id)
        self.assertEquals(picking.location_dest_id, self.customer_loc)
        self.picking_transfer(picking, 10)
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEquals(len(purchases), 0)
        self.assertEquals(product_buy.qty_available, 0)
        sale = self.create_sale(product_buy, 10, warehouse2)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(picking.location_id, warehouse2.lot_stock_id)
        self.assertEquals(picking.location_dest_id, self.customer_loc)
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEquals(len(purchases), 1)
        self.assertEquals(purchases.order_line.product_uom_qty, 10)

    def test_standard_buy_and_mto_route_multi_warehouses(self):
        warehouse2 = self.env['stock.warehouse'].create({
            'code': 'WH2',
            'name': 'Warehouse 2',
        })
        warehouse2.mto_mts_management = True
        product_buy_mto = self.env['product.product'].create({
            'name': 'Test product buy MTO',
            'type': 'product',
            'company_id': self.company.id,
            'route_ids': [(6, 0, [self.buy_route.id, self.mto_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'price': 10,
            })],
        })
        self.create_orderpoint(warehouse2, product_buy_mto)
        self.update_qty_on_hand(product_buy_mto, warehouse2.lot_stock_id, 99)
        self.assertEquals(product_buy_mto.with_context(
            location=warehouse2.lot_stock_id.id).qty_available, 99)
        sale = self.create_sale(product_buy_mto, 10, warehouse2)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(picking.location_id, warehouse2.lot_stock_id)
        self.assertEquals(picking.location_dest_id, self.customer_loc)
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEquals(len(purchases), 1)
        self.assertEquals(purchases.order_line.product_uom_qty, 10)
        purchases.button_confirm()
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEquals(len(purchases), 1)
        self.assertEquals(purchases.order_line.product_uom_qty, 10)
        self.assertEquals(product_buy_mto.qty_available, 99)
        sale = self.create_sale(product_buy_mto, 10, warehouse2)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(picking.location_id, warehouse2.lot_stock_id)
        self.assertEquals(picking.location_dest_id, self.customer_loc)
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
            ('state', '=', 'draft'),
        ])
        self.assertEquals(len(purchases), 1)
        self.assertEquals(purchases.order_line.product_uom_qty, 10)
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
            ('state', '=', 'draft'),
        ])
        self.assertEquals(len(purchases), 1)
        self.assertEquals(purchases.order_line.product_uom_qty, 10)

    def test_mts_mto_and_buy_route_mts_only_multiwarehouse(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'stock_mts_mto_rule'),
        ])
        if module.state != 'installed':
            self.skipTest('stock_mts_mto_rule not installed, ignore test.')
        warehouse2 = self.env['stock.warehouse'].create({
            'code': 'WH2',
            'name': 'Warehouse 2',
        })
        warehouse2.mto_mts_management = True
        product_mts_mto = self.env['product.product'].create({
            'name': 'Test product mts+mto',
            'type': 'product',
            'company_id': self.company.id,
            'route_ids': [(6, 0, [self.mts_mto_route.id, self.buy_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'delay': 1,
                'price': 5,
            })],
        })
        self.create_orderpoint(warehouse2, product_mts_mto)
        self.update_qty_on_hand(product_mts_mto, warehouse2.lot_stock_id, 100)
        sale = self.create_sale(product_mts_mto, 10, warehouse2)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(picking.picking_type_id, warehouse2.out_type_id)
        self.assertEquals(picking.location_id, warehouse2.lot_stock_id)
        self.assertEquals(picking.location_dest_id, self.customer_loc)
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.move_lines.product_uom_qty, 10)
        self.picking_transfer(picking, qty=10)
        purchase = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
        ])
        self.assertEquals(len(purchase), 0)
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEquals(len(purchases), 0)

    def test_mts_mto_and_buy_route_mto_only_duplicate_qty_multiwarehouse(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'stock_mts_mto_rule'),
        ])
        if module.state != 'installed':
            self.skipTest('stock_mts_mto_rule not installed, ignore test.')
        warehouse2 = self.env['stock.warehouse'].create({
            'code': 'WH2',
            'name': 'Warehouse 2',
        })
        warehouse2.mto_mts_management = True
        product_mts_mto = self.env['product.product'].create({
            'name': 'Test product mts+mto',
            'type': 'product',
            'company_id': self.company.id,
            'route_ids': [(6, 0, [self.mts_mto_route.id, self.buy_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'delay': 1,
                'price': 5,
            })],
        })
        self.create_orderpoint(warehouse2, product_mts_mto, 3)
        sale = self.create_sale(product_mts_mto, 10, warehouse2)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(picking.state, 'waiting')
        self.assertEquals(picking.picking_type_id, warehouse2.out_type_id)
        self.assertEquals(picking.location_id, warehouse2.lot_stock_id)
        self.assertEquals(picking.location_dest_id, self.customer_loc)
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.move_lines.product_uom_qty, 10)
        purchase = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
        ])
        self.assertEquals(len(purchase), 1)
        self.assertEquals(purchase.state, 'draft')
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.order_line[0].product_uom_qty, 10)
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEquals(len(purchases), 1)
        self.assertEquals(purchases.order_line.product_uom_qty, 13)
        purchase.button_confirm()
        self.assertEquals(len(purchase.picking_ids), 1)
        purchase_picking = purchase.picking_ids
        self.picking_transfer(purchase_picking, qty=13)
        self.assertEquals(
            purchase_picking.picking_type_id, warehouse2.in_type_id)
        self.assertEquals(purchase_picking.location_id, self.supplier_loc)
        self.assertEquals(
            purchase_picking.location_dest_id, warehouse2.lot_stock_id)

    def test_mts_mto_and_buy_route_mto_only_multiwarehouse(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'stock_mts_mto_rule'),
        ])
        if module.state != 'installed':
            self.skipTest('stock_mts_mto_rule not installed, ignore test.')
        warehouse2 = self.env['stock.warehouse'].create({
            'code': 'WH2',
            'name': 'Warehouse 2',
        })
        warehouse2.mto_mts_management = True
        product_mts_mto = self.env['product.product'].create({
            'name': 'Product mts+mto',
            'type': 'product',
            'company_id': self.company.id,
            'route_ids': [(6, 0, [self.mts_mto_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'delay': 1,
                'price': 5,
            })],
        })
        self.create_orderpoint(warehouse2, product_mts_mto, 3)
        sale = self.create_sale(product_mts_mto, 10, warehouse2)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(picking.state, 'waiting')
        self.assertEquals(picking.picking_type_id, warehouse2.out_type_id)
        self.assertEquals(picking.location_id, warehouse2.lot_stock_id)
        self.assertEquals(picking.location_dest_id, self.customer_loc)
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.move_lines.product_uom_qty, 10)
        purchase = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
        ])
        self.assertEquals(len(purchase), 1)
        self.assertEquals(purchase.state, 'draft')
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.order_line[0].product_uom_qty, 10)
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
            ('state', '=', 'draft'),
        ])
        self.assertEquals(len(purchases), 1)
        self.assertEquals(purchases.order_line.product_uom_qty, 13)
        product_mts_mto.orderpoint_ids.product_min_qty = 5
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
            ('state', '=', 'draft'),
        ])
        self.assertEquals(len(purchases), 1)
        self.assertEquals(purchases.order_line.product_uom_qty, 15)
        product_mts_mto.orderpoint_ids.product_min_qty = 0
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
            ('state', '=', 'draft'),
        ])
        self.assertEquals(len(purchases), 1)
        self.assertEquals(purchases.order_line.product_uom_qty, 15)
        purchase.button_confirm()
        self.assertEquals(len(purchase.picking_ids), 1)
        purchase_picking = purchase.picking_ids
        self.picking_transfer(purchase_picking, qty=15)
        self.assertEquals(
            purchase_picking.picking_type_id, warehouse2.in_type_id)
        self.assertEquals(purchase_picking.location_id, self.supplier_loc)
        self.assertEquals(
            purchase_picking.location_dest_id, warehouse2.lot_stock_id)

    def test_mts_mto_and_buy_route_split_multiwarehouse(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'stock_mts_mto_rule'),
        ])
        if module.state != 'installed':
            self.skipTest('stock_mts_mto_rule not installed, ignore test.')
        warehouse2 = self.env['stock.warehouse'].create({
            'code': 'WH2',
            'name': 'Warehouse 2',
        })
        warehouse2.mto_mts_management = True
        product_mts_mto = self.env['product.product'].create({
            'name': 'Test product mts+mto',
            'type': 'product',
            'company_id': self.company.id,
            'route_ids': [(6, 0, [self.mts_mto_route.id, self.buy_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'delay': 1,
                'price': 5,
            })],
        })
        self.create_orderpoint(warehouse2, product_mts_mto)
        self.update_qty_on_hand(
            product_mts_mto, warehouse2.lot_stock_id, 7)
        sale = self.create_sale(product_mts_mto, 10, warehouse2)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        sale_picking = sale.picking_ids[0]
        self.assertEquals(sale_picking.picking_type_id, warehouse2.out_type_id)
        self.assertEquals(sale_picking.location_id, warehouse2.lot_stock_id)
        self.assertEquals(sale_picking.location_dest_id, self.customer_loc)
        self.assertEquals(len(sale_picking.move_lines), 2)
        move_qty_7 = sale_picking.move_lines.filtered(
            lambda m: m.product_uom_qty == 7)
        self.assertTrue(move_qty_7)
        move_qty_3 = sale_picking.move_lines.filtered(
            lambda m: m.product_uom_qty == 3)
        self.assertTrue(move_qty_3)
        purchase = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
        ])
        self.assertEquals(len(purchase), 1)
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.order_line.product_uom_qty, 3)
        self.assertEquals(purchase.state, 'draft')
        purchase.button_confirm()
        self.assertEquals(len(purchase.picking_ids), 1)
        purchase_picking = purchase.picking_ids
        self.picking_transfer(purchase_picking, qty=3)
        self.assertEquals(
            purchase_picking.picking_type_id, warehouse2.in_type_id)
        self.assertEquals(purchase_picking.location_id, self.supplier_loc)
        self.assertEquals(
            purchase_picking.location_dest_id, warehouse2.lot_stock_id)
        self.assertEquals(purchase_picking.location_id, self.supplier_loc)
        self.assertEquals(
            purchase_picking.location_dest_id, warehouse2.lot_stock_id)
        self.assertEquals(len(purchase_picking.move_lines), 1)
        self.assertEquals(purchase_picking.move_lines.product_uom_qty, 3)
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEquals(len(purchases), 1)
