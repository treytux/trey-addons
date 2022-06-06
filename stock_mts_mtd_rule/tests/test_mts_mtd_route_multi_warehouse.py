###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestMtsMtdRouteMultiWarehouse(TransactionCase):

    def setUp(self):
        super(TestMtsMtdRouteMultiWarehouse, self).setUp()
        self.company = self.env.ref('base.main_company')
        self.warehouse = self.env.ref('stock.warehouse0')
        self.warehouse.mts_mtd_management = True
        self.warehouse2 = self.env['stock.warehouse'].create({
            'code': 'WH2',
            'name': 'Warehouse 2',
        })
        self.warehouse2.mts_mtd_management = True
        self.stock_loc = self.warehouse2.lot_stock_id
        self.customer_loc = self.env.ref('stock.stock_location_customers')
        self.supplier_loc = self.env.ref('stock.stock_location_suppliers')
        self.picking_type_out = self.warehouse2.out_type_id
        self.picking_type_dropshipping = self.env.ref(
            'stock_dropshipping.picking_type_dropship')
        self.buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        self.mts_mtd_route = self.env.ref('stock_mts_mtd_rule.route_mts_mtd')
        self.dropshipping_route = self.env.ref(
            'stock_dropshipping.route_drop_shipping')
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
        self.product_buy = self.env['product.product'].create({
            'name': 'Test product buy',
            'type': 'product',
            'company_id': self.company.id,
            'route_ids': [(6, 0, [self.buy_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'price': 10,
            })],
        })
        self.product_dropshipping = self.env['product.product'].create({
            'name': 'Test product dropshipping',
            'type': 'product',
            'company_id': self.company.id,
            'route_ids': [(6, 0, [self.dropshipping_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'price': 10,
            })],
        })
        self.product_mts_mtd = self.env['product.product'].create({
            'name': 'Test product mts+mtd',
            'type': 'product',
            'company_id': self.company.id,
            'route_ids': [(6, 0, [self.mts_mtd_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'delay': 1,
                'price': 5,
            })],
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
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = qty
        picking.action_done()
        self.assertEquals(picking.state, 'done')

    def test_standard_mts_route(self):
        self.update_qty_on_hand(
            self.product_buy, self.warehouse2.lot_stock_id, 10)
        self.assertEquals(self.product_buy.with_context(
            location=self.warehouse2.lot_stock_id.id).qty_available, 10)
        sale = self.create_sale(self.product_buy, 1, self.warehouse2)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        self.assertEquals(picking.location_id, self.stock_loc)
        self.assertEquals(picking.location_dest_id, self.customer_loc)

    def test_standard_mtd_route(self):
        self.update_qty_on_hand(
            self.product_dropshipping, self.warehouse2.lot_stock_id, 10)
        sale = self.create_sale(self.product_dropshipping, 1, self.warehouse2)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 0)
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sale.procurement_group_id.id),
        ])
        self.assertEquals(len(purchase), 1)
        self.assertEquals(purchase.state, 'draft')
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.order_line[0].product_uom_qty, 1)
        purchase.button_confirm()
        self.assertEquals(len(purchase.picking_ids), 1)
        purchase_picking = purchase.picking_ids
        self.picking_transfer(purchase_picking, qty=1)
        self.assertEquals(
            purchase_picking.picking_type_id, self.picking_type_dropshipping)
        self.assertEquals(purchase_picking.location_id, self.supplier_loc)
        self.assertEquals(purchase_picking.location_dest_id, self.customer_loc)
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(sale.picking_ids, purchase.picking_ids)
        self.assertEquals(
            sale.order_line[0].purchase_line_ids, purchase.order_line[0])
        self.assertEqual(sale.order_line[0].qty_delivered, 1)

    def test_mts_mtd_route_split(self):
        self.update_qty_on_hand(
            self.product_mts_mtd, self.warehouse2.lot_stock_id, 7)
        sale = self.create_sale(self.product_mts_mtd, 10, self.warehouse2)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        sale_picking = sale.picking_ids[0]
        self.assertEquals(sale_picking.picking_type_id, self.picking_type_out)
        self.assertEquals(sale_picking.location_id, self.stock_loc)
        self.assertEquals(sale_picking.location_dest_id, self.customer_loc)
        self.assertEquals(len(sale_picking.move_lines), 1)
        self.assertEquals(sale_picking.move_lines.product_uom_qty, 7)
        self.picking_transfer(sale_picking, qty=7)
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sale.procurement_group_id.id),
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
            purchase_picking.picking_type_id, self.picking_type_dropshipping)
        self.assertEquals(purchase_picking.location_id, self.supplier_loc)
        self.assertEquals(purchase_picking.location_dest_id, self.customer_loc)
        self.assertEquals(purchase_picking.location_id, self.supplier_loc)
        self.assertEquals(purchase_picking.location_dest_id, self.customer_loc)
        self.assertEquals(len(purchase_picking.move_lines), 1)
        self.assertEquals(purchase_picking.move_lines.product_uom_qty, 3)
        self.assertEquals(
            sale.order_line[0].purchase_line_ids, purchase.order_line[0])
        self.assertEqual(sale.order_line[0].qty_delivered, 10)

    def test_mts_mtd_route_mts_only(self):
        self.update_qty_on_hand(
            self.product_mts_mtd, self.warehouse2.lot_stock_id, 100)
        sale = self.create_sale(self.product_mts_mtd, 10, self.warehouse2)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 1)
        sale_picking = sale.picking_ids[0]
        self.assertEquals(sale_picking.picking_type_id, self.picking_type_out)
        self.assertEquals(sale_picking.location_id, self.stock_loc)
        self.assertEquals(sale_picking.location_dest_id, self.customer_loc)
        self.assertEquals(len(sale_picking.move_lines), 1)
        self.assertEquals(sale_picking.move_lines.product_uom_qty, 10)
        self.picking_transfer(sale_picking, qty=10)
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sale.procurement_group_id.id),
        ])
        self.assertEquals(len(purchase), 0)

    def test_mts_mtd_route_mtd_only(self):
        self.update_qty_on_hand(
            self.product_mts_mtd, self.warehouse2.lot_stock_id, 0)
        sale = self.create_sale(self.product_mts_mtd, 10, self.warehouse2)
        self.assertEquals(sale.state, 'sale')
        self.assertEquals(len(sale.picking_ids), 0)
        purchase = self.env['purchase.order'].search([
            ('group_id', '=', sale.procurement_group_id.id),
        ])
        self.assertEquals(len(purchase), 1)
        self.assertEquals(purchase.state, 'draft')
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.order_line[0].product_uom_qty, 10)
        purchase.button_confirm()
        self.assertEquals(len(purchase.picking_ids), 1)
        purchase_picking = purchase.picking_ids
        self.picking_transfer(purchase_picking, qty=10)
        self.assertEquals(
            purchase_picking.picking_type_id, self.picking_type_dropshipping)
        self.assertEquals(purchase_picking.location_id, self.supplier_loc)
        self.assertEquals(purchase_picking.location_dest_id, self.customer_loc)
        self.assertEquals(len(sale.picking_ids), 1)
        self.assertEquals(sale.picking_ids, purchase.picking_ids)
        self.assertEquals(
            sale.order_line[0].purchase_line_ids, purchase.order_line[0])
        self.assertEqual(sale.order_line[0].qty_delivered, 10)

    def test_mts_mtd_rule_contrains(self):
        rule = self.env['stock.rule'].search([
            ('action', '=', 'split_procurement_mts_mtd'),
        ], limit=1)
        with self.assertRaises(exceptions.ValidationError):
            rule.mts_rule_id = False

    def test_get_all_routes_for_warehouse(self):
        self.assertTrue(self.warehouse2.mts_mtd_rule_id)
        routes = self.warehouse2._get_all_routes()
        self.assertIn(self.warehouse2.mts_mtd_rule_id.route_id, routes)
