###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
from io import BytesIO

import pandas as pd
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class testStockQuantInventoryImportExcel(TransactionCase):

    def setUp(self):
        super().setUp()
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.product_1 = self.env['product.product'].create({
            'type': 'product',
            'name': 'Product 1',
            'barcode': '001',
        })
        self.product_2 = self.env['product.product'].create({
            'type': 'product',
            'name': 'Product 2',
            'barcode': '002',
        })

    def get_stock(self, product, location):
        return product.with_context(location=location.id).qty_available

    def test_import_file(self):
        df = pd.DataFrame({
            'EAN': [self.product_1.barcode, self.product_2.barcode],
            'CANTIDAD': [1, 2],
        })
        file_content = BytesIO()
        df.to_excel(file_content, index=False, engine='openpyxl')
        file_content.seek(0)
        wizard = self.env['stock.quant.inventory_import_excel'].create({
            'location_id': self.stock_location.id,
            'file': base64.b64encode(file_content.read()),
            'filename': 'test_inventory.xlsx',
        })
        wizard.import_inventory()
        self.assertTrue(self.get_stock(self.product_1, self.stock_location), 1)
        self.assertTrue(self.get_stock(self.product_2, self.stock_location), 2)

    def test_import_file_without_quantity(self):
        df = pd.DataFrame({
            'EAN': [
                self.product_1.barcode,
                self.product_2.barcode,
                self.product_2.barcode,
            ],
        })
        file_content = BytesIO()
        df.to_excel(file_content, index=False, engine='openpyxl')
        file_content.seek(0)
        wizard = self.env['stock.quant.inventory_import_excel'].create({
            'location_id': self.stock_location.id,
            'file': base64.b64encode(file_content.read()),
            'filename': 'test_inventory.xlsx',
        })
        wizard.import_inventory()
        self.assertTrue(self.get_stock(self.product_1, self.stock_location), 1)
        self.assertTrue(self.get_stock(self.product_2, self.stock_location), 2)

    def test_import_file_product_not_found(self):
        df = pd.DataFrame({
            'EAN': [
                'NOT-EXISTS',
                self.product_1.barcode,
                self.product_2.barcode,
            ],
            'CANTIDAD': [0, 1, 2],
        })
        file_content = BytesIO()
        df.to_excel(file_content, index=False, engine='openpyxl')
        file_content.seek(0)
        wizard = self.env['stock.quant.inventory_import_excel'].create({
            'location_id': self.stock_location.id,
            'file': base64.b64encode(file_content.read()),
            'filename': 'test_inventory.xlsx',
        })
        wizard.import_inventory()
        self.assertTrue(self.get_stock(self.product_1, self.stock_location), 1)
        self.assertTrue(self.get_stock(self.product_2, self.stock_location), 2)

    def test_import_file_product_quantity_and_duplicate(self):
        df = pd.DataFrame({
            'EAN': [
                self.product_1.barcode,
                self.product_2.barcode,
                self.product_2.barcode,
                self.product_2.barcode,
            ],
            'CANTIDAD': [1, 1, False, 2],
        })
        file_content = BytesIO()
        df.to_excel(file_content, index=False, engine='openpyxl')
        file_content.seek(0)
        wizard = self.env['stock.quant.inventory_import_excel'].create({
            'location_id': self.stock_location.id,
            'file': base64.b64encode(file_content.read()),
            'filename': 'test_inventory.xlsx',
        })
        wizard.import_inventory()
        self.assertTrue(self.get_stock(self.product_1, self.stock_location), 1)
        self.assertTrue(self.get_stock(self.product_2, self.stock_location), 4)

    def test_import_file_for_update_stock(self):
        df = pd.DataFrame({
            'EAN': [self.product_1.barcode],
            'CANTIDAD': [1],
        })
        file_content = BytesIO()
        df.to_excel(file_content, index=False, engine='openpyxl')
        file_content.seek(0)
        wizard = self.env['stock.quant.inventory_import_excel'].create({
            'location_id': self.stock_location.id,
            'file': base64.b64encode(file_content.read()),
            'filename': 'test_inventory.xlsx',
        })
        wizard.import_inventory()
        self.assertTrue(self.get_stock(self.product_1, self.stock_location), 1)
        df = pd.DataFrame({
            'EAN': [self.product_1.barcode],
            'CANTIDAD': [2],
        })
        file_content = BytesIO()
        df.to_excel(file_content, index=False, engine='openpyxl')
        file_content.seek(0)
        wizard = self.env['stock.quant.inventory_import_excel'].create({
            'location_id': self.stock_location.id,
            'file': base64.b64encode(file_content.read()),
            'filename': 'test_inventory.xlsx',
        })
        wizard.import_inventory()
        self.assertTrue(self.get_stock(self.product_1, self.stock_location), 2)
        df = pd.DataFrame({
            'EAN': [self.product_1.barcode],
            'CANTIDAD': [1],
        })
        file_content = BytesIO()
        df.to_excel(file_content, index=False, engine='openpyxl')
        file_content.seek(0)
        wizard = self.env['stock.quant.inventory_import_excel'].create({
            'location_id': self.stock_location.id,
            'file': base64.b64encode(file_content.read()),
            'filename': 'test_inventory.xlsx',
        })
        wizard.import_inventory()
        self.assertTrue(self.get_stock(self.product_1, self.stock_location), 1)

    def test_test_file(self):
        df = pd.DataFrame({
            'EAN': [self.product_1.barcode, 'NOT-EXISTS'],
            'CANTIDAD': [1, 1],
        })
        file_content = BytesIO()
        df.to_excel(file_content, index=False, engine='openpyxl')
        file_content.seek(0)
        wizard = self.env['stock.quant.inventory_import_excel'].create({
            'location_id': self.stock_location.id,
            'file': base64.b64encode(file_content.read()),
            'filename': 'test_inventory.xlsx',
        })
        self.assertEqual(wizard.state, 'draft')
        wizard.action_check_file()
        self.assertEqual(len(wizard.error_ids), 1)
        wizard.action_check_file()
        self.assertEqual(len(wizard.error_ids), 1)
        self.assertEqual(wizard.state, 'error')
        wizard.action_back()
        self.assertEqual(len(wizard.error_ids), 0)
        df = pd.DataFrame({
            'EAN': [self.product_1.barcode],
            'CANTIDAD': [1],
        })
        file_content = BytesIO()
        df.to_excel(file_content, index=False, engine='openpyxl')
        file_content.seek(0)
        wizard = self.env['stock.quant.inventory_import_excel'].create({
            'location_id': self.stock_location.id,
            'file': base64.b64encode(file_content.read()),
            'filename': 'test_inventory.xlsx',
        })
        self.assertEqual(wizard.state, 'draft')
        wizard.action_check_file()
        self.assertEqual(wizard.state, 'ok')

    def test_import_file_product_quantity_zero_and_empty(self):
        df = pd.DataFrame({
            'EAN': [
                self.product_1.barcode,
                self.product_2.barcode,
            ],
            'CANTIDAD': [0, None],
        })
        file_content = BytesIO()
        df.to_excel(file_content, index=False, engine='openpyxl')
        file_content.seek(0)
        wizard = self.env['stock.quant.inventory_import_excel'].create({
            'location_id': self.stock_location.id,
            'file': base64.b64encode(file_content.read()),
            'filename': 'test_inventory.xlsx',
        })
        wizard.import_inventory()
        self.assertEqual(self.get_stock(self.product_1, self.stock_location), 0.0)
        self.assertEqual(self.get_stock(self.product_2, self.stock_location), 1.0)

    def test_import_file_product_quantity_with_char(self):
        df = pd.DataFrame({
            'EAN': [
                self.product_1.barcode,
                self.product_2.barcode,
            ],
            'CANTIDAD': [0, 'test'],
        })
        file_content = BytesIO()
        df.to_excel(file_content, index=False, engine='openpyxl')
        file_content.seek(0)
        wizard = self.env['stock.quant.inventory_import_excel'].create({
            'location_id': self.stock_location.id,
            'file': base64.b64encode(file_content.read()),
            'filename': 'test_inventory.xlsx',
        })
        with self.assertRaises(UserError) as err:
            wizard.import_inventory()
        self.assertIn('Invalid quantity in row', err.exception.args[0])
