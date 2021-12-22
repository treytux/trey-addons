###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from calendar import monthrange
from datetime import date
from math import ceil

from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestStockWarehouseOrderpointCompute(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company1 = self.env.ref('base.main_company')
        self.company1.is_stock_rotation = True
        self.company2 = self.env['res.company'].create({
            'name': 'Company 2',
            'is_stock_rotation': True,
        })
        self.user_company1 = self.create_user('1', self.company1)
        self.user_company2 = self.create_user('2', self.company2)
        self.stock_wh = self.env.ref('stock.warehouse0')
        self.stock_wh2 = self.env['stock.warehouse'].search([
            ('company_id', '=', self.company2.id),
        ])
        self.assertEquals(len(self.stock_wh2), 1)
        self.stock_location1 = self.stock_wh.lot_stock_id
        self.stock_location2 = self.stock_wh2.lot_stock_id
        self.customer_loc = self.env.ref(
            'stock.stock_location_locations_partner')
        self.buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        self.customer1 = self.env['res.partner'].create({
            'name': 'Test customer 1',
            'customer': True,
            'company_id': False,
        })
        self.customer2 = self.env['res.partner'].create({
            'name': 'Test customer 2',
            'customer': True,
            'company_id': self.company2.id,
        })
        self.supplier1 = self.env['res.partner'].create({
            'name': 'Test supplier 1',
            'supplier': True,
            'factor_min_stock': 1.50,
            'factor_max_stock': 1.20,
            'company_id': False,
        })
        self.supplier2 = self.env['res.partner'].create({
            'name': 'Test supplier 2',
            'supplier': True,
            'factor_min_stock': 1.50,
            'factor_max_stock': 1.20,
            'company_id': self.company2.id,
        })
        self.categ_1 = self.env['product.category'].create({
            'name': 'Categ 1',
        })
        self.product1 = self.env['product.product'].create({
            'name': 'Test product 1',
            'type': 'product',
            'standard_price': 10,
            'list_price': 100,
            'route_ids': [(6, 0, [self.buy_route.id])],
            'categ_id': self.categ_1.id,
            'seller_ids': [(0, 0, {
                'name': self.supplier1.id,
                'delay': 1,
            })],
            'company_id': False,
        })
        self.assertEquals(len(self.product1.seller_ids), 1)
        self.product2 = self.env['product.product'].create({
            'name': 'Test product 2',
            'type': 'product',
            'standard_price': 10,
            'list_price': 100,
            'route_ids': [(6, 0, [self.buy_route.id])],
            'categ_id': self.categ_1.id,
            'seller_ids': [(0, 0, {
                'name': self.supplier2.id,
                'delay': 1,
            })],
            'company_id': self.company2.id,
        })
        self.assertEquals(len(self.product2.seller_ids), 1)
        self.orderpoint1 = self.create_orderpoint(
            self.user_company1, 'Orderpoint 1', self.product1, self.stock_wh)
        self.orderpoint2 = self.create_orderpoint(
            self.user_company2, 'Orderpoint 2', self.product2, self.stock_wh2)
        self.today = fields.Date.today()
        self.days_of_month = monthrange(
            self.today.year, self.today.month)[1]
        self.company1.rotation_init_date = date(
            self.today.year, self.today.month, 1)
        self.company2.rotation_init_date = date(
            self.today.year, self.today.month, 1)
        self.date_init = date(
            self.today.year, self.today.month, 1)
        self.date_end = date(
            self.today.year, self.today.month, self.days_of_month)

    def create_user(self, key, company):
        user = self.env['res.users'].create({
            'name': 'User %s' % key,
            'login': 'user%s@test.com' % key,
            'company_ids': [(6, 0, [company.id])],
            'company_id': company.id,
            'groups_id': [(6, 0, [
                self.env.ref('stock.group_stock_manager').id,
                self.env.ref('stock.group_stock_multi_warehouses').id,
                self.env.ref('purchase.group_purchase_user').id,
                self.env.ref('sales_team.group_sale_salesman').id,
            ])],
        })
        user.partner_id.email = user.login
        return user

    def create_warehouse(self, key, company):
        return self.env['stock.warehouse'].create({
            'name': 'Warehouse %s' % key,
            'code': 'WH%s' % key,
            'company_id': company.id,
        })

    def create_orderpoint(self, user, key, product, warehouse):
        return self.env['stock.warehouse.orderpoint'].sudo(user.id).create({
            'name': 'Orderpoint %s' % key,
            'product_id': product.id,
            'warehouse_id': warehouse.id,
            'location_id': warehouse.out_type_id.default_location_src_id.id,
            'product_min_qty': 5,
            'product_max_qty': 20,
            'company_id': user.company_id.id,
        })

    def create_sale_order(self, user, partner, product, qty):
        sale = self.env['sale.order'].sudo(user.id).create({
            'partner_id': partner.id,
            'partner_invoice_id': partner.id,
            'partner_shipping_id': partner.id,
            'pricelist_id': self.env.ref('product.list0').id,
        })
        sale.onchange_partner_id()
        vline = self.env['sale.order.line'].new({
            'order_id': sale.id,
            'name': product.name,
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': product.uom_id.id,
            'price_unit': product.list_price,
        })
        vline.product_id_change()
        self.env['sale.order.line'].sudo(user.id).create(
            vline._convert_to_write(vline._cache))
        return sale

    def create_purchase_order(self, user, partner, product, qty):
        purchase = self.env['purchase.order'].sudo(user.id).create({
            'partner_id': partner.id,
        })
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': purchase.id,
            'product_id': product.id,
            'price_unit': product.list_price,
            'quantity': qty,
        })
        line.onchange_product_id()
        line_obj.sudo(user.id).create(line_obj._convert_to_write(line._cache))
        return purchase

    def create_inventory(
            self, user, key, product, warehouse, qty, force_datetime=None):
        location = warehouse.out_type_id.default_location_src_id
        inventory = self.env['stock.inventory'].sudo(user.id).create({
            'name': 'Inventory %s' % key,
            'filter': 'product',
            'location_id': location.id,
            'product_id': product.id,
            'exhausted': True,
        })
        inventory.action_start()
        inventory.line_ids.sudo(user.id).write({
            'product_qty': qty,
            'location_id': location.id,
        })
        inventory._action_done()
        for move in inventory.move_ids:
            move.date = force_datetime
        return inventory

    def picking_transfer(self, picking, qty, force_datetime=None):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = qty
        picking.action_done()
        self.assertEquals(picking.state, 'done')
        if force_datetime:
            for move in picking.move_lines:
                move.date = force_datetime

    def picking_return(self, picking, qty, force_datetime=None):
        done_pickings = picking.filtered(lambda p: p.state == 'done')
        self.assertTrue(done_pickings)
        self.assertEquals(len(done_pickings.move_lines), 1)
        picking_wizard = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids, active_id=picking.id).create({})
        picking_wizard.product_return_moves.quantity = qty
        picking_wizard.product_return_moves.to_refund = True
        picking_return_action = picking_wizard.create_returns()
        picking_return = self.env['stock.picking'].browse(
            picking_return_action['res_id'])
        picking_return.move_lines[0].move_line_ids[0].qty_done = qty
        self.assertTrue(picking_return.action_done())
        self.assertEquals(picking_return.state, 'done')
        for move in picking_return.move_lines:
            move.date = force_datetime
        return picking_return

    def update_qty_on_hand(self, user, product, location, new_qty):
        wizard = self.env['stock.change.product.qty'].sudo(user.id).create({
            'product_id': product.id,
            'new_quantity': new_qty,
            'location_id': location.id,
        })
        wizard.change_product_qty()
        self.assertEquals(product.with_context(
            location=location.id).qty_available, new_qty)

    def compute_stock_rotation(
            self, date_init=None, date_end=None, company=None):
        self.env['product.product.stock.rotation'].compute_stock_rotation_day(
            init_date=date_init, end_date=date_end, company=company)

    def test_compute_qtys(self):
        quantity = (self.days_of_month * 10) + 10
        purchase = self.create_purchase_order(
            self.user_company1, self.supplier1, self.product1, quantity)
        purchase.button_confirm()
        date_picking_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+4))
        self.assertEquals(purchase.state, 'purchase')
        self.picking_transfer(
            purchase.picking_ids, quantity, force_datetime=date_picking_done)
        self.assertEquals(
            purchase.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(purchase.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity)
        sale1 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, quantity - 10)
        sale1.action_confirm()
        self.picking_transfer(
            sale1.picking_ids, quantity - 10, force_datetime=date_picking_done)
        self.assertEquals(sale1.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, 10)
        delay = self.product1.seller_ids.delay
        factor_min = self.supplier1.factor_min_stock
        factor_max = self.supplier1.factor_max_stock
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company1)
        qty_per_day, qty_min, qty_max, days, date_init, qty_out = \
            self.orderpoint1._compute_qtys(
                self.date_init, self.date_end, delay, factor_min, factor_max)
        self.assertEquals(days, self.days_of_month)
        self.assertEquals(qty_per_day, 10)
        self.assertEquals(qty_min, 10 * 1.50)
        self.assertEquals(qty_max, 10 * 1.50 * 1.20)

    def test_compute_qtys_one_day(self):
        quantity = (self.days_of_month * 10) + 10
        purchase = self.create_purchase_order(
            self.user_company1, self.supplier1, self.product1, quantity)
        purchase.button_confirm()
        self.assertEquals(purchase.state, 'purchase')
        date_picking_done = fields.Datetime.to_datetime(self.date_init)
        self.picking_transfer(
            purchase.picking_ids, quantity, force_datetime=date_picking_done)
        self.assertEquals(
            purchase.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(purchase.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity)
        sale1 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, quantity - 10)
        sale1.action_confirm()
        self.picking_transfer(
            sale1.picking_ids, quantity - 10, force_datetime=date_picking_done)
        self.assertEquals(
            sale1.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(sale1.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, 10)
        delay = self.product1.seller_ids.delay
        factor_min = self.supplier1.factor_min_stock
        factor_max = self.supplier1.factor_max_stock
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company1)
        qty_per_day, qty_min, qty_max, days, date_init, qty_out = \
            self.orderpoint1._compute_qtys(
                self.date_init, self.date_init, delay, factor_min, factor_max)
        self.assertEquals(days, 1)
        self.assertEquals(qty_per_day, quantity - 10)
        self.assertEquals(qty_min, (quantity - 10) * 1.50)
        self.assertEquals(qty_max, (quantity - 10) * 1.50 * 1.20)

    def test_compute_constraint_date(self):
        delay = self.product1.seller_ids.delay
        factor_min = self.supplier1.factor_min_stock
        factor_max = self.supplier1.factor_max_stock
        self.compute_stock_rotation(
            date_init=self.date_init, company=self.company1)
        with self.assertRaises(UserError):
            self.orderpoint1._compute_qtys(
                self.date_end, self.date_init, delay, factor_min, factor_max)

    def test_compute_qtys_without_stock_with_supplier_moves(self):
        quantity = self.days_of_month * 10
        purchase = self.create_purchase_order(
            self.user_company1, self.supplier1, self.product1, quantity)
        purchase.button_confirm()
        date_picking_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+4))
        date_picking_sale_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+6))
        self.assertEquals(purchase.state, 'purchase')
        self.picking_transfer(
            purchase.picking_ids, quantity, force_datetime=date_picking_done)
        self.assertEquals(
            purchase.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(purchase.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity)
        sale1 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, quantity + 10)
        sale1.action_confirm()
        self.picking_transfer(
            sale1.picking_ids, quantity + 10,
            force_datetime=date_picking_sale_done)
        self.assertEquals(
            sale1.picking_ids.move_lines.date, date_picking_sale_done)
        self.assertEquals(sale1.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, -10)
        delay = self.product1.seller_ids.delay
        factor_min = self.supplier1.factor_min_stock
        factor_max = self.supplier1.factor_max_stock
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company1)
        qty_per_day, qty_min, qty_max, days, date_init, qty_out = (
            self.orderpoint1._compute_qtys(
                self.date_init, self.date_end, delay, factor_min, factor_max))
        self.assertEquals(days, self.days_of_month - 4)
        self.assertEquals(qty_per_day, 12)
        self.assertEquals(qty_min, 12 * 1.50)
        self.assertEquals(qty_max, 12 * 1.50 * 1.20)

    def test_compute_qtys_without_stock_without_supplier_moves(self):
        quantity = self.days_of_month * 10
        date_picking_sale_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+6))
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, 0)
        sale1 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, quantity)
        sale1.action_confirm()
        self.picking_transfer(
            sale1.picking_ids, quantity, force_datetime=date_picking_sale_done)
        self.assertEquals(
            sale1.picking_ids.move_lines.date, date_picking_sale_done)
        self.assertEquals(sale1.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity * -1)
        delay = 10
        factor_min = self.supplier1.factor_min_stock
        factor_max = self.supplier1.factor_max_stock
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company1)
        qty_per_day, qty_min, qty_max, days, date_init, qty_out = (
            self.orderpoint1._compute_qtys(
                self.date_init, self.date_end, delay, factor_min, factor_max))
        self.assertEquals(days, self.days_of_month)
        self.assertEquals(qty_per_day, 10)
        self.assertEquals(qty_min, 10 * 1.50)
        self.assertEquals(qty_max, 10 * 1.50 * 1.20)

    def test_compute_qtys_inventory_without_stock_with_supplier_moves(self):
        quantity = (self.days_of_month * 10) + 10
        date_picking_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+4))
        date_inventory_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+5))
        date_picking_sale_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+6))
        purchase = self.create_purchase_order(
            self.user_company1, self.supplier1, self.product1, quantity)
        purchase.button_confirm()
        self.assertEquals(purchase.state, 'purchase')
        self.picking_transfer(
            purchase.picking_ids, quantity, force_datetime=date_picking_done)
        self.assertEquals(
            purchase.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(purchase.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity)
        self.inventory = self.create_inventory(
            self.user_company1, '1', self.product1, self.stock_wh, 100,
            force_datetime=date_inventory_done)
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, 100)
        sale1 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, quantity - 10)
        sale1.action_confirm()
        self.picking_transfer(
            sale1.picking_ids, quantity - 10,
            force_datetime=date_picking_sale_done)
        self.assertEquals(
            sale1.picking_ids.move_lines.date, date_picking_sale_done)
        self.assertEquals(sale1.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, 100 - (
                quantity - 10))
        delay = self.product1.seller_ids.delay
        factor_min = self.supplier1.factor_min_stock
        factor_max = self.supplier1.factor_max_stock
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company1)
        qty_per_day, qty_min, qty_max, days, date_init, qty_out = (
            self.orderpoint1._compute_qtys(
                self.date_init, self.date_end, delay, factor_min, factor_max))
        self.assertEquals(days, self.days_of_month - 4)
        self.assertEquals(qty_per_day, 12)
        self.assertEquals(qty_min, 12 * 1.50)
        self.assertEquals(qty_max, 12 * 1.50 * 1.20)

    def test_compute_qtys_inventory_without_stock_without_supplier_moves(self):
        quantity = (self.days_of_month * 10) + 10
        date_inventory_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+5))
        date_picking_sale_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+6))
        self.inventory = self.create_inventory(
            self.user_company1, '1', self.product1, self.stock_wh, 100,
            force_datetime=date_inventory_done)
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, 100)
        sale1 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, quantity - 10)
        sale1.action_confirm()
        self.picking_transfer(
            sale1.picking_ids, quantity - 10,
            force_datetime=date_picking_sale_done)
        self.assertEquals(
            sale1.picking_ids.move_lines.date, date_picking_sale_done)
        self.assertEquals(sale1.picking_ids.state, 'done')
        self.assertEquals(
            self.product1.with_context(
                location=self.stock_location1.id).qty_available,
            110 - quantity)
        delay = self.product1.seller_ids.delay
        factor_min = self.supplier1.factor_min_stock
        factor_max = self.supplier1.factor_max_stock
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company1)
        qty_per_day, qty_min, qty_max, days, date_init, qty_out = (
            self.orderpoint1._compute_qtys(
                self.date_init, self.date_end, delay, factor_min, factor_max))
        self.assertEquals(days, self.days_of_month)
        self.assertEquals(qty_per_day, 10)
        self.assertEquals(qty_min, 10 * 1.50)
        self.assertEquals(qty_max, 10 * 1.50 * 1.20)

    def test_compute_qtys_without_stock_several_purchases(self):
        date_picking_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+4))
        date_picking_done2 = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+5))
        purchase1 = self.create_purchase_order(
            self.user_company1, self.supplier1, self.product1, 100)
        purchase1.button_confirm()
        self.assertEquals(purchase1.state, 'purchase')
        self.picking_transfer(
            purchase1.picking_ids, 100, force_datetime=date_picking_done)
        self.assertEquals(
            purchase1.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(purchase1.picking_ids.state, 'done')
        purchase2 = self.create_purchase_order(
            self.user_company1, self.supplier1, self.product1, 200)
        purchase2.button_confirm()
        self.assertEquals(purchase2.state, 'purchase')
        self.picking_transfer(
            purchase2.picking_ids, 200, force_datetime=date_picking_done2)
        self.assertEquals(
            purchase2.picking_ids.move_lines.date, date_picking_done2)
        self.assertEquals(purchase2.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, 300)
        sale1 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, 310)
        sale1.action_confirm()
        self.picking_transfer(
            sale1.picking_ids, 310, force_datetime=date_picking_done)
        self.assertEquals(
            sale1.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(sale1.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, -10)
        delay = self.product1.seller_ids.delay
        factor_min = self.supplier1.factor_min_stock
        factor_max = self.supplier1.factor_max_stock
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company1)
        qty_per_day, qty_min, qty_max, days, date_init, qty_out = (
            self.orderpoint1._compute_qtys(
                self.date_init, self.date_end, delay, factor_min, factor_max))
        self.assertEquals(days, self.days_of_month - 5)
        self.assertEquals(qty_per_day, 0)
        self.assertEquals(qty_min, 0 * 1.50)
        self.assertEquals(qty_max, 0 * 1.50 * 1.20)

    def test_compute_qtys_with_stock_several_purchases(self):
        quantity = (self.days_of_month * 10)
        date_picking_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+4))
        date_picking_done2 = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+5))
        purchase1 = self.create_purchase_order(
            self.user_company1, self.supplier1, self.product1, quantity + 200)
        purchase1.button_confirm()
        self.assertEquals(purchase1.state, 'purchase')
        self.picking_transfer(
            purchase1.picking_ids, quantity + 100,
            force_datetime=date_picking_done)
        self.assertEquals(
            purchase1.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(purchase1.picking_ids.state, 'done')
        purchase2 = self.create_purchase_order(
            self.user_company1, self.supplier1, self.product1, quantity + 100)
        purchase2.button_confirm()
        self.assertEquals(purchase2.state, 'purchase')
        self.picking_transfer(
            purchase2.picking_ids, quantity + 100,
            force_datetime=date_picking_done2)
        self.assertEquals(
            purchase2.picking_ids.move_lines.date, date_picking_done2)
        self.assertEquals(purchase2.picking_ids.state, 'done')
        self.assertEquals(
            self.product1.with_context(
                location=self.stock_location1.id).qty_available,
            (quantity * 2) + 200)
        sale1 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, quantity)
        sale1.action_confirm()
        self.picking_transfer(
            sale1.picking_ids, quantity, force_datetime=date_picking_done)
        self.assertEquals(
            sale1.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(sale1.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity + 200)
        delay = self.product1.seller_ids.delay
        factor_min = self.supplier1.factor_min_stock
        factor_max = self.supplier1.factor_max_stock
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company1)
        qty_per_day, qty_min, qty_max, days, date_init, qty_out = (
            self.orderpoint1._compute_qtys(
                self.date_init, self.date_end, delay, factor_min, factor_max))
        self.assertEquals(days, self.days_of_month)
        self.assertEquals(qty_per_day, 10)
        self.assertEquals(qty_min, 10 * 1.50)
        self.assertEquals(qty_max, 10 * 1.50 * 1.20)

    def test_compute_qtys_without_stock_several_sales(self):
        quantity = (self.days_of_month * 10)
        date_picking_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+4))
        date_picking_done2 = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+5))
        purchase = self.create_purchase_order(
            self.user_company1, self.supplier1, self.product1, quantity)
        purchase.button_confirm()
        self.assertEquals(purchase.state, 'purchase')
        self.picking_transfer(
            purchase.picking_ids, quantity, force_datetime=date_picking_done)
        self.assertEquals(
            purchase.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(purchase.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity)
        sale1 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, quantity / 2)
        sale1.action_confirm()
        self.picking_transfer(sale1.picking_ids, quantity / 2,
                              force_datetime=date_picking_done)
        self.assertEquals(sale1.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(sale1.picking_ids.state, 'done')
        sale2 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1,
            (quantity / 2) + 10)
        sale2.action_confirm()
        self.picking_transfer(sale2.picking_ids, (quantity / 2) + 10,
                              force_datetime=date_picking_done2)
        self.assertEquals(
            sale2.picking_ids.move_lines.date, date_picking_done2)
        self.assertEquals(sale2.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, -10)
        delay = self.product1.seller_ids.delay
        factor_min = self.supplier1.factor_min_stock
        factor_max = self.supplier1.factor_max_stock
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company1)
        qty_per_day, qty_min, qty_max, days, date_init, qty_out = (
            self.orderpoint1._compute_qtys(
                self.date_init, self.date_end, delay, factor_min, factor_max))
        self.assertEquals(days, self.days_of_month - 4)
        self.assertEquals(qty_per_day, 12)
        self.assertEquals(qty_min, 12 * 1.50)
        self.assertEquals(qty_max, 12 * 1.50 * 1.20)

    def test_compute_qtys_with_stock_several_sales(self):
        quantity = (self.days_of_month * 10)
        date_picking_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+4))
        date_picking_done2 = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+5))
        purchase = self.create_purchase_order(
            self.user_company1, self.supplier1, self.product1, quantity + 100)
        purchase.button_confirm()
        self.assertEquals(purchase.state, 'purchase')
        self.picking_transfer(
            purchase.picking_ids, quantity + 100,
            force_datetime=date_picking_done)
        self.assertEquals(
            purchase.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(purchase.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity + 100)
        sale1 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, quantity - 10)
        sale1.action_confirm()
        self.picking_transfer(
            sale1.picking_ids, quantity, force_datetime=date_picking_done)
        self.assertEquals(
            sale1.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(sale1.picking_ids.state, 'done')
        sale2 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, 10)
        sale2.action_confirm()
        self.picking_transfer(
            sale2.picking_ids, 10, force_datetime=date_picking_done2)
        self.assertEquals(
            sale2.picking_ids.move_lines.date, date_picking_done2)
        self.assertEquals(sale2.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, 90)
        delay = self.product1.seller_ids.delay
        factor_min = self.supplier1.factor_min_stock
        factor_max = self.supplier1.factor_max_stock
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company1)
        qty_per_day, qty_min, qty_max, days, date_init, qty_out = (
            self.orderpoint1._compute_qtys(
                self.date_init, self.date_end, delay, factor_min, factor_max))
        self.assertEquals(days, self.days_of_month)
        factor_qty_days = ceil(quantity / self.days_of_month + 1)
        self.assertEquals(qty_per_day, factor_qty_days)
        self.assertEquals(qty_min, factor_qty_days * 1.50)
        self.assertEquals(qty_max, factor_qty_days * 1.50 * 1.20)

    def test_compute_qtys_partial_return_sale(self):
        quantity = (self.days_of_month * 10)
        date_picking_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+4))
        date_picking_sale_return = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+5))
        purchase = self.create_purchase_order(
            self.user_company1, self.supplier1, self.product1, quantity + 10)
        purchase.button_confirm()
        self.assertEquals(purchase.state, 'purchase')
        self.picking_transfer(
            purchase.picking_ids, quantity + 10,
            force_datetime=date_picking_done)
        self.assertEquals(
            purchase.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(purchase.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity + 10)
        sale1 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, quantity)
        sale1.action_confirm()
        self.picking_transfer(
            sale1.picking_ids, quantity, force_datetime=date_picking_done)
        self.assertEquals(
            sale1.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(sale1.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, 10)
        self.picking_return(
            sale1.picking_ids, 100, force_datetime=date_picking_sale_return)
        self.assertEquals(len(sale1.picking_ids), 2)
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, 110)
        delay = self.product1.seller_ids.delay
        factor_min = self.supplier1.factor_min_stock
        factor_max = self.supplier1.factor_max_stock
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company1)
        qty_per_day, qty_min, qty_max, days, date_init, qty_out = (
            self.orderpoint1._compute_qtys(
                self.date_init, self.date_end, delay, factor_min, factor_max))
        self.assertEquals(days, self.days_of_month)
        factor_qty_days = ceil((quantity - 100) / (self.days_of_month + 1))
        self.assertEquals(qty_per_day, factor_qty_days)
        self.assertEquals(qty_min, factor_qty_days * 1.50)
        self.assertEquals(qty_max, factor_qty_days * 1.50 * 1.20)

    def test_compute_qtys_partial_return_purchase_with_stock(self):
        quantity = (self.days_of_month * 10)
        date_picking_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+4))
        date_picking_purchase_return = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+5))
        purchase = self.create_purchase_order(
            self.user_company1, self.supplier1, self.product1, quantity + 10)
        purchase.button_confirm()
        self.assertEquals(purchase.state, 'purchase')
        self.picking_transfer(
            purchase.picking_ids, quantity + 10,
            force_datetime=date_picking_done)
        self.assertEquals(
            purchase.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(purchase.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity + 10)
        self.picking_return(
            purchase.picking_ids, 5,
            force_datetime=date_picking_purchase_return)
        self.assertEquals(len(purchase.picking_ids), 2)
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity + 5)
        sale = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, quantity)
        sale.action_confirm()
        self.picking_transfer(
            sale.picking_ids, quantity,
            force_datetime=date_picking_purchase_return)
        self.assertEquals(
            sale.picking_ids.move_lines.date, date_picking_purchase_return)
        self.assertEquals(sale.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, 5)
        delay = self.product1.seller_ids.delay
        factor_min = self.supplier1.factor_min_stock
        factor_max = self.supplier1.factor_max_stock
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company1)
        qty_per_day, qty_min, qty_max, days, date_init, qty_out = (
            self.orderpoint1._compute_qtys(
                self.date_init, self.date_end, delay, factor_min, factor_max))
        self.assertEquals(days, self.days_of_month)
        factor_qty_days = ceil(quantity / (self.days_of_month + 1))
        self.assertEquals(qty_per_day, factor_qty_days)
        self.assertEquals(qty_min, factor_qty_days * 1.50)
        self.assertEquals(qty_max, factor_qty_days * 1.50 * 1.20)

    def test_compute_qtys_partial_return_purchase_without_stock(self):
        quantity = (self.days_of_month * 10)
        date_picking_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+4))
        date_picking_purchase_return = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+5))
        purchase = self.create_purchase_order(
            self.user_company1, self.supplier1, self.product1, quantity + 10)
        purchase.button_confirm()
        self.assertEquals(purchase.state, 'purchase')
        self.picking_transfer(
            purchase.picking_ids, quantity + 10,
            force_datetime=date_picking_done)
        self.assertEquals(
            purchase.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(purchase.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity + 10)
        self.picking_return(
            purchase.picking_ids, 20,
            force_datetime=date_picking_purchase_return)
        self.assertEquals(len(purchase.picking_ids), 2)
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity - 10)
        sale = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, quantity)
        sale.action_confirm()
        self.picking_transfer(sale.picking_ids, quantity,
                              force_datetime=date_picking_purchase_return)
        self.assertEquals(
            sale.picking_ids.move_lines.date, date_picking_purchase_return)
        self.assertEquals(sale.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, -10)
        delay = self.product1.seller_ids.delay
        factor_min = self.supplier1.factor_min_stock
        factor_max = self.supplier1.factor_max_stock
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company1)
        qty_per_day, qty_min, qty_max, days, date_init, qty_out = (
            self.orderpoint1._compute_qtys(
                self.date_init, self.date_end, delay, factor_min, factor_max))
        self.assertEquals(days, self.days_of_month - 5)
        factor_qty_days = ceil(quantity / ((self.days_of_month - 5) + 1))
        self.assertEquals(qty_per_day, factor_qty_days)
        self.assertEquals(qty_min, factor_qty_days * 1.50)
        self.assertEquals(qty_max, factor_qty_days * 1.50 * 1.20)

    def test_check_schedule_compute_stock(self):
        quantity = (self.days_of_month * 10)
        date_picking_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+4))
        purchase = self.create_purchase_order(
            self.user_company1, self.supplier1, self.product1, quantity + 10)
        purchase.button_confirm()
        self.assertEquals(purchase.state, 'purchase')
        self.picking_transfer(purchase.picking_ids, quantity + 10,
                              force_datetime=date_picking_done)
        self.assertEquals(
            purchase.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(purchase.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity + 10)
        sale1 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, 5)
        sale1.action_confirm()
        self.picking_transfer(
            sale1.picking_ids, 5, force_datetime=date_picking_done)
        self.assertEquals(
            sale1.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(sale1.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity + 5)
        sale2 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, quantity)
        sale2.action_confirm()
        self.picking_transfer(
            sale2.picking_ids, quantity, force_datetime=date_picking_done)
        self.assertEquals(sale2.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(sale2.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, 5)
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company1)
        self.env['stock.warehouse.orderpoint'].sudo(
            self.user_company1.id).schedule_compute_stock()
        self.assertEquals(self.orderpoint1.product_min_qty, 15)
        self.assertEquals(self.orderpoint1.product_max_qty, 18)

    def test_check_schedule_compute_stock_product_without_seller_ids(self):
        quantity = (self.days_of_month * 10)
        date_picking_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+5))
        self.product1.seller_ids = [(6, 0, [])]
        self.assertFalse(self.product1.seller_ids)
        purchase = self.create_purchase_order(
            self.user_company1, self.supplier1, self.product1, quantity + 10)
        purchase.button_confirm()
        self.assertEquals(purchase.state, 'purchase')
        self.picking_transfer(purchase.picking_ids, quantity + 10,
                              force_datetime=date_picking_done)
        self.assertEquals(
            purchase.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(purchase.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity + 10)
        sale1 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, 5)
        sale1.action_confirm()
        self.picking_transfer(
            sale1.picking_ids, 5, force_datetime=date_picking_done)
        self.assertEquals(
            sale1.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(sale1.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity + 5)
        sale2 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, quantity)
        sale2.action_confirm()
        self.picking_transfer(
            sale2.picking_ids, quantity, force_datetime=date_picking_done)
        self.assertEquals(sale2.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(sale2.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, 5)
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company1)
        self.env['stock.warehouse.orderpoint'].sudo().schedule_compute_stock()
        self.assertEquals(self.orderpoint1.product_min_qty, 15.00)
        self.assertEquals(self.orderpoint1.product_max_qty, 18.00)

    def test_check_constraint_company(self):
        with self.assertRaises(ValidationError):
            self.company1.stock_delay = 0
        with self.assertRaises(ValidationError):
            self.company1.stock_period = 0

    def test_onchange_name_supplierinfo(self):
        self.product1.seller_ids = [(6, 0, [])]
        self.assertFalse(self.product1.seller_ids)
        product_suppplierinfo = self.env['product.supplierinfo'].new({
            'product_tmpl_id': self.product1.product_tmpl_id.id,
            'name': self.supplier1.id,
            'delay': 10,
        })
        product_suppplierinfo.onchange_name()
        self.assertEquals(product_suppplierinfo.delay, 7)

    def test_qty_multiple_no_modify_calculation(self):
        quantity = (self.days_of_month * 10)
        date_picking_done = fields.Datetime.to_datetime(self.date_init)
        date_picking_done2 = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+5))
        self.orderpoint1.qty_multiple = 100
        purchase = self.create_purchase_order(
            self.user_company1, self.supplier1, self.product1, quantity + 10)
        purchase.button_confirm()
        self.assertEquals(purchase.state, 'purchase')
        self.picking_transfer(
            purchase.picking_ids, quantity + 10, date_picking_done2)
        self.assertEquals(
            purchase.picking_ids.move_lines.date, date_picking_done2)
        self.assertEquals(purchase.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity + 10)
        sale1 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, quantity)
        sale1.action_confirm()
        self.picking_transfer(
            sale1.picking_ids, quantity, force_datetime=date_picking_done)
        self.assertEquals(
            sale1.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(sale1.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, 10)
        delay = self.product1.seller_ids.delay
        factor_min = self.supplier1.factor_min_stock
        factor_max = self.supplier1.factor_max_stock
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company1)
        qty_per_day, qty_min, qty_max, days, date_init, qty_out = (
            self.orderpoint1._compute_qtys(
                self.date_init, self.date_end, delay, factor_min, factor_max))
        self.assertEquals(days, self.days_of_month)
        factor_qty_days = ceil(quantity / (self.days_of_month + 1))
        self.assertEquals(qty_per_day, factor_qty_days)
        self.assertEquals(qty_min, factor_qty_days * 1.50)
    #     self.assertEquals(qty_max, factor_qty_days * 1.50 * 1.20)

    def test_check_schedule_compute_stock_company2(self):
        quantity = (self.days_of_month * 10)
        date_picking_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+4))
        purchase = self.create_purchase_order(
            self.user_company2, self.supplier2, self.product2, quantity + 10)
        purchase.button_confirm()
        self.assertEquals(purchase.state, 'purchase')
        self.picking_transfer(purchase.picking_ids, quantity + 10,
                              force_datetime=date_picking_done)
        self.assertEquals(
            purchase.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(purchase.picking_ids.state, 'done')
        self.assertEquals(self.product2.with_context(
            location=self.stock_location2.id).qty_available, quantity + 10)
        sale1 = self.create_sale_order(
            self.user_company2, self.customer2, self.product2, 5)
        sale1.action_confirm()
        self.picking_transfer(
            sale1.picking_ids, 5, force_datetime=date_picking_done)
        self.assertEquals(
            sale1.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(sale1.picking_ids.state, 'done')
        self.assertEquals(self.product2.with_context(
            location=self.stock_location2.id).qty_available, quantity + 5)
        sale2 = self.create_sale_order(
            self.user_company2, self.customer2, self.product2, quantity)
        sale2.action_confirm()
        self.picking_transfer(sale2.picking_ids, quantity,
                              force_datetime=date_picking_done)
        self.assertEquals(
            sale2.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(sale2.picking_ids.state, 'done')
        self.assertEquals(self.product2.with_context(
            location=self.stock_location2.id).qty_available, 5)
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company2)
        self.env['stock.warehouse.orderpoint'].sudo(
            self.user_company2.id).schedule_compute_stock()
        self.assertEquals(self.orderpoint2.product_min_qty, 15)
        self.assertEquals(self.orderpoint2.product_max_qty, 18)

    def test_check_schedule_compute_stock_with_stock_several_companies(self):
        quantity = (self.days_of_month * 10)
        date_picking_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+4))
        purchase_company1 = self.create_purchase_order(
            self.user_company1, self.supplier1, self.product1, quantity + 10)
        purchase_company1.button_confirm()
        self.assertEquals(purchase_company1.state, 'purchase')
        self.picking_transfer(
            purchase_company1.picking_ids, quantity + 10,
            force_datetime=date_picking_done)
        self.assertEquals(
            purchase_company1.picking_ids.move_lines.date,
            date_picking_done)
        self.assertEquals(purchase_company1.picking_ids.state, 'done')
        purchase_company2 = self.create_purchase_order(
            self.user_company2, self.supplier2, self.product2, quantity * 2)
        purchase_company2.button_confirm()
        self.assertEquals(purchase_company2.state, 'purchase')
        self.picking_transfer(
            purchase_company2.picking_ids, quantity * 2,
            force_datetime=date_picking_done)
        self.assertEquals(
            purchase_company2.picking_ids.move_lines.date,
            date_picking_done)
        self.assertEquals(purchase_company2.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity + 10)
        self.assertEquals(self.product2.with_context(
            location=self.stock_location2.id).qty_available, quantity * 2)
        sale_company1 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, 5)
        sale_company1.action_confirm()
        self.picking_transfer(
            sale_company1.picking_ids, 5, force_datetime=date_picking_done)
        self.assertEquals(
            sale_company1.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(sale_company1.picking_ids.state, 'done')
        sale_company2 = self.create_sale_order(
            self.user_company2, self.customer2, self.product2, quantity)
        sale_company2.action_confirm()
        self.picking_transfer(sale_company2.picking_ids, quantity,
                              force_datetime=date_picking_done)
        self.assertEquals(
            sale_company2.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(sale_company2.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, quantity + 5)
        self.assertEquals(self.product2.with_context(
            location=self.stock_location2.id).qty_available, quantity)
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company2)
        self.env['stock.warehouse.orderpoint'].sudo(
            self.user_company2.id).schedule_compute_stock()
        self.assertEquals(self.orderpoint2.product_min_qty, 15)
        self.assertEquals(self.orderpoint2.product_max_qty, 18)
        self.assertEquals(self.orderpoint1.product_min_qty, 5)
        self.assertEquals(self.orderpoint1.product_max_qty, 20)
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company1)
        self.env['stock.warehouse.orderpoint'].sudo(
            self.user_company1.id).schedule_compute_stock()
        self.assertEquals(self.orderpoint1.product_min_qty, 1.5)
        self.assertEquals(self.orderpoint1.product_max_qty, 1.8)
        self.assertEquals(self.orderpoint2.product_min_qty, 15)
        self.assertEquals(self.orderpoint2.product_max_qty, 18)

    def test_check_schedule_compute_without_stock_several_companies(self):
        quantity = (self.days_of_month * 10)
        date_picking_done = fields.Datetime.to_datetime(
            self.date_init + relativedelta(days=+4))
        purchase_company1 = self.create_purchase_order(
            self.user_company1, self.supplier1, self.product1, 10)
        purchase_company1.button_confirm()
        self.assertEquals(purchase_company1.state, 'purchase')
        self.picking_transfer(
            purchase_company1.picking_ids, 10,
            force_datetime=date_picking_done)
        self.assertEquals(
            purchase_company1.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(purchase_company1.picking_ids.state, 'done')
        purchase_company2 = self.create_purchase_order(
            self.user_company2, self.supplier2, self.product2, 20)
        purchase_company2.button_confirm()
        self.assertEquals(purchase_company2.state, 'purchase')
        self.picking_transfer(
            purchase_company2.picking_ids, 20,
            force_datetime=date_picking_done)
        self.assertEquals(
            purchase_company2.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(purchase_company2.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, 10)
        self.assertEquals(self.product2.with_context(
            location=self.stock_location2.id).qty_available, 20)
        sale_company1 = self.create_sale_order(
            self.user_company1, self.customer1, self.product1, 5)
        sale_company1.action_confirm()
        self.picking_transfer(
            sale_company1.picking_ids, 5, force_datetime=date_picking_done)
        self.assertEquals(
            sale_company1.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(sale_company1.picking_ids.state, 'done')
        sale_company2 = self.create_sale_order(
            self.user_company2, self.customer2, self.product2, quantity)
        sale_company2.action_confirm()
        self.picking_transfer(
            sale_company2.picking_ids, quantity,
            force_datetime=date_picking_done)
        self.assertEquals(
            sale_company2.picking_ids.move_lines.date, date_picking_done)
        self.assertEquals(sale_company2.picking_ids.state, 'done')
        self.assertEquals(self.product1.with_context(
            location=self.stock_location1.id).qty_available, 5)
        self.assertEquals(
            self.product2.with_context(
                location=self.stock_location2.id).qty_available,
            (quantity - 20) * -1)
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company2)
        self.env['stock.warehouse.orderpoint'].sudo(
            self.user_company2.id).schedule_compute_stock()
        self.assertEquals(self.orderpoint2.product_min_qty, 75)
        self.assertEquals(self.orderpoint2.product_max_qty, 90)
        self.assertEquals(self.orderpoint1.product_min_qty, 5)
        self.assertEquals(self.orderpoint1.product_max_qty, 20)
        self.compute_stock_rotation(
            date_init=self.date_init, date_end=self.date_end,
            company=self.company1)
        self.env['stock.warehouse.orderpoint'].sudo(
            self.user_company1.id).schedule_compute_stock()
        self.assertEquals(self.orderpoint1.product_min_qty, 1.5)
        self.assertEquals(self.orderpoint1.product_max_qty, 1.8)
        self.assertEquals(self.orderpoint2.product_min_qty, 75)
        self.assertEquals(self.orderpoint2.product_max_qty, 90)
