###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json

from odoo.tests.common import HttpCase


class TestStockDepositImportJson(HttpCase):

    def setUp(self):
        super().setUp()
        type_revenue = self.env.ref('account.data_account_type_revenue')
        type_payable = self.env.ref('account.data_account_type_payable')
        self.account_70 = self.env['account.account'].create({
            'code': '70000',
            'name': '70000',
            'user_type_id': self.ref('account.data_account_type_revenue'),
        })
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
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
            'invoice_policy': 'delivery',
            'property_account_income_id': self.account_70.id,
            'default_code': 'TEST-01',
        })
        self.wh_stock = self.env.ref('stock.warehouse0')
        self.wh_stock.int_type_id.active = True
        self.stock_wh = self.env.ref('stock.warehouse0')
        self.buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        self.customer_loc = self.env.ref('stock.stock_location_customers')
        self.endpoint = '/stock_deposit/import'

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

    def update_qty_on_hand(self, product, location, new_qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': new_qty,
            'location_id': location.id,
        })
        wizard.change_product_qty()
        self.assertEqual(
            product.with_context(location=location.id).qty_available, new_qty)

    def create_json(self):
        deposit_name = 'Deposit test 1'
        deposits_view_loc = self.env['stock.location'].create({
            'name': 'Parent deposits',
            'usage': 'view',
        })
        self.stock_wh.deposit_parent_id = deposits_view_loc.id
        wizard = self.env['create.deposit'].create({
            'name': deposit_name,
            'warehouse_id': self.stock_wh.id,
        })
        wizard.action_create_deposit()
        deposit_loc = self.check_and_assign_action_create_deposit(
            deposit_name)
        self.update_qty_on_hand(self.product, self.stock_wh.lot_stock_id, 10)
        partner_deposit1, partner_deposit_ship = self.create_partner_deposit(
            deposit_name, deposit_loc)
        sale = self.create_sale_order(
            partner_deposit1, partner_deposit_ship, self.stock_wh,
            self.product, 5, price_forced=10)
        sale.action_confirm()
        picking_int = sale.picking_ids
        picking_int.move_lines.quantity_done = 5
        picking_int.action_done()
        data_json = {
            'name': 'SD123',
            'create_invoice': True,
            'shipping_partner_name': partner_deposit_ship.name,
            'price_option': 'last_price',
            'line_ids': [
                {
                    'ttype': 'sale',
                    'default_code': 'TEST-01',
                    'qty': 7,
                    'force_inventory': False,
                },
            ],
        }
        return data_json

    def test_url_accepted_stock_deposit(self):
        self.authenticate('admin', 'admin')
        self.opener.headers.update({
            'Content-type': 'application/json',
            'Accept': 'text/plain',
        })
        params = self.create_json()
        response = self.url_open(
            '/stock_deposit/import', data=json.dumps(params))
        data_json = json.loads(response.content.decode('utf-8'))
        deposits = self.env['stock.deposit'].search([
            ('id', '=', data_json['result']['result']),
        ])
        self.assertEqual(len(deposits), 1)
        self.assertEqual(deposits.price_option, 'last_price')
        self.assertEqual(deposits.line_ids.force_inventory, False)
        self.assertEqual(deposits.line_ids.ttype, 'sale')
        self.assertEqual(deposits.line_ids.qty, 7)
        self.assertEqual(deposits.line_ids.qty_finish, 5)
        self.assertEqual(deposits.line_ids.qty_theorical, 5)

    def test_error_product_not_exist(self):
        self.authenticate('admin', 'admin')
        self.opener.headers.update({
            'Content-type': 'application/json',
            'Accept': 'text/plain',
        })
        params = self.create_json()
        params['line_ids'][0]['default_code'] = 'TEST-03'
        response = self.url_open(
            '/stock_deposit/import', data=json.dumps(params))
        data_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(
            data_json['error']['data']['message'],
            'Product with code TEST-03 not exist\nNone')

    def test_error_products_with_same_code(self):
        self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
            'invoice_policy': 'delivery',
            'property_account_income_id': self.account_70.id,
            'default_code': 'TEST-01',
        })
        self.authenticate('admin', 'admin')
        self.opener.headers.update({
            'Content-type': 'application/json',
            'Accept': 'text/plain',
        })
        params = self.create_json()
        response = self.url_open(
            '/stock_deposit/import', data=json.dumps(params))
        data_json = json.loads(response.content.decode('utf-8'))
        self.assertEqual(
            data_json['error']['data']['message'],
            'Many products with same code TEST-01\nNone')

    def test_create_invoice_false(self):
        self.authenticate('admin', 'admin')
        self.opener.headers.update({
            'Content-type': 'application/json',
            'Accept': 'text/plain',
        })
        params = self.create_json()
        params['create_invoice'] = False
        response = self.url_open(
            '/stock_deposit/import', data=json.dumps(params))
        data_json = json.loads(response.content.decode('utf-8'))
        deposits = self.env['stock.deposit'].search([
            ('id', '=', data_json['result']['result']),
        ])
        self.assertEqual(len(deposits), 1)
        self.assertEqual(deposits.create_invoice, False)
        partner_deposit = self.env['res.partner'].search([
            ('name', '=', 'Test Deposit test 1 partner'),
            ('customer', '=', True),
        ])
        self.assertEqual(len(partner_deposit), 1)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'to invoice')

    def test_create_invoice_true(self):
        self.authenticate('admin', 'admin')
        self.opener.headers.update({
            'Content-type': 'application/json',
            'Accept': 'text/plain',
        })
        params = self.create_json()
        response = self.url_open(
            '/stock_deposit/import', data=json.dumps(params))
        data_json = json.loads(response.content.decode('utf-8'))
        deposits = self.env['stock.deposit'].search([
            ('id', '=', data_json['result']['result']),
        ])
        self.assertEqual(len(deposits), 1)
        self.assertEqual(deposits.create_invoice, True)
        partner_deposit = self.env['res.partner'].search([
            ('name', '=', 'Test Deposit test 1 partner'),
            ('customer', '=', True),
        ])
        self.assertEqual(len(partner_deposit), 1)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', partner_deposit.id),
        ], order='id desc', limit=1)
        self.assertTrue(new_sale)
        self.assertEqual(new_sale.state, 'sale')
        self.assertEqual(new_sale.invoice_status, 'invoiced')

    def test_price_option_real_fifo(self):
        self.authenticate('admin', 'admin')
        self.opener.headers.update({
            'Content-type': 'application/json',
            'Accept': 'text/plain',
        })
        params = self.create_json()
        params['price_option'] = 'real_fifo'
        response = self.url_open(
            '/stock_deposit/import', data=json.dumps(params))
        data_json = json.loads(response.content.decode('utf-8'))
        deposits = self.env['stock.deposit'].search([
            ('id', '=', data_json['result']['result']),
        ])
        self.assertEqual(len(deposits), 1)
        self.assertEqual(deposits.price_option, 'real_fifo')

    def test_force_inventory_true(self):
        self.authenticate('admin', 'admin')
        self.opener.headers.update({
            'Content-type': 'application/json',
            'Accept': 'text/plain',
        })
        params = self.create_json()
        params['line_ids'][0]['force_inventory'] = True
        response = self.url_open(
            '/stock_deposit/import', data=json.dumps(params))
        data_json = json.loads(response.content.decode('utf-8'))
        deposits = self.env['stock.deposit'].search([
            ('id', '=', data_json['result']['result']),
        ])
        self.assertEqual(len(deposits), 1)
        self.assertEqual(deposits.line_ids.force_inventory, True)
        self.assertEqual(deposits.line_ids.qty, 7)
        self.assertEqual(deposits.line_ids.qty_finish, 0)
        self.assertEqual(deposits.line_ids.qty_theorical, 5)
