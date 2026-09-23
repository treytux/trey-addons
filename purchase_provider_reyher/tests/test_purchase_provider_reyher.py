###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from odoo import exceptions, fields
from odoo.tests import common


class TestPurchaseProviderReyher(common.TransactionCase):

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
            'name': 'Reyher test connector',
            'supplier_id': self.supplier.id,
            'supplier_mode': 'reyher',
            'token_validity_date_reyher': (
                datetime.today() + relativedelta(years=1)),
            # For tests, please fill next information:
            # 'username_ws': '',
            # 'password_ws': '',
            # 'token_reyher': '',
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
            'product_code': '63250000030010',
            'price': 25,
        })
        self.supplierinfo_02 = self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.product_02.product_tmpl_id.id,
            'product_id': self.product_02.id,
            'name': self.supplier.id,
            'product_code': '9348100040000',
            'price': 35,
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
        if not self.connector.username_ws or not self.connector.password_ws:
            self.skipTest('Without Reyher credentials')
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

    def test_connector_reyher_purchase_01(self):
        self.check_credentials()
        purchase = self.create_purchase_order(self.product_01, self.product_02)
        action = purchase.action_simulator_purchase_reyher()
        wizard = self.env['connector.simulator.purchase'].browse(
            action['res_id'])
        wizard.action_to_step_2()
        self.assertEqual(len(wizard.lines), 2)
        messages_01 = purchase.message_ids
        wizard.action_to_step_done()
        line_01 = wizard.lines[0]
        line_02 = wizard.lines[1]
        self.assertEqual(
            purchase.order_line[0].price_unit,
            round(line_01.total_price_reyher / line_01.product_qty, 2))
        self.assertEqual(
            purchase.order_line[1].price_unit,
            round(line_02.total_price_reyher / line_02.product_qty, 2))
        self.assertEqual(len(purchase.message_ids), len(messages_01) + 1)
        self.assertIn(
            'Prices simulated with supplier connector on',
            purchase.message_ids[0].body)

    def test_connector_reyher_sale_01(self):
        self.check_credentials()
        sale = self.create_sale_order(self.product_01, self.product_02)
        action = sale.action_simulator_sale_reyher()
        wizard = self.env['connector.simulator.sale'].browse(action['res_id'])
        wizard.action_to_step_2()
        self.assertEqual(len(wizard.lines), 2)
        messages_01 = sale.message_ids
        wizard.action_to_step_done()
        self.assertEqual(len(sale.message_ids), len(messages_01) + 1)
        self.assertIn(
            'Prices simulated with supplier connector on',
            sale.message_ids[0].body)

    def test_connector_purchase_sku_unknow(self):
        self.check_credentials()
        purchase = self.create_purchase_order(
            self.product_test, self.product_02)
        action = purchase.action_simulator_purchase_reyher()
        wizard = self.env['connector.simulator.purchase'].browse(
            action['res_id'])
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.action_to_step_2()
        self.assertEqual(
            result.exception.name,
            '10: Unkown sku : %s' % self.code_unknow.zfill(15))

    def test_connector_sale_sku_unknow(self):
        self.check_credentials()
        sale = self.create_sale_order(self.product_test, self.product_02)
        action = sale.action_simulator_sale_reyher()
        wizard = self.env['connector.simulator.sale'].browse(action['res_id'])
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.action_to_step_2()
        self.assertEqual(
            result.exception.name,
            '10: Unkown sku : %s' % self.code_unknow.zfill(15))

    def test_connector_sale_no_product_related_supplier(self):
        self.check_credentials()
        product_no_supplier = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product no supplier',
            'standard_price': 10,
            'list_price': 30,
            'default_code': 'PDTESTNO',
        })
        sale = self.create_sale_order(product_no_supplier, self.product_02)
        action = sale.action_simulator_sale_reyher()
        wizard = self.env['connector.simulator.sale'].browse(action['res_id'])
        wizard.action_to_step_2()
        self.assertEqual(len(wizard.lines), 1)
        self.assertEqual(wizard.lines[0].product_id, self.product_02)
        self.assertNotEqual(wizard.lines[0].price_unit_reyher, 0)
        self.assertEqual(
            wizard.lines[0].msg_reyher, 'Rate obtained by API Reyher')

    def test_connector_purchase_no_product_related_supplier(self):
        self.check_credentials()
        product_no_supplier = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product no supplier',
            'standard_price': 10,
            'list_price': 30,
            'default_code': 'PDTESTNO',
        })
        purchase = self.create_purchase_order(
            product_no_supplier, self.product_02)
        action = purchase.action_simulator_purchase_reyher()
        wizard = self.env['connector.simulator.purchase'].browse(
            action['res_id'])
        wizard.action_to_step_2()
        self.assertEqual(len(wizard.lines), 1)
        self.assertEqual(wizard.lines[0].product_id, self.product_02)
        self.assertNotEqual(wizard.lines[0].total_price_reyher, 0)
        self.assertEqual(
            wizard.lines[0].msg_reyher, 'Rate obtained by API Reyher')

    def test_cron_reyher_update_product_prices(self):
        self.check_credentials()
        self.connector.write({
            'reyher_batch_size': 2,
            'daily_limit_reyher': 2,
        })
        product_templates = self.product_01.product_tmpl_id | (
            self.product_02.product_tmpl_id | self.product_test.product_tmpl_id)
        jobs_before = self.env['queue.job'].search_count([
            ('model_name', '=', 'product.template'),
            ('method_name', '=', 'job_reyher_update_price'),
            ('channel', '=', 'root.reyher_prices'),
        ])
        result = (
            self.env['product.template'].cron_reyher_update_product_prices([
                ('id', 'in', product_templates.ids),
            ]))
        jobs_after = self.env['queue.job'].search_count([
            ('model_name', '=', 'product.template'),
            ('method_name', '=', 'job_reyher_update_price'),
            ('channel', '=', 'root.reyher_prices'),
        ])
        self.assertTrue(result)
        self.assertEqual(jobs_after - jobs_before, 2)

    def test_cron_reyher_update_product_prices_without_products(self):
        with self.assertRaises(exceptions.ValidationError) as error:
            self.env['product.template'].cron_reyher_update_product_prices(
                domain=[('id', '=', 0)])
        self.assertEqual(
            error.exception.name, 'No products found with Reyher supplier')

    def test_job_reyher_update_price(self):
        self.check_credentials()
        self.supplierinfo_01.product_code = '632500000300100001'
        product_templates = (
            self.product_01.product_tmpl_id | self.product_02.product_tmpl_id)
        price_previous = self.supplierinfo_01.price
        product_templates.job_reyher_update_price()
        self.assertNotAlmostEquals(price_previous, self.supplierinfo_01.price)

    def test_job_reyher_update_price_mock(self):
        self.supplierinfo_01.product_code = '632500000300100001'
        self.supplierinfo_02.product_code = '934810004000000001'
        product_templates = (
            self.product_01.product_tmpl_id | self.product_02.product_tmpl_id)
        mock_path = (
            'odoo.addons.purchase_provider_reyher.models.'
            'connector_supplier.ConnectorSupplier.reyher_get_order_simulate')
        with patch(mock_path) as mock_reyher_get_order_simulate:
            mock_reyher_get_order_simulate.return_value = [{
                'StatusCode': 0,
                'Payload': {
                    'Items': [
                        {'Position': 1, 'Price': 1234},
                        {'Position': 2, 'Price': 2000},
                    ],
                },
            }]
            result = product_templates.job_reyher_update_price()
        self.assertEqual(self.supplierinfo_01.price, 12.34)
        self.assertEqual(self.supplierinfo_02.price, 20.0)
        self.assertIn('INFO: Reyher price updated for product [PD01]', result)
        self.assertIn('INFO: Reyher price updated for product [PD02]', result)
