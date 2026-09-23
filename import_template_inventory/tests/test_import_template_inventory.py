###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os

from odoo import _
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
        self.product_04 = self.env['product.product'].create({
            'name': 'Test Product 04',
            'type': 'product',
            'default_code': 'PROD4TEST',
            'standard_price': 80,
            'list_price': 100,
        })
        self.lot_1 = self.env['stock.production.lot'].create({
            'name': '111111',
            'product_id': self.product_01.id,
        })
        self.lot_2 = self.env['stock.production.lot'].create({
            'name': '222222',
            'product_id': self.product_02.id,
        })
        self.lot_3 = self.env['stock.production.lot'].create({
            'name': '333333',
            'product_id': self.product_03.id,
        })
        self.lot_4 = self.env['stock.production.lot'].create({
            'name': '444444',
            'product_id': self.product_03.id,
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
        self.location_test_4 = self.env['stock.location'].create({
            'name': 'Test location 4',
            'usage': 'internal',
            'location_id': self.location_stock.id,
        })

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def get_file_name(self, fname):
        return fname.split('/')[-1:][0]

    def test_import_inventory_ok(self):
        fname = self.get_sample('sample_inventory_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_inventory.template_inventory').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        stock_inv_line_1 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_01.id),
        ])
        self.assertEquals(len(stock_inv_line_1), 0)
        stock_inv_line_2 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_02.id),
        ])
        self.assertEquals(len(stock_inv_line_2), 0)
        stock_inv_line_3 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_03.id),
        ])
        self.assertEquals(len(stock_inv_line_3), 0)
        wizard.action_import_from_simulation()
        stock_inv_line_1 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_01.id),
        ])
        self.assertEquals(len(stock_inv_line_1), 1)
        self.assertEquals(len(stock_inv_line_1.inventory_id.line_ids), 3)
        self.assertEquals(stock_inv_line_1.inventory_id.state, 'confirm')
        self.assertEquals(stock_inv_line_1.product_qty, 10)
        self.assertEquals(stock_inv_line_1.location_id, self.location_stock)
        self.assertTrue(stock_inv_line_1.prod_lot_id)
        self.assertEquals(stock_inv_line_1.prod_lot_id, self.lot_1)
        stock_inv_line_2 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_02.id),
        ])
        self.assertEquals(len(stock_inv_line_2), 1)
        self.assertEquals(len(stock_inv_line_2.inventory_id.line_ids), 3)
        self.assertEquals(stock_inv_line_2.inventory_id.state, 'confirm')
        self.assertEquals(stock_inv_line_2.product_qty, 15)
        self.assertEquals(stock_inv_line_2.location_id, self.location_test_2)
        self.assertFalse(stock_inv_line_2.prod_lot_id)
        stock_inv_line_3 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_03.id),
        ])
        self.assertEquals(len(stock_inv_line_3), 1)
        self.assertEquals(len(stock_inv_line_3.inventory_id.line_ids), 3)
        self.assertEquals(stock_inv_line_3.inventory_id.state, 'confirm')
        self.assertEquals(stock_inv_line_3.product_qty, 20)
        self.assertEquals(stock_inv_line_3.location_id, self.location_test_3)
        self.assertFalse(stock_inv_line_3.prod_lot_id)

    def test_import_without_inventory_id(self):
        fname = self.get_sample('sample_inventory_without_inventory_id.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_inventory.template_inventory').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        for line in wizard.line_ids:
            self.assertIn(_(
                'The \'inventory_id\' field is required'), line.name)
        stock_inv_line_1 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_01.id),
        ])
        self.assertEquals(len(stock_inv_line_1), 0)
        stock_inv_line_2 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_02.id),
        ])
        self.assertEquals(len(stock_inv_line_2), 0)
        stock_inv_line_3 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_03.id),
        ])
        self.assertEquals(len(stock_inv_line_3), 0)
        wizard.action_import_from_simulation()
        stock_inv_line_1 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_01.id),
        ])
        self.assertEquals(len(stock_inv_line_1), 0)
        stock_inv_line_2 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_02.id),
        ])
        self.assertEquals(len(stock_inv_line_2), 0)
        stock_inv_line_3 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_03.id),
        ])
        self.assertEquals(len(stock_inv_line_3), 0)

    def test_import_with_one_line_inventory_id(self):
        fname = self.get_sample('sample_inventory_with_line_inventory_id.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_inventory.template_inventory').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: The \'inventory_id\' field is required'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '4: The \'inventory_id\' field is required'),
            wizard.line_ids[1].name)
        stock_inv_line_1 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_01.id),
        ])
        self.assertEquals(len(stock_inv_line_1), 0)
        stock_inv_line_2 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_02.id),
        ])
        self.assertEquals(len(stock_inv_line_2), 0)
        stock_inv_line_3 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_03.id),
        ])
        self.assertEquals(len(stock_inv_line_3), 0)
        wizard.action_import_from_simulation()
        stock_inv_line_1 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_01.id),
        ])
        self.assertEquals(len(stock_inv_line_1), 0)
        stock_inv_line_2 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_02.id),
        ])
        self.assertEquals(len(stock_inv_line_2), 1)
        self.assertEquals(len(stock_inv_line_2.inventory_id.line_ids), 1)
        self.assertEquals(stock_inv_line_2.inventory_id.state, 'confirm')
        self.assertEquals(stock_inv_line_2.product_qty, 15)
        self.assertEquals(stock_inv_line_2.location_id, self.location_test_2)
        self.assertFalse(stock_inv_line_2.prod_lot_id)
        stock_inv_line_3 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_03.id),
        ])
        self.assertEquals(len(stock_inv_line_3), 0)

    def test_import_product_error_cases(self):
        fname = self.get_sample('sample_inventory_product_errors.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_inventory.template_inventory').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 5)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 5)
        self.assertIn(_(
            '2: No value found for \'product_id\'.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: The \'product_id\' field is required'), wizard.line_ids[1].name)
        self.assertIn(_(
            '5: The product \'DESCONOCIDO\' does not exist'),
            wizard.line_ids[2].name)
        self.assertIn(_(
            '5: The \'product_id\' field is required'), wizard.line_ids[3].name)
        self.assertIn(_(
            '6: Lot \'ERRONEO\' not found'), wizard.line_ids[4].name)
        stock_inv_line_1 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_01.id),
        ])
        self.assertEquals(len(stock_inv_line_1), 0)
        stock_inv_line_2 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_02.id),
        ])
        self.assertEquals(len(stock_inv_line_2), 0)
        stock_inv_line_3 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_03.id),
        ])
        self.assertEquals(len(stock_inv_line_3), 0)
        stock_inv_line_4 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_04.id),
        ])
        self.assertEquals(len(stock_inv_line_4), 0)
        wizard.action_import_from_simulation()
        stock_inv_line_1 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_01.id),
        ])
        self.assertEquals(len(stock_inv_line_1), 0)
        stock_inv_line_2 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_02.id),
        ])
        self.assertEquals(len(stock_inv_line_2), 1)
        self.assertEquals(len(stock_inv_line_2.inventory_id.line_ids), 2)
        self.assertEquals(stock_inv_line_2.inventory_id.state, 'confirm')
        self.assertEquals(stock_inv_line_2.product_qty, 15)
        self.assertEquals(stock_inv_line_2.location_id, self.location_test_2)
        self.assertTrue(stock_inv_line_2.prod_lot_id)
        stock_inv_line_3 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_03.id),
        ])
        self.assertEquals(len(stock_inv_line_3), 1)
        self.assertEquals(len(stock_inv_line_3.inventory_id.line_ids), 2)
        self.assertEquals(stock_inv_line_3.inventory_id.state, 'confirm')
        self.assertEquals(stock_inv_line_3.product_qty, 20)
        self.assertEquals(stock_inv_line_3.location_id, self.location_test_3)
        self.assertFalse(stock_inv_line_3.prod_lot_id)
        stock_inv_line_4 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_04.id),
        ])
        self.assertEquals(len(stock_inv_line_4), 0)

    def test_with_product_inventory_progress(self):
        inventory = self.env['stock.inventory'].create({
            'name': 'Inventary in progress',
            'filter': 'partial',
            'location_id': self.location_stock.id,
            'exhausted': True,
        })
        inventory.action_start()
        stock_inv_line = self.env['stock.inventory.line'].create({
            'inventory_id': inventory.id,
            'product_id': self.product_01.id,
            'product_qty': 10,
            'location_id': self.location_stock.id,
        })
        self.assertEquals(len(inventory.line_ids), 1)
        self.assertEquals(len(stock_inv_line), 1)
        self.assertEquals(stock_inv_line.inventory_id.state, 'confirm')
        fname = self.get_sample('sample_inventory_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_inventory.template_inventory').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: Already exists an inventory'), wizard.line_ids[0].name)
        stock_inv_line_1 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_01.id),
            ('inventory_id', '!=', inventory.id),
        ])
        self.assertEquals(len(stock_inv_line_1), 0)
        stock_inv_line_2 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_02.id),
        ])
        self.assertEquals(len(stock_inv_line_2), 0)
        stock_inv_line_3 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_03.id),
        ])
        self.assertEquals(len(stock_inv_line_3), 0)
        wizard.action_import_from_simulation()
        stock_inv_line_1 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_01.id),
            ('inventory_id', '!=', inventory.id),
        ])
        self.assertEquals(len(stock_inv_line_1), 0)
        stock_inv_line_2 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_02.id),
        ])
        self.assertEquals(len(stock_inv_line_2), 1)
        self.assertEquals(len(stock_inv_line_2.inventory_id.line_ids), 2)
        self.assertEquals(stock_inv_line_2.inventory_id.state, 'confirm')
        self.assertEquals(stock_inv_line_2.product_qty, 15)
        self.assertEquals(stock_inv_line_2.location_id, self.location_test_2)
        self.assertFalse(stock_inv_line_2.prod_lot_id)
        stock_inv_line_3 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_03.id),
        ])
        self.assertEquals(len(stock_inv_line_3), 1)
        self.assertEquals(len(stock_inv_line_3.inventory_id.line_ids), 2)
        self.assertEquals(stock_inv_line_3.inventory_id.state, 'confirm')
        self.assertEquals(stock_inv_line_3.product_qty, 20)
        self.assertEquals(stock_inv_line_3.location_id, self.location_test_3)
        self.assertFalse(stock_inv_line_3.prod_lot_id)

    def test_import_location_error_cases(self):
        fname = self.get_sample('sample_inventory_location_errors.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_inventory.template_inventory').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 10)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 10)
        self.assertIn(_(
            '2: No value found for \'inventory_location_id\''),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The location \'Desconocida\' does not exist'),
            wizard.line_ids[2].name)
        self.assertIn(_(
            '4: No value found for \'location_id\''), wizard.line_ids[4].name)
        self.assertIn(_(
            '5: The location \'Desconocida\' does not exist'),
            wizard.line_ids[6].name)
        self.assertIn(_(
            '6: The location \'Desconocida\' does not exist'),
            wizard.line_ids[8].name)
        stock_inv_line_1 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_01.id),
        ])
        self.assertEquals(len(stock_inv_line_1), 0)
        stock_inv_line_2 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_02.id),
        ])
        self.assertEquals(len(stock_inv_line_2), 0)
        stock_inv_line_3 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_03.id),
        ])
        self.assertEquals(len(stock_inv_line_3), 0)
        stock_inv_line_4 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_04.id),
        ])
        self.assertEquals(len(stock_inv_line_4), 0)
        wizard.action_import_from_simulation()
        stock_inv_line_1 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_01.id),
        ])
        self.assertEquals(len(stock_inv_line_1), 0)
        stock_inv_line_2 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_02.id),
        ])
        self.assertEquals(len(stock_inv_line_2), 0)
        stock_inv_line_3 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_03.id),
        ])
        self.assertEquals(len(stock_inv_line_3), 0)
        stock_inv_line_4 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_04.id),
        ])
        self.assertEquals(len(stock_inv_line_4), 0)

    def test_import_product_qty_error_cases(self):
        fname = self.get_sample('sample_inventory_product_qty_errors.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_inventory.template_inventory').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '3: The value of the \'product_qty\' field cannot be a negative.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '4: The \'product_qty\' field is required'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '5: The \'product_qty\' field is required'),
            wizard.line_ids[2].name)
        stock_inv_line_1 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_01.id),
        ])
        self.assertEquals(len(stock_inv_line_1), 0)
        stock_inv_line_2 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_02.id),
        ])
        self.assertEquals(len(stock_inv_line_2), 0)
        stock_inv_line_3 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_03.id),
        ])
        self.assertEquals(len(stock_inv_line_3), 0)
        stock_inv_line_4 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_04.id),
        ])
        self.assertEquals(len(stock_inv_line_4), 0)
        wizard.action_import_from_simulation()
        stock_inv_line_1 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_01.id),
        ])
        self.assertEquals(len(stock_inv_line_1), 1)
        self.assertEquals(len(stock_inv_line_1.inventory_id.line_ids), 1)
        self.assertEquals(stock_inv_line_1.inventory_id.state, 'confirm')
        self.assertEquals(stock_inv_line_1.product_qty, 0)
        self.assertEquals(stock_inv_line_1.location_id, self.location_stock)
        self.assertTrue(stock_inv_line_1.prod_lot_id)
        stock_inv_line_2 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_02.id),
        ])
        self.assertEquals(len(stock_inv_line_2), 0)
        stock_inv_line_3 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_03.id),
        ])
        self.assertEquals(len(stock_inv_line_3), 0)
        stock_inv_line_4 = self.env['stock.inventory.line'].search([
            ('product_id', '=', self.product_04.id),
        ])
        self.assertEquals(len(stock_inv_line_4), 0)
