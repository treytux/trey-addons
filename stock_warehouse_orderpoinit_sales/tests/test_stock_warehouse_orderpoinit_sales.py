###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestStockWarehouseOrderpoinitSales(TransactionCase):

    def setUp(self):
        super().setUp()
        self.main_company = self.env.ref('base.main_company')
        self.new_company = self.create_new_company()
        self.new_user = self.create_user(self.main_company)
        self.new_user.company_ids = [(4, self.new_company.id)]
        self.assertIn(self.main_company, self.new_user.company_ids)
        self.assertIn(self.new_company, self.new_user.company_ids)
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product_1 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 1',
            'standard_price': 10,
            'list_price': 100,
        })
        self.warehouse_company1 = self.env['stock.warehouse'].search(
            []).filtered(lambda wh: wh.company_id.id == self.main_company.id)
        self.assertEquals(len(self.warehouse_company1), 1)

    def create_warehouse(self, user, key, company):
        return self.env['stock.warehouse'].sudo(user.id).create({
            'name': 'Warehouse %s' % key,
            'code': 'WH%s' % key,
            'company_id': company.id,
        })

    def create_new_company(self):
        return self.env['res.company'].create({
            'name': 'New test company',
        })

    def create_user(self, company):
        new_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'user@test.com',
            'company_ids': [(6, 0, [company.id])],
            'company_id': company.id,
            'groups_id': [(6, 0, [
                self.env.ref('sales_team.group_sale_salesman').id,
                self.env.ref('stock.group_stock_manager').id,
                self.env.ref('stock.group_stock_multi_warehouses').id,
            ])],
        })
        new_user.partner_id.email = new_user.login
        return new_user

    def create_orderpoint(
            self, user, warehouse, product, min_qty=0, max_qty=0):
        return self.env['stock.warehouse.orderpoint'].sudo(user.id).create({
            'name': 'OP/%s' % product.name,
            'company_id': user.company_id.id,
            'product_id': product.id,
            'warehouse_id': warehouse.id,
            'location_id': warehouse.out_type_id.default_location_src_id.id,
            'product_min_qty': min_qty,
            'product_max_qty': max_qty,
        })

    def create_sale(self, user, product, quantity, warehouse):
        sale = self.env['sale.order'].sudo(user.id).create({
            'partner_id': self.partner.id,
            'company_id': user.company_id.id,
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

    def test_orderpoint_sales(self):
        self.assertEquals(self.new_user.company_id, self.main_company)
        orderpoint = self.create_orderpoint(
            self.new_user, self.warehouse_company1, self.product_1)
        self.assertEquals(orderpoint.qty_sold, 0)
        self.assertEquals(
            orderpoint.location_id, self.warehouse_company1.lot_stock_id)
        sale = self.create_sale(
            self.new_user, self.product_1, 10, self.warehouse_company1)
        picking = sale.picking_ids
        self.assertEquals(len(picking), 1)
        self.picking_transfer(picking, 10)
        self.assertEquals(orderpoint.qty_sold, 10)
        sale = self.create_sale(
            self.new_user, self.product_1, 20, self.warehouse_company1)
        self.assertEquals(orderpoint.qty_sold, 30)

    def test_orderpoint_sales_return(self):
        self.assertEquals(self.new_user.company_id, self.main_company)
        orderpoint = self.create_orderpoint(
            self.new_user, self.warehouse_company1, self.product_1)
        self.assertEquals(orderpoint.qty_sold, 0)
        self.assertEquals(
            orderpoint.location_id, self.warehouse_company1.lot_stock_id)
        sale = self.create_sale(
            self.new_user, self.product_1, 10, self.warehouse_company1)
        picking = sale.picking_ids
        self.assertEquals(len(picking), 1)
        self.picking_transfer(picking, 10)
        self.assertEquals(orderpoint.qty_sold, 10)
        done_picking = picking.filtered(lambda p: p.state == 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=done_picking.ids,
            active_id=done_picking.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.filtered(
            lambda m: m.product_id == self.product_1).quantity = 1.0
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).quantity_done = 1
        return_pick.move_lines.filtered(
            lambda m: m.product_id == self.product_1).to_refund = True
        return_pick.action_done()
        self.assertEquals(orderpoint.qty_sold, 9)

    def test_orderpoint_change_location(self):
        self.assertEquals(self.new_user.company_id, self.main_company)
        orderpoint = self.create_orderpoint(
            self.new_user, self.warehouse_company1, self.product_1)
        self.assertEquals(orderpoint.qty_sold, 0)
        self.assertEquals(
            orderpoint.location_id, self.warehouse_company1.lot_stock_id)
        sale = self.create_sale(
            self.new_user, self.product_1, 10, self.warehouse_company1)
        picking = sale.picking_ids
        self.assertEquals(len(picking), 1)
        self.picking_transfer(picking, 10)
        self.assertEquals(orderpoint.qty_sold, 10)
        sale = self.create_sale(
            self.new_user, self.product_1, 20, self.warehouse_company1)
        self.assertEquals(orderpoint.qty_sold, 30)
        new_location = self.env['stock.location'].create({
            'name': 'Location test',
            'location_id': (
                self.warehouse_company1.lot_stock_id.location_id.id),
        })
        orderpoint.location_id = new_location.id
        self.assertEquals(orderpoint.qty_sold, 0)

    def tests_orderpoint_multicompany(self):
        self.assertEquals(self.new_user.company_id, self.main_company)
        orderpoint_company1 = self.create_orderpoint(
            self.new_user, self.warehouse_company1, self.product_1)
        self.assertEquals(orderpoint_company1.qty_sold, 0)
        self.assertEquals(
            orderpoint_company1.location_id,
            self.warehouse_company1.lot_stock_id)
        sale = self.create_sale(
            self.new_user, self.product_1, 10, self.warehouse_company1)
        picking = sale.picking_ids
        self.assertEquals(len(picking), 1)
        self.picking_transfer(picking, 10)
        self.assertEquals(orderpoint_company1.qty_sold, 10)
        self.new_user.company_id = self.new_company.id
        self.assertEquals(self.new_user.company_id, self.new_company)
        self.warehouse_company2 = self.create_warehouse(
            self.new_user, 2, self.new_company)
        self.assertEquals(len(self.warehouse_company2), 1)
        orderpoint_company2 = self.create_orderpoint(
            self.new_user, self.warehouse_company2, self.product_1)
        self.assertEquals(orderpoint_company2.qty_sold, 0)
        sale = self.create_sale(
            self.new_user, self.product_1, 10, self.warehouse_company2)
        picking = sale.picking_ids
        self.assertEquals(len(picking), 1)
        self.picking_transfer(picking, 99)
        self.assertEquals(orderpoint_company2.qty_sold, 99)

    def test_orderpoint_picking_cancel(self):
        self.assertEquals(self.new_user.company_id, self.main_company)
        orderpoint = self.create_orderpoint(
            self.new_user, self.warehouse_company1, self.product_1)
        self.assertEquals(orderpoint.qty_sold, 0)
        self.assertEquals(
            orderpoint.location_id, self.warehouse_company1.lot_stock_id)
        sale = self.create_sale(
            self.new_user, self.product_1, 10, self.warehouse_company1)
        picking = sale.picking_ids
        self.assertEquals(len(picking), 1)
        self.assertEquals(orderpoint.qty_sold, 10)
        picking.action_cancel()
        self.assertEquals(picking.state, 'cancel')
        self.assertEquals(orderpoint.qty_sold, 0)
