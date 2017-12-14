# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
# coding: utf-8
import openerp.tests


@openerp.tests.common.at_install(False)
@openerp.tests.common.post_install(True)
class TestMyAccountSAT(openerp.tests.HttpCase):

    def test_01_sat_dashboard_admin(self):
        self.phantom_js("/",
                        "openerp.Tour.run('sat_dashboard', 'test')",
                        "openerp.Tour.tours.sat_dashboard",
                        login='admin')

    # def test_01_sale_process_filters_admin(self):
    #     self.phantom_js("/",
    #                     "openerp.Tour.run('shop_test_filters', 'test')",
    #                     "openerp.Tour.tours.shop_test_filters",
    #                     login='admin')

    # def test_02_sale_process_filters_demo(self):
    #     self.phantom_js("/",
    #                     "openerp.Tour.run('shop_test_filters', 'test')",
    #                     "openerp.Tour.tours.shop_test_filters",
    #                     login='demo')

    # def test_03_sale_process_filters_portal(self):
    #     self.phantom_js("/",
    #                     "openerp.Tour.run('shop_test_filters', 'test')",
    #                     "openerp.Tour.tours.shop_test_filters",
    #                     login='portal')

    # def test_04_sale_process_filters_nouser(self):
    #     self.phantom_js("/",
    #                     "openerp.Tour.run('shop_test_filters', 'test')",
    #                     "openerp.Tour.tours.shop_test_filters")

# import openerp
# import logging
# _log = logging.getLogger(__name__)


# class TestMyAccountSAT(openerp.tests.HttpCase):
#     def setUp(self):
#         super(TestMyAccountSAT, self).setUp()
#         self.group_sat_id = self.env.ref(
#             'website_myaccount_sat.group_myaccount_sat').id
#         self.user_id = self.env['res.users'].create({
#             'name': 'Test User 1',
#             'login': 'testuser1@domain.com',
#             'new_passwd': 'a',
#             'groups_id': [(6, 0, [self.group_sat_id])]})
#         _log.info('=' * 100)
#         _log.info(self.user_id.id)
#         # wiz = self.env['change.password.wizard'].with_context(
#         #     dict(active_ids=[self.user_id.id])).create({
#         #         'new_passwd': 'a'})
#         # wiz.change_password_button()
#         _log.info('=' * 100)
#         _log.info(self.user_id.new_passwd)
#         _log.info('=' * 100)

#     def test_login(self):
#         self.authenticate('testuser1@domain.com', 'a')
#         _log.info('=' * 100)
#         _log.info(self.user_id.login, self.user_id.new_passwd)
#         _log.info('=' * 100)
#         r = self.url_open('/myaccount/sat/claims')
#         code = r.getcode()
#         _log.info(code)
#         _log.info('=' * 100)
#         self.assertIn(code, xrange(200, 300), 'Comprobación code')

    # def crawl(self, url, seen=None, msg=''):
    #     if seen == None:
    #         seen = set()

    #     url_slug = re.sub(r"[/](([^/=?&]+-)?[0-9]+)([/]|$)", '/<slug>/', url)
    #     url_slug = re.sub(r"([^/=?&]+)=[^/=?&]+", '\g<1>=param', url_slug)
    #     if url_slug in seen:
    #         return seen
    #     else:
    #         seen.add(url_slug)

    #     _logger.info("%s %s", msg, url)
    #     r = self.url_open(url)
    #     code = r.getcode()
        # self.assertIn(
        #     code, xrange(200, 300),
        #     "%s Fetching %s returned error response (%d)" % (msg, url, code))

    #     if r.info().gettype() == 'text/html':
    #         doc = lxml.html.fromstring(r.read())
    #         for link in doc.xpath('//a[@href]'):
    #             href = link.get('href')

    #             parts = urlparse.urlsplit(href)
    #             # href with any fragment removed
    #             href = urlparse.urlunsplit((
    #                 parts.scheme,
    #                 parts.netloc,
    #                 parts.path,
    #                 parts.query,
    #                 ''
    #             ))

    #             # FIXME: handle relative link (not parts.path.startswith /)
    #             if parts.netloc or \
    #                 not parts.path.startswith('/') or \
    #                 parts.path == '/web' or\
    #                 parts.path.startswith('/web/') or \
    #                 parts.path.startswith('/en_US/') or \
    #                 (parts.scheme and parts.scheme not in ('http', 'https')):
    #                 continue

    #             self.crawl(href, seen, msg)
    #     return seen

    # def test_10_crawl_public(self):
    #     t0 = time.time()
    #     t0_sql = self.registry.test_cr.sql_log_count
    #     seen = self.crawl('/', msg='Anonymous Coward')
    #     count = len(seen)
    #     duration = time.time() - t0
    #     sql = self.registry.test_cr.sql_log_count - t0_sql

    # def test_20_crawl_demo(self):
    #     t0 = time.time()
    #     t0_sql = self.registry.test_cr.sql_log_count
    #     self.authenticate('demo', 'demo')
    #     seen = self.crawl('/', msg='demo')
    #     count = len(seen)
    #     duration = time.time() - t0
    #     sql = self.registry.test_cr.sql_log_count - t0_sql

    # def test_30_crawl_admin(self):
    #     t0 = time.time()
    #     t0_sql = self.registry.test_cr.sql_log_count
    #     self.authenticate('admin', 'admin')
    #     seen = self.crawl('/', msg='admin')
    #     count = len(seen)
    #     duration = time.time() - t0
    #     sql = self.registry.test_cr.sql_log_count - t0_sql


# from openerp.tests import common
# import logging
# _log = logging.getLogger(__name__)


# class TestMyAccountSAT(common.TransactionCase):

#     def setUp(self):
#         super(TestMyAccountSAT, self).setUp()
#         self.group_sat_id = self.env.ref(
#             'website_myaccount_sat.group_myaccount_sat').id
#         self.user_id = self.env['res.users'].create({
#             'name': 'Test User 1',
#             'login': 'testuser1@domain.com',
#             'email': 'testuser1@domain.com',
#             'groups_id': [(6, 0, [self.group_sat_id])]})

#     def test_login(self):
#         env = self.env(user=self.user_id.id)
#         claims = env['website_myaccount_sat.myaccount'].claims()
#         _log.info('=' * 100)
#         _log.info(claims)
#         _log.info('=' * 100)
#         # _log.info('=' * 100)
#         # _log.info(env.user.name)
#         # _log.info('=' * 100)

#     def test_order(self):
#         pass
#         # self.partner = self.env['res.partner'].create({
#         #     'name': 'Test Partner 1'})
#         # self.product_1 = self.env['product.product'].create({
#         #     'name': 'Test Product 1'})
#         # self.product_2 = self.env['product.product'].create({
#         #     'name': 'Test Product 2'})
#         # self.order = self.env['sale.order'].create({
#         #     'partner_id': self.partner.id})
#         # self.order_line_1 = self.env['sale.order.line'].create({
#         #     'product_id': self.product_1.id,
#         #     'name': self.product_1.name,
#         #     'order_id': self.order.id})
#         # self.order_line_2 = self.env['sale.order.line'].create({
#         #     'product_id': self.product_2.id,
#         #     'name': self.product_2.name,
#         #     'order_id': self.order.id})

#         # self.product = self.env['product.product'].create({
#         #     'name': 'SILICONA DUPLICAR 6KG+CAT. MAQ.30 TECHIM'})
#         # self.picking = self.env['stock.picking'].create({
#         #     'company_id': self.env.user.company_id.id,
#         #     'picking_type_id': self.env.ref('stock.picking_type_out').id})
#         # lot = self.env['stock.production.lot'].create({
#         #     'name': 'LOT-000001',
#         #     'product_id': self.product.id})
#         # move = self.env['stock.move'].create({
#         #     'product_id': self.product.id,
#         #     'product_uom_qty': 1,
#         #     'product_uom': self.env.ref('product.product_uom_unit').id,
#         #     'name': self.product.name,
#         #     'location_dest_id': self.env.ref(
#         #         'stock.stock_location_customers').id,
#         #     'location_id': self.env.ref('stock.stock_location_stock').id,
#         #     'picking_id': self.picking.id,
#         #     'lot_ids': [(6, 0, [lot.id])]})
#         # # self.picking.action_confirm()
#         # # self.picking.action_done()
#         # self.product.ean13 = '0075678164125'
#         # self.product.default_code = 'COD-PROD-1'

#         # wiz = self.env['wiz.product.label'].with_context(
#         #     dict(active_ids=[self.picking.id])).create({
#         #         # 'report_id':
#         #         'quantity_picking': 'one'})
#         # re = wiz.button_print_from_picking()

#         # ctx = re['context']
#         # ctx.update(dict(active_id=move.id, active_ids=[move.id]))

#         # def print_report(fname):
#         #     pdf = self.env['report'].with_context(ctx).get_pdf(
#         #         move, re['report_name'], data=re['datas'])
#         #     with open(fname, 'w') as fp:
#         #         fp.write(pdf)

#         # print_report('/home/Escritorio/claim.pdf')
#         # #self.env.cr.commit()
