###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests import common


class TestPurchaseProviderComafe(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.supplier = self.env['res.partner'].create({
            'name': 'Test partner supplier',
            'is_company': False,
            'supplier': True,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': False,
        })
        self.connector = self.env['connector.supplier'].create({
            'name': 'Comafe test connector',
            'supplier_id': self.supplier.id,
            'supplier_mode': 'comafe',
            # For tests, please fill next information:
            # 'erp_user_comafe': '',
            # 'erp_password_comafe': '',
            # 'customer_code_comafe': '',
            # 'customer_office_comafe': '',
            # 'customer_key_comafe': '',
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 01',
            'standard_price': 10,
            'list_price': 30,
            'default_code': 'PD01',
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 02',
            'standard_price': 20,
            'list_price': 40,
            'default_code': 'PD02',
        })
        self.product_test = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product sku unknow',
            'standard_price': 10,
            'list_price': 30,
            'default_code': 'PDTEST',
        })
        self.supplierinfo_01 = self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.product_01.product_tmpl_id.id,
            'product_id': self.product_01.id,
            'name': self.supplier.id,
            'product_code': '129337',
            'price': 2.1,
        })
        self.supplierinfo_02 = self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.product_02.product_tmpl_id.id,
            'product_id': self.product_02.id,
            'name': self.supplier.id,
            'product_code': '106956',
            'price': 4,
        })
        self.code_unknow = '12345678909875'
        self.supplierinfo_test = self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.product_test.product_tmpl_id.id,
            'product_id': self.product_test.id,
            'name': self.supplier.id,
            'product_code': self.code_unknow,
            'price': 25,
        })

    def check_credentials(self):
        if not self.connector.erp_user_comafe or (
                not self.connector.erp_password_comafe):
            self.skipTest('Without Comafe credentials')
        return True

    def create_sale_order(self, product_01, product_02):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'name': product_01.name,
                    'product_id': product_01.id,
                    'product_uom_qty': 10,
                    'product_uom': product_01.uom_id.id,
                    'price_unit': product_01.list_price,
                }),
                (0, 0, {
                    'name': product_02.name,
                    'product_id': product_02.id,
                    'product_uom_qty': 20,
                    'product_uom': product_02.uom_id.id,
                    'price_unit': product_02.list_price,
                }),
            ],
        })

    def create_purchase_order(self, product_01, product_02):
        return self.env['purchase.order'].create({
            'partner_id': self.supplier.id,
            'order_line': [
                (0, 0, {
                    'name': product_01.name,
                    'product_id': product_01.id,
                    'product_qty': 10,
                    'date_planned': fields.Date.today(),
                    'product_uom': product_01.uom_id.id,
                    'price_unit': product_01.standard_price,
                }),
                (0, 0, {
                    'name': product_02.name,
                    'product_id': product_02.id,
                    'product_qty': 20,
                    'date_planned': fields.Date.today(),
                    'product_uom': product_02.uom_id.id,
                    'price_unit': product_02.standard_price,
                }),
            ],
        })

    def test_connector_comafe_purchase_only_stock_01(self):
        self.check_credentials()
        purchase = self.create_purchase_order(self.product_01, self.product_02)
        action = purchase.action_simulator_purchase_comafe()
        wizard = self.env['connector.simulator.purchase'].browse(
            action['res_id'])
        wizard.action_to_step_2()
        self.assertEqual(len(wizard.lines), 2)
        messages_01 = purchase.message_ids
        line_01 = wizard.lines[0]
        line_02 = wizard.lines[1]
        self.assertTrue(line_01.qty_available_comafe > 0)
        self.assertTrue(line_02.qty_available_comafe > 0)
        self.assertEqual(line_01.price_unit_comafe, 0)
        self.assertEqual(line_02.price_unit_comafe, 0)
        self.assertEqual(line_01.total_price_comafe, 0)
        self.assertEqual(line_02.total_price_comafe, 0)
        self.assertEqual(line_01.msg_comafe, 'Stock obtained by API Comafe')
        self.assertEqual(line_02.msg_comafe, 'Stock obtained by API Comafe')
        wizard.action_to_step_done()
        self.assertEqual(len(purchase.message_ids), len(messages_01) + 1)
        self.assertIn(
            'Prices updated with supplier connector',
            purchase.message_ids[0].body)

    def test_connector_comafe_purchase_stock_and_price_02(self):
        self.check_credentials()
        self.supplierinfo_01.product_code = '127837'
        self.supplierinfo_02.product_code = '127843'
        purchase = self.create_purchase_order(self.product_01, self.product_02)
        action = purchase.action_simulator_purchase_comafe()
        wizard = self.env['connector.simulator.purchase'].browse(
            action['res_id'])
        wizard.action_to_step_2()
        self.assertEqual(len(wizard.lines), 2)
        line_01 = wizard.lines[0]
        line_02 = wizard.lines[1]
        self.assertTrue(line_01.qty_available_comafe > 0)
        self.assertTrue(line_02.qty_available_comafe > 0)
        self.assertNotEqual(line_01.price_unit_comafe, 0)
        self.assertNotEqual(line_02.total_price_comafe, 0)
        self.assertEqual(
            line_01.msg_comafe, 'Rate and stock obtained by API Comafe')
        self.assertEqual(
            line_02.msg_comafe, 'Rate and stock obtained by API Comafe')

    def test_connector_comafe_purchase_all_stock_cases_03(self):
        self.check_credentials()
        product_03 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 03',
            'standard_price': 30,
            'list_price': 50,
            'default_code': 'PD03',
        })
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': product_03.product_tmpl_id.id,
            'product_id': product_03.id,
            'name': self.supplier.id,
            'product_code': '51200',
            'price': 5,
        })
        self.supplierinfo_01.product_code = '10011509'
        self.supplierinfo_02.product_code = '106087'
        purchase = self.create_purchase_order(self.product_01, self.product_02)
        purchase.order_line[0].product_qty = 1
        purchase.write({
            'order_line': [
                (0, 0, {
                    'product_id': product_03.id,
                    'name': product_03.name,
                    'product_qty': 30,
                    'price_unit': product_03.standard_price,
                    'date_planned': fields.Date.today(),
                    'product_uom': product_03.uom_id.id,
                }),
            ],
        })
        action = purchase.action_simulator_purchase_comafe()
        wizard = self.env['connector.simulator.purchase'].browse(
            action['res_id'])
        wizard.action_to_step_2()
        self.assertEqual(len(wizard.lines), 3)
        line_01 = wizard.lines[0]
        line_02 = wizard.lines[1]
        line_03 = wizard.lines[2]
        self.assertEqual(line_01.qty_available_comafe, line_01.product_qty)
        self.assertTrue(line_02.product_qty > line_02.qty_available_comafe)
        self.assertTrue(line_03.qty_available_comafe > 0)
        self.assertEqual(line_01.msg_comafe, 'Stock obtained by API Comafe')
        self.assertEqual(line_02.msg_comafe, 'Stock obtained by API Comafe')
        self.assertEqual(line_03.msg_comafe, 'Stock obtained by API Comafe')

    def test_connector_comafe_purchase_product_not_found_in_api_04(self):
        self.check_credentials()
        self.supplierinfo_02.product_code = '44992868183'
        purchase = self.create_purchase_order(self.product_01, self.product_02)
        action = purchase.action_simulator_purchase_comafe()
        wizard = self.env['connector.simulator.purchase'].browse(
            action['res_id'])
        wizard.action_to_step_2()
        self.assertEqual(len(wizard.lines), 2)
        line_01 = wizard.lines[0]
        line_02 = wizard.lines[1]
        self.assertEqual(
            line_01.msg_comafe, 'Rate and stock obtained by API Comafe')
        self.assertIn('not found in api response', line_02.msg_comafe)

    def test_connector_comafe_purchase_not_supplierinfo_05(self):
        self.check_credentials()
        self.supplierinfo_02.unlink()
        supplierinfos = self.env['product.supplierinfo'].search([
            ('product_id', '=', self.product_02.id),
        ])
        self.assertEqual(len(supplierinfos), 0)
        purchase = self.create_purchase_order(self.product_01, self.product_02)
        action = purchase.action_simulator_purchase_comafe()
        wizard = self.env['connector.simulator.purchase'].browse(
            action['res_id'])
        wizard.action_to_step_2()
        self.assertEqual(len(wizard.lines), 2)
        line_01 = wizard.lines[0]
        line_02 = wizard.lines[1]
        self.assertEqual(
            line_01.msg_comafe, 'Rate and stock obtained by API Comafe')
        self.assertEqual(
            line_02.msg_comafe, 'No supplier rate or product code found')

    def test_connector_comafe_sale_only_stock_01(self):
        self.check_credentials()
        sale = self.create_sale_order(self.product_01, self.product_02)
        action = sale.action_simulator_sale_comafe()
        wizard = self.env['connector.simulator.sale'].browse(action['res_id'])
        wizard.action_to_step_2()
        self.assertEqual(len(wizard.lines), 2)
        messages_01 = sale.message_ids
        line_01 = wizard.lines[0]
        line_02 = wizard.lines[1]
        self.assertTrue(line_01.qty_available_comafe > 0)
        self.assertTrue(line_02.qty_available_comafe > 0)
        self.assertEqual(line_01.price_unit_comafe, 0)
        self.assertEqual(line_02.price_unit_comafe, 0)
        self.assertEqual(line_01.total_price_comafe, 0)
        self.assertEqual(line_02.total_price_comafe, 0)
        self.assertEqual(line_01.msg_comafe, 'Stock obtained by API Comafe')
        self.assertEqual(line_02.msg_comafe, 'Stock obtained by API Comafe')
        wizard.action_to_step_done()
        self.assertEqual(len(sale.message_ids), len(messages_01) + 1)
        self.assertIn(
            'Prices simulated with supplier connector on',
            sale.message_ids[0].body)

    def test_connector_comafe_sale_stock_and_price_02(self):
        self.check_credentials()
        self.supplierinfo_01.product_code = '127837'
        self.supplierinfo_02.product_code = '127843'
        sale = self.create_sale_order(self.product_01, self.product_02)
        action = sale.action_simulator_sale_comafe()
        wizard = self.env['connector.simulator.sale'].browse(action['res_id'])
        wizard.action_to_step_2()
        self.assertEqual(len(wizard.lines), 2)
        line_01 = wizard.lines[0]
        line_02 = wizard.lines[1]
        self.assertTrue(line_01.qty_available_comafe > 0)
        self.assertTrue(line_02.qty_available_comafe > 0)
        self.assertNotEqual(line_01.price_unit_comafe, 0)
        self.assertNotEqual(line_02.total_price_comafe, 0)
        self.assertEqual(
            line_01.msg_comafe, 'Rate and stock obtained by API Comafe')
        self.assertEqual(
            line_02.msg_comafe, 'Rate and stock obtained by API Comafe')

    def test_connector_comafe_sale_all_stock_cases_03(self):
        self.check_credentials()
        product_03 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 03',
            'standard_price': 30,
            'list_price': 50,
            'default_code': 'PD03',
        })
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': product_03.product_tmpl_id.id,
            'product_id': product_03.id,
            'name': self.supplier.id,
            'product_code': '51200',
            'price': 5,
        })
        self.supplierinfo_01.product_code = '10011509'
        self.supplierinfo_02.product_code = '106087'
        sale = self.create_sale_order(self.product_01, self.product_02)
        sale.order_line[0].product_qty = 1
        sale.write({
            'order_line': [
                (0, 0, {
                    'product_id': product_03.id,
                    'name': product_03.name,
                    'product_uom_qty': 30,
                    'price_unit': product_03.standard_price,
                    'product_uom': product_03.uom_id.id,
                }),
            ],
        })
        action = sale.action_simulator_sale_comafe()
        wizard = self.env['connector.simulator.sale'].browse(
            action['res_id'])
        wizard.action_to_step_2()
        self.assertEqual(len(wizard.lines), 3)
        line_01 = wizard.lines[0]
        line_02 = wizard.lines[1]
        line_03 = wizard.lines[2]
        self.assertEqual(line_01.qty_available_comafe, line_01.product_qty)
        self.assertTrue(line_02.product_qty > line_02.qty_available_comafe)
        self.assertTrue(line_03.qty_available_comafe > 0)
        self.assertEqual(line_01.msg_comafe, 'Stock obtained by API Comafe')
        self.assertEqual(line_02.msg_comafe, 'Stock obtained by API Comafe')
        self.assertEqual(line_03.msg_comafe, 'Stock obtained by API Comafe')

    def test_connector_comafe_sale_product_not_found_in_api_04(self):
        self.check_credentials()
        self.supplierinfo_02.product_code = '44992868183'
        sale = self.create_sale_order(self.product_01, self.product_02)
        action = sale.action_simulator_sale_comafe()
        wizard = self.env['connector.simulator.sale'].browse(action['res_id'])
        wizard.action_to_step_2()
        self.assertEqual(len(wizard.lines), 2)
        line_01 = wizard.lines[0]
        line_02 = wizard.lines[1]
        self.assertEqual(
            line_01.msg_comafe, 'Rate and stock obtained by API Comafe')
        self.assertIn('not found in api response', line_02.msg_comafe)

    def test_connector_comafe_not_supplierinfo_05(self):
        self.check_credentials()
        self.supplierinfo_02.unlink()
        supplierinfos = self.env['product.supplierinfo'].search([
            ('product_id', '=', self.product_02.id),
        ])
        self.assertEqual(len(supplierinfos), 0)
        purchase = self.create_sale_order(self.product_01, self.product_02)
        action = purchase.action_simulator_sale_comafe()
        wizard = self.env['connector.simulator.sale'].browse(action['res_id'])
        wizard.action_to_step_2()
        self.assertEqual(len(wizard.lines), 2)
        line_01 = wizard.lines[0]
        line_02 = wizard.lines[1]
        self.assertEqual(
            line_01.msg_comafe, 'Rate and stock obtained by API Comafe')
        self.assertEqual(
            line_02.msg_comafe, 'No supplier rate or product code found')

    def test_connector_comafe_margin_sale(self):
        self.check_credentials()
        self.supplierinfo_01.product_code = '127837'
        self.supplierinfo_02.product_code = '127843'
        sale = self.create_sale_order(self.product_01, self.product_02)
        action = sale.action_simulator_sale_comafe()
        wizard = self.env['connector.simulator.sale'].browse(action['res_id'])
        wizard.action_to_step_2()
        self.assertEqual(len(wizard.lines), 2)
        line_01 = wizard.lines[0]
        line_02 = wizard.lines[1]
        margin_01 = (1 - (
            line_01.price_unit_comafe / line_01.sale_line_id.price_unit)) * 100
        margin_02 = (1 - (
            line_02.price_unit_comafe / line_02.sale_line_id.price_unit)) * 100
        self.assertEqual(line_01.margin_comafe, margin_01)
        self.assertEqual(line_02.margin_comafe, margin_02)

    def test_connector_comafe_margin_sale_discount(self):
        self.check_credentials()
        self.supplierinfo_01.product_code = '127837'
        self.supplierinfo_02.product_code = '127843'
        sale = self.create_sale_order(self.product_01, self.product_02)
        self.assertEqual(sale.order_line[0].discount, 0)
        self.assertEqual(sale.order_line[1].discount, 0)
        sale.order_line[0].discount = 10
        sale.order_line[1].discount = 20
        self.assertEqual(sale.order_line[0].discount, 10)
        self.assertEqual(sale.order_line[1].discount, 20)
        action = sale.action_simulator_sale_comafe()
        wizard = self.env['connector.simulator.sale'].browse(action['res_id'])
        wizard.action_to_step_2()
        self.assertEqual(len(wizard.lines), 2)
        line_01 = wizard.lines[0]
        line_02 = wizard.lines[1]
        price_discount_01 = line_01.sale_line_id.price_unit * (
            1 - (line_01.sale_line_id.discount / 100))
        price_discount_02 = line_02.sale_line_id.price_unit * (
            1 - (line_02.sale_line_id.discount / 100))
        margin_01 = (1 - (line_01.price_unit_comafe / price_discount_01)) * 100
        margin_02 = (1 - (line_02.price_unit_comafe / price_discount_02)) * 100
        self.assertEqual(line_01.margin_comafe, margin_01)
        self.assertEqual(line_02.margin_comafe, margin_02)

    def test_connector_comafe_margin_sale_onchange(self):
        self.check_credentials()
        self.supplierinfo_01.product_code = '127837'
        self.supplierinfo_02.product_code = '127843'
        sale = self.create_sale_order(self.product_01, self.product_02)
        action = sale.action_simulator_sale_comafe()
        wizard = self.env['connector.simulator.sale'].browse(action['res_id'])
        wizard.action_to_step_2()
        self.assertEqual(len(wizard.lines), 2)
        line_01 = wizard.lines[0]
        line_02 = wizard.lines[1]
        margin_01 = (1 - (
            line_01.price_unit_comafe / line_01.sale_line_id.price_unit)) * 100
        margin_02 = (1 - (
            line_02.price_unit_comafe / line_02.sale_line_id.price_unit)) * 100
        self.assertEqual(line_01.margin_comafe, margin_01)
        self.assertEqual(line_02.margin_comafe, margin_02)
        self.assertEqual(line_01.price_unit, sale.order_line[0].price_unit)
        self.assertEqual(line_02.price_unit, sale.order_line[1].price_unit)
        line_01.price_unit = 50
        line_02.price_unit = 60
        self.assertNotEqual(line_01.price_unit, sale.order_line[0].price_unit)
        self.assertNotEqual(line_02.price_unit, sale.order_line[1].price_unit)
        line_01._origin = line_01
        line_02._origin = line_02
        line_01.onchange_sale_line_margin()
        line_02.onchange_sale_line_margin()
        self.assertNotEqual(line_01.margin_comafe, margin_01)
        self.assertNotEqual(line_02.margin_comafe, margin_02)
