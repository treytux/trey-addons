##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase
import base64
import os


class TestStockWarehouseOrderpointImport(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product_01 = self.env['product.product'].create({
            'default_code': 'TEST1',
            'name': 'testwriterule'})
        self.product_02 = self.env['product.product'].create({
            'default_code': 'TEST2',
            'name': 'testcreaterule'})
        self.location = self.env.ref('stock.stock_location_stock')
        self.rule_01 = self.env['stock.warehouse.orderpoint'].create({
            'product_id': self.product_01.id,
            'location': self.location.id,
            'warhouse_id': self.location.get_warehouse().id,
            'product_min_qty': 10,
            'product_max_qty': 25})

    def test_import_ok(self):
        def get_path(*relative_path):
            path = '../'
            fname = os.path.join(__file__, path, *relative_path)
            return os.path.abspath(fname)

        file_name = 'test_file_ok.xlsx'
        path = get_path(file_name)
        ffile = open(path, 'rb').read()
        wiz = self.env['wizard.stock.warehouse.orderpoint.import'].create({
            'location_id': self.location.id,
            'data_file': base64.encodestring(ffile)})
        wiz.action_import()
        rule_02 = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', self.product_02.id)])
        self.assertEquals(int(self.rule_01.product_min_qty), 111)
        self.assertEquals(int(self.rule_01.product_max_qty), 222)
        self.assertEquals(int(rule_02.product_min_qty), 33)
        self.assertEquals(int(rule_02.product_max_qty), 44)
        self.assertEquals(int(wiz.rows_imported), 2)
        wiz.unlink()

    def test_error_values(self):
        def get_path(*relative_path):
            path = '../'
            fname = os.path.join(__file__, path, *relative_path)
            return os.path.abspath(fname)

        file_name = 'test_file_error_values.xlsx'
        path = get_path(file_name)
        ffile = open(path, 'rb').read()
        wiz = self.env['wizard.stock.warehouse.orderpoint.import'].create({
            'location_id': self.location.id,
            'data_file': base64.encodestring(ffile)})
        self.assertRaises(UserError, wiz.action_import)

    def test_empty_required_column(self):
        def get_path(*relative_path):
            path = '../'
            fname = os.path.join(__file__, path, *relative_path)
            return os.path.abspath(fname)

        file_name = 'test_file_empty_colum.xlsx'
        path = get_path(file_name)
        ffile = open(path, 'rb').read()
        wiz = self.env['wizard.stock.warehouse.orderpoint.import'].create({
            'location_id': self.location.id,
            'data_file': base64.encodestring(ffile)})
        self.assertRaises(UserError, wiz.action_import)

    def test_empty_file(self):
        def get_path(*relative_path):
            path = '../'
            fname = os.path.join(__file__, path, *relative_path)
            return os.path.abspath(fname)

        file_name = 'test_file_empty_file.xlsx'
        path = get_path(file_name)
        ffile = open(path, 'rb').read()
        wiz = self.env['wizard.stock.warehouse.orderpoint.import'].create({
            'location_id': self.location.id,
            'data_file': base64.encodestring(ffile)})
        self.assertRaises(ValidationError, wiz.action_import)
