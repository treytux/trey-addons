###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os

from odoo.tests.common import TransactionCase


class TestImportTemplateInventory(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product_01 = self.env['product.product'].create({
            'name': 'Test Product 01',
            'type': 'product',
            'default_code': 'PROD1TEST',
            'standard_price': 80,
            'list_price': 100,
        })
        self.product_02 = self.env['product.product'].create({
            'name': 'Test Product 02',
            'type': 'product',
            'default_code': 'PROD2TEST',
            'standard_price': 80,
            'list_price': 100,
        })
        self.product_03 = self.env['product.product'].create({
            'name': 'Test Product 03',
            'type': 'product',
            'default_code': 'PROD3TEST',
            'standard_price': 80,
            'list_price': 100,
        })
        self.location_stock = self.env.ref('stock.stock_location_stock')
        self.location_test_2 = self.env['stock.location'].create({
            'name': 'Test location 2',
            'usage': 'internal',
            'location_id': self.location_stock.id,
        })
        self.location_test_3 = self.env['stock.location'].create({
            'name': 'Test location 3',
            'usage': 'internal',
            'location_id': self.location_stock.id,
        })

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def get_file_name(self, fname):
        return fname.split('/')[-1:][0]

    def test_import_create_orderpoint_ok(self):
        fname = self.get_sample('sample_create_ok.xls')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_stock_orderpoint.template_orderpoint').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        stock_orderpoint_1 = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', self.product_01.id),
        ])
        self.assertEquals(len(stock_orderpoint_1), 0)
        stock_orderpoint_2 = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', self.product_02.id),
        ])
        self.assertEquals(len(stock_orderpoint_2), 0)
        stock_orderpoint_3 = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', self.product_03.id),
        ])
        self.assertEquals(len(stock_orderpoint_3), 0)
        wizard.action_import_from_simulation()
        stock_orderpoint_1 = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', self.product_01.id),
        ])
        self.assertEquals(len(stock_orderpoint_1), 1)
        self.assertEquals(stock_orderpoint_1.product_id, self.product_01)
        self.assertEquals(stock_orderpoint_1.location_id, self.location_stock)
        self.assertEquals(stock_orderpoint_1.product_min_qty, 1)
        self.assertEquals(stock_orderpoint_1.product_max_qty, 2)
        self.assertEquals(stock_orderpoint_1.qty_multiple, 3)
        self.assertEquals(stock_orderpoint_1.lead_days, 4)
        self.assertEquals(stock_orderpoint_1.lead_type, 'supplier')
        stock_orderpoint_2 = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', self.product_02.id),
        ])
        self.assertEquals(len(stock_orderpoint_2), 1)
        self.assertEquals(stock_orderpoint_2.product_id, self.product_02)
        self.assertEquals(stock_orderpoint_2.location_id, self.location_test_2)
        self.assertEquals(stock_orderpoint_2.product_min_qty, 0)
        self.assertEquals(stock_orderpoint_2.product_max_qty, 0)
        self.assertEquals(stock_orderpoint_2.qty_multiple, 0)
        self.assertEquals(stock_orderpoint_2.lead_days, 0)
        self.assertEquals(stock_orderpoint_2.lead_type, 'net')
        stock_orderpoint_3 = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', self.product_03.id),
        ])
        self.assertEquals(len(stock_orderpoint_3), 1)
        self.assertEquals(stock_orderpoint_3.product_id, self.product_03)
        self.assertEquals(stock_orderpoint_3.location_id, self.location_test_3)
        self.assertEquals(stock_orderpoint_3.product_min_qty, 0)
        self.assertEquals(stock_orderpoint_3.product_max_qty, 0)
        self.assertEquals(stock_orderpoint_3.qty_multiple, 0)
        self.assertEquals(stock_orderpoint_3.lead_days, 0)
        self.assertEquals(stock_orderpoint_3.lead_type, 'net')

    def test_import_write_orderpoint_ok(self):
        fname = self.get_sample('sample_write_ok.xls')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_stock_orderpoint.template_orderpoint').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 1)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.env['stock.warehouse.orderpoint'].create({
            'product_id': self.product_01.id,
            'location_id': self.location_stock.id,
            'product_min_qty': 12,
            'product_max_qty': 24,
            'qty_multiple': 1,
            'lead_days': 10,
            'lead_type': 'supplier',
        })
        stock_orderpoint_1 = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', self.product_01.id),
        ])
        self.assertEquals(len(stock_orderpoint_1), 1)
        self.assertEquals(stock_orderpoint_1.product_id, self.product_01)
        self.assertEquals(stock_orderpoint_1.location_id, self.location_stock)
        self.assertEquals(stock_orderpoint_1.product_min_qty, 12)
        self.assertEquals(stock_orderpoint_1.product_max_qty, 24)
        self.assertEquals(stock_orderpoint_1.qty_multiple, 1)
        self.assertEquals(stock_orderpoint_1.lead_days, 10)
        self.assertEquals(stock_orderpoint_1.lead_type, 'supplier')
        wizard.action_import_from_simulation()
        stock_orderpoint_1 = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', self.product_01.id),
        ])
        self.assertEquals(len(stock_orderpoint_1), 1)
        self.assertEquals(stock_orderpoint_1.product_id, self.product_01)
        self.assertEquals(stock_orderpoint_1.location_id, self.location_stock)
        self.assertEquals(stock_orderpoint_1.product_min_qty, 2)
        self.assertEquals(stock_orderpoint_1.product_max_qty, 3)
        self.assertEquals(stock_orderpoint_1.qty_multiple, 4)
        self.assertEquals(stock_orderpoint_1.lead_days, 5)
        self.assertEquals(stock_orderpoint_1.lead_type, 'net')

    def test_import_import_wrong_cases(self):
        fname = self.get_sample('sample_create_wrong_cases.xls')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_stock_orderpoint.template_orderpoint').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 7)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 7)
        wizard.action_import_from_simulation()
        self.assertEquals(
            '2: The location \'Wrong\' does not exist, select one of the '
            'available ones, for \'location_id\'.', wizard.line_ids[0].name)
        self.assertEquals(
            '2: The \'location_id\' field is required, you must fill it with a '
            'valid value.', wizard.line_ids[1].name)
        self.assertEquals(
            '3: No value found for \'product_id\'.', wizard.line_ids[2].name)
        self.assertEquals(
            '3: The \'product_id\' field is required, you must fill it with a '
            'valid value.', wizard.line_ids[3].name)
        self.assertEquals(
            '4: The product \'PROD3WRONG\' does not exist, select one of the '
            'available ones.', wizard.line_ids[4].name)
        self.assertEquals(
            '4: The \'product_id\' field is required, you must fill it with a '
            'valid value.', wizard.line_ids[5].name)
        self.assertEquals(
            '4: The \'lead_type\' field is required, you must fill it with a '
            'valid value.', wizard.line_ids[6].name)
        stock_orderpoint_1 = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', self.product_01.id),
        ])
        self.assertEquals(len(stock_orderpoint_1), 0)
        stock_orderpoint_2 = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', self.product_02.id),
        ])
        self.assertEquals(len(stock_orderpoint_2), 0)
        stock_orderpoint_3 = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', self.product_03.id),
        ])
        self.assertEquals(len(stock_orderpoint_3), 0)
