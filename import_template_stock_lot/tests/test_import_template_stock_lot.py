###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os

from odoo import _
from odoo.tests.common import TransactionCase


class TestImportTemplateStockLot(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product_01 = self.env['product.product'].create({
            'name': 'Test Product 01 (lot tracking)',
            'type': 'product',
            'tracking': 'lot',
            'default_code': 'PROD1TEST',
            'standard_price': 80,
            'list_price': 100,
        })
        self.product_02 = self.env['product.product'].create({
            'name': 'Test Product 02 (without tracking)',
            'type': 'product',
            'tracking': 'none',
            'default_code': 'PROD2TEST',
            'standard_price': 3,
            'list_price': 5,
        })
        self.attr = self.env['product.attribute'].create({
            'name': 'Attribute test',
        })
        for value in ['White', 'Black']:
            self.env['product.attribute.value'].create({
                'attribute_id': self.attr.id,
                'name': value,
            })
        self.product_tmpl_03 = self.env['product.template'].create({
            'name': 'Test product 3 (lot tracking)',
            'type': 'product',
            'tracking': 'lot',
            'standard_price': 10.00,
            'company_id': False,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr.id,
                    'value_ids': [(6, 0, self.attr.value_ids.ids)],
                }),
            ],
        })
        self.assertEqual(len(self.product_tmpl_03.product_variant_ids), 2)
        self.product_03_white = (
            self.product_tmpl_03.product_variant_ids.filtered(
                lambda p: p.product_template_attribute_value_ids.name == 'White'))
        self.assertEqual(len(self.product_03_white), 1)
        self.product_03_black = (
            self.product_tmpl_03.product_variant_ids.filtered(
                lambda p: p.product_template_attribute_value_ids.name == 'Black'))
        self.assertEqual(len(self.product_03_black), 1)
        self.product_03_white.default_code = 'PROD1TEST-White'
        self.product_03_black.default_code = 'PROD1TEST-Black'
        self.env.flush_all()

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def get_file_name(self, fname):
        return fname.split('/')[-1:][0]

    def test_import_create_lot_with_product_id_column(self):
        fname = self.get_sample('sample_with_product_id_column.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_stock_lot.template_stock_lot').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertFalse(lot_01)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertFalse(lot_02)
        wizard.action_import_from_simulation()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertTrue(lot_01)
        self.assertEqual(lot_01.product_id, self.product_01)
        self.assertIn('Note for lot 1111', lot_01.note)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertTrue(lot_02)
        self.assertEqual(lot_02.product_id, self.product_02)
        self.assertIn('Note for lot 2222', lot_02.note)

    def test_import_create_lot_without_product_id(self):
        fname = self.get_sample('sample_without_product_id_column.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_stock_lot.template_stock_lot').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 2)
        self.assertIn(_(
            '2: The lot \'LOT_1111\' does not exist, select one of the '
            'available ones or add a new column \'product_id\' to the file '
            'with the product\'s default code or barcode.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The lot \'LOT_2222\' does not exist, select one of the '
            'available ones or add a new column \'product_id\' to the file '
            'with the product\'s default code or barcode.'),
            wizard.line_ids[1].name)
        wizard.action_import_from_simulation()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 2)
        self.assertIn(_(
            '2: The lot \'LOT_1111\' does not exist, select one of the '
            'available ones or add a new column \'product_id\' to the file '
            'with the product\'s default code or barcode.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The lot \'LOT_2222\' does not exist, select one of the '
            'available ones or add a new column \'product_id\' to the file '
            'with the product\'s default code or barcode.'),
            wizard.line_ids[1].name)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertFalse(lot_01)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertFalse(lot_02)
        self.env['stock.lot'].create({
            'product_id': self.product_01.id,
            'name': 'LOT_1111',
        })
        self.env['stock.lot'].create({
            'product_id': self.product_02.id,
            'name': 'LOT_2222',
        })
        fname = self.get_sample('sample_without_product_id_column.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_stock_lot.template_stock_lot').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        wizard.action_import_from_simulation()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertTrue(lot_01)
        self.assertEqual(lot_01.product_id, self.product_01)
        self.assertIn('Note for lot 1111', lot_01.note)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertTrue(lot_02)
        self.assertEqual(lot_02.product_id, self.product_02)
        self.assertIn('Note for lot 2222', lot_02.note)

    def test_import_create_lot_with_variants_with_product_id_column(self):
        fname = self.get_sample(
            'sample_with_variants_with_product_id_column.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_stock_lot.template_stock_lot').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertFalse(lot_01)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertFalse(lot_02)
        wizard.action_import_from_simulation()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertTrue(lot_01)
        self.assertEqual(lot_01.product_id, self.product_03_white)
        self.assertIn('Note for lot 1111', lot_01.note)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertTrue(lot_02)
        self.assertEqual(lot_02.product_id, self.product_03_black)
        self.assertIn('Note for lot 2222', lot_02.note)

    def test_import_create_lot_with_variants_without_product_id_column(
            self):
        fname = self.get_sample(
            'sample_with_variants_without_product_id_column.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_stock_lot.template_stock_lot').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 2)
        self.assertIn(_(
            '2: The lot \'LOT_1111\' does not exist, select one of the '
            'available ones or add a new column \'product_id\' to the file '
            'with the product\'s default code or barcode.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The lot \'LOT_2222\' does not exist, select one of the '
            'available ones or add a new column \'product_id\' to the file '
            'with the product\'s default code or barcode.'),
            wizard.line_ids[1].name)
        wizard.action_import_from_simulation()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 2)
        self.assertIn(_(
            '2: The lot \'LOT_1111\' does not exist, select one of the '
            'available ones or add a new column \'product_id\' to the file '
            'with the product\'s default code or barcode.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The lot \'LOT_2222\' does not exist, select one of the '
            'available ones or add a new column \'product_id\' to the file '
            'with the product\'s default code or barcode.'),
            wizard.line_ids[1].name)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertFalse(lot_01)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertFalse(lot_02)
        self.env['stock.lot'].create({
            'product_id': self.product_03_white.id,
            'name': 'LOT_1111',
        })
        self.env['stock.lot'].create({
            'product_id': self.product_03_black.id,
            'name': 'LOT_2222',
        })
        fname = self.get_sample(
            'sample_with_variants_without_product_id_column.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_stock_lot.template_stock_lot').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        wizard.action_import_from_simulation()
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertTrue(lot_01)
        self.assertEqual(lot_01.product_id, self.product_03_white)
        self.assertIn('Note for lot 1111', lot_01.note)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertTrue(lot_02)
        self.assertEqual(lot_02.product_id, self.product_03_black)
        self.assertIn('Note for lot 2222', lot_02.note)

    def test_import_write_lot_with_product_id_column(self):
        self.env['stock.lot'].create({
            'product_id': self.product_01.id,
            'name': 'LOT_1111',
        })
        fname = self.get_sample('sample_with_product_id_column.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_stock_lot.template_stock_lot').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertEqual(len(lot_01), 1)
        self.assertFalse(lot_01.note)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertFalse(lot_02)
        wizard.action_import_from_simulation()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertTrue(lot_01)
        self.assertEqual(lot_01.product_id, self.product_01)
        self.assertIn('Note for lot 1111', lot_01.note)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertTrue(lot_02)
        self.assertEqual(lot_02.product_id, self.product_02)
        self.assertIn('Note for lot 2222', lot_02.note)

    def test_import_write_lot_without_product_id_column(self):
        self.env['stock.lot'].create({
            'product_id': self.product_01.id,
            'name': 'LOT_1111',
        })
        self.env['stock.lot'].create({
            'product_id': self.product_02.id,
            'name': 'LOT_2222',
        })
        fname = self.get_sample('sample_without_product_id_column.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_stock_lot.template_stock_lot').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertEqual(len(lot_01), 1)
        self.assertFalse(lot_01.note)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertEqual(len(lot_02), 1)
        self.assertFalse(lot_02.note)
        wizard.action_import_from_simulation()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertTrue(lot_01)
        self.assertEqual(lot_01.product_id, self.product_01)
        self.assertIn('Note for lot 1111', lot_01.note)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertTrue(lot_02)
        self.assertEqual(lot_02.product_id, self.product_02)
        self.assertIn('Note for lot 2222', lot_02.note)

    def test_import_write_lot_with_variants_with_product_id_column(self):
        self.env['stock.lot'].create({
            'product_id': self.product_03_white.id,
            'name': 'LOT_1111',
        })
        fname = self.get_sample(
            'sample_with_variants_with_product_id_column.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_stock_lot.template_stock_lot').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertEqual(len(lot_01), 1)
        self.assertFalse(lot_01.note)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertFalse(lot_02)
        wizard.action_import_from_simulation()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertTrue(lot_01)
        self.assertEqual(lot_01.product_id, self.product_03_white)
        self.assertIn('Note for lot 1111', lot_01.note)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertTrue(lot_02)
        self.assertEqual(lot_02.product_id, self.product_03_black)
        self.assertIn('Note for lot 2222', lot_02.note)

    def test_import_write_lot_with_variants_without_product_id_column(self):
        self.env['stock.lot'].create({
            'product_id': self.product_03_white.id,
            'name': 'LOT_1111',
        })
        self.env['stock.lot'].create({
            'product_id': self.product_03_black.id,
            'name': 'LOT_2222',
        })
        fname = self.get_sample(
            'sample_with_variants_without_product_id_column.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_stock_lot.template_stock_lot').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertEqual(len(lot_01), 1)
        self.assertFalse(lot_01.note)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertEqual(len(lot_02), 1)
        self.assertFalse(lot_02.note)
        wizard.action_import_from_simulation()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertTrue(lot_01)
        self.assertEqual(lot_01.product_id, self.product_03_white)
        self.assertIn('Note for lot 1111', lot_01.note)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertTrue(lot_02)
        self.assertEqual(lot_02.product_id, self.product_03_black)
        self.assertIn('Note for lot 2222', lot_02.note)

    def test_import_lot_error_empty_required_fields(self):
        fname = self.get_sample('sample_empty_required_fields.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_stock_lot.template_stock_lot').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 3)
        self.assertIn(_(
            '2: The \'name\' field is required, you must fill it with a valid '
            'value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: Product \'\' not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '3: The \'product_id\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[2].name)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertFalse(lot_01)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertFalse(lot_02)
        wizard.action_import_from_simulation()
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 3)
        self.assertIn(_(
            '2: The \'name\' field is required, you must fill it with a valid '
            'value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: Product \'\' not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '3: The \'product_id\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[2].name)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertFalse(lot_01)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertFalse(lot_02)

    def test_import_lot_error_no_allow_change_product_qty_compute_field(self):
        fname = self.get_sample(
            'sample_no_allow_change_product_qty_field.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_stock_lot.template_stock_lot').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertFalse(lot_01)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertFalse(lot_02)
        wizard.action_import_from_simulation()
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertTrue(lot_01)
        self.assertEqual(lot_01.product_id, self.product_01)
        self.assertIn('Note for lot 1111', lot_01.note)
        self.assertEqual(lot_01.product_qty, 0)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertTrue(lot_02)
        self.assertEqual(lot_02.product_id, self.product_02)
        self.assertIn('Note for lot 2222', lot_02.note)
        self.assertEqual(lot_02.product_qty, 0)

    def test_import_lot_same_lote_different_product_id_field(self):
        self.env['stock.lot'].create({
            'product_id': self.product_01.id,
            'name': 'LOT_1111',
        })
        fname = self.get_sample(
            'sample_write_same_lot_different_product_id_field.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_stock_lot.template_stock_lot').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertTrue(lot_01)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertFalse(lot_02)
        wizard.action_import_from_simulation()
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lots_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertEqual(len(lots_01), 2)
        lot_01_product_01 = lots_01.filtered(
            lambda lot: lot.product_id == self.product_01)
        self.assertTrue(len(lot_01_product_01), 1)
        self.assertFalse(lot_01_product_01.note)
        lot_01_product_02 = lots_01.filtered(
            lambda lot: lot.product_id == self.product_02)
        self.assertTrue(len(lot_01_product_02), 1)
        self.assertIn('Note for lot 1111', lot_01_product_02.note)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertTrue(lot_02)
        self.assertEqual(lot_02.product_id, self.product_02)
        self.assertIn('Note for lot 2222', lot_02.note)

    def test_new_fields_error_no_exist_field(self):
        fname = self.get_sample('sample_new_fields_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_stock_lot.template_stock_lot').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 2)
        self.assertIn(_(
            '2: The \'new_field\' column is not a field for model.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The \'new_field\' column is not a field for model.'),
            wizard.line_ids[1].name)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertFalse(lot_01)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertFalse(lot_02)
        wizard.action_import_from_simulation()
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 2)
        self.assertIn(_(
            '2: The \'new_field\' column is not a field for model.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The \'new_field\' column is not a field for model.'),
            wizard.line_ids[1].name)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertFalse(lot_01)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertFalse(lot_02)

    def test_import_create_lot_serial_unique_for_product(self):
        self.product_serial = self.env['product.product'].create({
            'name': 'Test Product (serial tracking)',
            'type': 'product',
            'tracking': 'serial',
            'default_code': 'PRODSERIALTEST',
            'standard_price': 80,
            'list_price': 100,
        })
        fname = self.get_sample('sample_write_serial_unique_for_product.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_stock_lot.template_stock_lot').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEqual(wizard.total_rows, 3)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertFalse(lot_01)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertFalse(lot_02)
        wizard.action_import_from_simulation()
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertTrue(lot_01)
        self.assertEqual(lot_01.product_id, self.product_serial)
        self.assertIn('Note for lot 1111 duplicated', lot_01.note)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertTrue(lot_02)
        self.assertEqual(lot_02.product_id, self.product_02)
        self.assertIn('Note for lot 2222', lot_02.note)

    def test_import_lot_with_empty_char_column(self):
        fname = self.get_sample('sample_with_empty_char_column.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_stock_lot.template_stock_lot').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertFalse(lot_01)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertFalse(lot_02)
        wizard.action_import_from_simulation()
        self.assertEqual(wizard.total_rows, 2)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(wizard.total_warn, 0)
        self.assertEqual(wizard.total_error, 0)
        lot_01 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_1111'),
        ])
        self.assertTrue(lot_01)
        self.assertEqual(lot_01.product_id, self.product_01)
        self.assertIn('Note for lot 1111', lot_01.note)
        lot_02 = self.env['stock.lot'].search([
            ('name', '=', 'LOT_2222'),
        ])
        self.assertTrue(lot_02)
        self.assertEqual(lot_02.product_id, self.product_02)
        self.assertEqual('', lot_02.note)
