###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)


class TestOrderpointCreatePurchaseSendMail(TransactionCase):

    def setUp(self):
        super().setUp()
        self.buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        self.supplier = self.env['res.partner'].create({
            'name': 'Supplier test',
            'supplier': True,
        })
        self.company = self.env.ref('base.main_company')
        self.product1 = self.env['product.product'].create({
            'name': 'Product 1',
            'type': 'product',
            'company_id': self.company.id,
            'standard_price': 8,
            'list_price': 10,
            'route_ids': [(6, 0, [self.buy_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'delay': 1,
                'price': 200,
            })],
        })
        self.stock_wh = self.env.ref('stock.warehouse0')
        self.orderpoint1 = self.create_orderpoint(
            self.company, self.product1, self.stock_wh)
        self.company2 = self.create_company('Company 2')
        self.product2 = self.env['product.product'].create({
            'name': 'Product 2',
            'type': 'product',
            'company_id': self.company2.id,
            'standard_price': 80,
            'list_price': 100,
            'route_ids': [(6, 0, [self.buy_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'delay': 7,
                'price': 90,
            })],
        })
        warehouse_c2 = self.env['stock.warehouse'].search([
            ('company_id', '=', self.company2.id),
        ])
        self.assertEquals(len(warehouse_c2), 1)
        self.orderpoint2 = self.create_orderpoint(
            self.company2, self.product2, warehouse_c2,
            force_seq_name='OP/9999')
        self.env['ir.mail_server'].create({
            'name': 'localhost',
            'smtp_host': 'localhost',
            'smtp_user': 'email_smtp_user@test.com',
        })
        self.user1 = self.create_user('1', self.company)
        self.company.users_to_send_mail_ids = [(6, 0, self.user1.ids)]

    def create_company(self, name):
        templates = self.env['account.chart.template'].search([])
        if not templates:
            _log.warn(
                'Test skipped because there is no chart of account defined '
                'new company')
            self.skipTest('No Chart of account found')
            return
        company = self.env['res.company'].create({
            'name': name,
        })
        self.env.user.company_id = company.id
        return company

    def create_orderpoint(
            self, company, product, warehouse, force_seq_name=None):
        data = {
            'company_id': company.id,
            'product_id': product.id,
            'warehouse_id': warehouse.id,
            'location_id': (
                warehouse.out_type_id.default_location_src_id.id),
            'product_min_qty': 5,
            'product_max_qty': 20,
        }
        if force_seq_name:
            data.update({
                'name': force_seq_name,
            })
        return self.env['stock.warehouse.orderpoint'].create(data)

    def create_user(self, key, company):
        new_user = self.env['res.users'].create({
            'name': 'Test User %s' % key,
            'login': 'user%s@test.com' % key,
            'company_ids': [(6, 0, [company.id])],
            'company_id': company.id,
        })
        new_user.partner_id.email = new_user.login
        return new_user

    def create_purchase_order(self, company, product):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.supplier.id,
            'company_id': company.id,
        })
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': purchase.id,
            'product_id': product.id,
            'price_unit': 100,
            'quantity': 1
        })
        line.onchange_product_id()
        line_obj.create(line_obj._convert_to_write(line._cache))
        return purchase

    def update_qty_on_hand(self, product, location, new_qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': new_qty,
            'location_id': location.id,
        })
        wizard.change_product_qty()
        self.assertEquals(product.with_context(
            location=location.id).qty_available, new_qty)

    def test_stock_0_launch_run_procurements_send_mail_ok(self):
        self.assertEquals(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id)
        ])
        self.assertEquals(len(purchases), 1)
        purchase = purchases[0]
        self.assertEquals(len(purchase), 1)
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.order_line.product_id, self.product1)
        self.assertEquals(purchase.order_line.product_uom_qty, 20)
        mails = self.env['mail.mail'].search([
            ('body_html', 'ilike', 'Product: %Product 1%'),
            ('body_html', 'ilike', 'Quantity: %20%'),
        ])
        self.assertEquals(len(mails), 1)
        mail = mails[0]
        self.assertEquals(mail.email_from, 'email_smtp_user@test.com')
        self.assertEquals(mail.email_to, 'user1@test.com')

    def test_stock_50_launch_run_procurements(self):
        self.update_qty_on_hand(self.product1, self.stock_wh.lot_stock_id, 50)
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEquals(len(purchases), 0)
        mails = self.env['mail.mail'].search([
            ('body_html', 'ilike', 'Product: %Product 1%'),
        ])
        self.assertEquals(len(mails), 0)

    def test_create_normal_purchase_order(self):
        purchase = self.create_purchase_order(self.company, self.product1)
        self.assertTrue(purchase)
        mails = self.env['mail.mail'].search([
            ('body_html', 'ilike', 'Product: %Product 1%'),
        ])
        self.assertEquals(len(mails), 0)

    def test_no_mail_server(self):
        mail_servers = self.env['ir.mail_server'].search([])
        self.assertEquals(len(mail_servers), 1)
        mail_servers.unlink()
        mail_servers = self.env['ir.mail_server'].search([])
        self.assertFalse(mail_servers)

    def test_several_users_to_send_mail(self):
        user2 = self.create_user('2', self.company)
        self.company.users_to_send_mail_ids = [(4, user2.id)]
        self.assertEquals(len(self.company.users_to_send_mail_ids), 2)
        self.assertEquals(self.product1.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEquals(len(purchases), 1)
        purchase = purchases[0]
        self.assertEquals(len(purchase), 1)
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.order_line.product_id, self.product1)
        self.assertEquals(purchase.order_line.product_uom_qty, 20)
        mails = self.env['mail.mail'].search([
            ('body_html', 'ilike', 'Product: %Product 1%'),
            ('body_html', 'ilike', 'Quantity: %20%'),
        ])
        self.assertEquals(len(mails), 1)
        mail = mails[0]
        self.assertEquals(mail.email_from, 'email_smtp_user@test.com')
        self.assertEquals(mail.email_to, 'user1@test.com, user2@test.com')

    def test_several_users_to_send_mail_several_companies(self):
        self.assertEquals(len(self.company.users_to_send_mail_ids), 1)
        user2 = self.create_user('2', self.company2)
        self.company2.users_to_send_mail_ids = [(6, 0, user2.ids)]
        self.assertEquals(len(self.company2.users_to_send_mail_ids), 1)
        self.assertEquals(self.product2.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
            ('company_id', '=', self.company2.id),
        ])
        self.assertEquals(len(purchases), 1)
        purchase = purchases[0]
        self.assertEquals(len(purchase), 1)
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.order_line.product_id, self.product2)
        self.assertEquals(purchase.order_line.product_uom_qty, 20)
        mails = self.env['mail.mail'].search([
            ('body_html', 'ilike', 'Product: %Product 2%'),
            ('body_html', 'ilike', 'Quantity: %20%'),
        ])
        self.assertEquals(len(mails), 1)
        mail = mails[0]
        self.assertEquals(mail.email_from, 'email_smtp_user@test.com')
        self.assertEquals(mail.email_to, 'user2@test.com')
