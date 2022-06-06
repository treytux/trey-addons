###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import logging
import os

from odoo import _
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)


class TestImportTemplateSupplierInfo(TransactionCase):

    def setUp(self):
        super().setUp()
        self.supplier_01 = self.env['res.partner'].create({
            'name': 'Test supplier 01',
            'supplier': True,
            'ref': 'REFSUPPLIER01',
        })
        self.supplier_02 = self.env['res.partner'].create({
            'name': 'Test supplier 02',
            'supplier': True,
            'ref': 'REFSUPPLIER02',
        })
        self.supplier_03 = self.env['res.partner'].create({
            'name': 'Test supplier 03',
            'supplier': True,
            'ref': 'REFSUPPLIER03',
        })
        self.product_01 = self.env['product.product'].create({
            'name': 'Test Product 01',
            'type': 'service',
            'default_code': 'PROD1TEST',
            'standard_price': 80,
            'list_price': 100,
        })
        self.product_02 = self.env['product.product'].create({
            'name': 'Test Product 02',
            'type': 'service',
            'default_code': 'PROD2TEST',
            'standard_price': 3,
            'list_price': 5,
        })
        self.product_03 = self.env['product.product'].create({
            'name': 'Test Product 03',
            'type': 'service',
            'barcode': '1122334455667',
            'default_code': 'PROD3TEST',
            'standard_price': 10,
            'list_price': 15,
        })
        self.attr = self.env['product.attribute'].create({
            'name': 'Attribute test',
        })
        for value in ['White', 'Black']:
            self.env['product.attribute.value'].create({
                'attribute_id': self.attr.id,
                'name': value,
            })
        self.product_tmpl_04 = self.env['product.template'].create({
            'name': 'Test product 4',
            'type': 'service',
            'standard_price': 10.00,
            'company_id': False,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr.id,
                    'value_ids': [(6, 0, self.attr.value_ids.ids)],
                }),
            ],
        })
        self.assertEquals(len(self.product_tmpl_04.product_variant_ids), 2)
        self.product_04_white = (
            self.product_tmpl_04.product_variant_ids.filtered(
                lambda p: p.attribute_value_ids.name == 'White'))
        self.assertEquals(len(self.product_04_white), 1)
        self.product_04_black = (
            self.product_tmpl_04.product_variant_ids.filtered(
                lambda p: p.attribute_value_ids.name == 'Black'))
        self.assertEquals(len(self.product_04_black), 1)
        self.product_04_white.default_code = 'PROD1TEST-White'
        self.product_04_black.default_code = 'PROD1TEST-Black'

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def get_file_name(self, fname):
        return fname.split('/')[-1:][0]

    def test_import_create_ok(self):
        fname = self.get_sample('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_supplierinfo.template_supplierinfo').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.product_01.seller_ids), 1)
        supplierinfo_sup_01 = self.product_01.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_01.id)
        self.assertEquals(len(supplierinfo_sup_01), 1)
        self.assertEquals(supplierinfo_sup_01.product_name, 'supplier_name_01')
        self.assertEquals(supplierinfo_sup_01.product_code, 'supplier_code_01')
        self.assertEquals(supplierinfo_sup_01.min_qty, 10)
        self.assertEquals(supplierinfo_sup_01.price, 11.11)
        self.assertEquals(len(self.product_02.seller_ids), 1)
        supplierinfo_sup_02 = self.product_02.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_02.id)
        self.assertEquals(len(supplierinfo_sup_02), 1)
        self.assertEquals(supplierinfo_sup_02.product_name, 'supplier_name_02')
        self.assertEquals(supplierinfo_sup_02.product_code, 'supplier_code_02')
        self.assertEquals(supplierinfo_sup_02.min_qty, 5)
        self.assertEquals(supplierinfo_sup_02.price, 22.22)
        self.assertEquals(len(self.product_03.seller_ids), 1)
        supplierinfo_sup_03 = self.product_03.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_03.id)
        self.assertEquals(len(supplierinfo_sup_03), 1)
        self.assertEquals(supplierinfo_sup_03.product_name, 'supplier_name_03')
        self.assertEquals(supplierinfo_sup_03.product_code, 'supplier_code_03')
        self.assertEquals(supplierinfo_sup_03.min_qty, 15)
        self.assertEquals(supplierinfo_sup_03.price, 33.33)

    def test_import_write_ok(self):
        self.env['product.supplierinfo'].create({
            'product_id': self.product_01.id,
            'name': self.supplier_01.id,
            'product_name': 'Supplier name',
            'product_code': 'SUP_CODE',
            'min_qty': 12,
            'price': 10.50,
        })
        self.env['product.supplierinfo'].create({
            'product_id': self.product_02.id,
            'name': self.supplier_02.id,
        })
        fname = self.get_sample('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_supplierinfo.template_supplierinfo').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.product_01.seller_ids), 1)
        supplierinfo_sup_01 = self.product_01.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_01.id)
        self.assertEquals(len(supplierinfo_sup_01), 1)
        self.assertEquals(supplierinfo_sup_01.product_name, 'supplier_name_01')
        self.assertEquals(supplierinfo_sup_01.product_code, 'supplier_code_01')
        self.assertEquals(supplierinfo_sup_01.min_qty, 10)
        self.assertEquals(supplierinfo_sup_01.price, 11.11)
        self.assertEquals(len(self.product_02.seller_ids), 1)
        supplierinfo_sup_02 = self.product_02.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_02.id)
        self.assertEquals(len(supplierinfo_sup_02), 1)
        self.assertEquals(supplierinfo_sup_02.product_name, 'supplier_name_02')
        self.assertEquals(supplierinfo_sup_02.product_code, 'supplier_code_02')
        self.assertEquals(supplierinfo_sup_02.min_qty, 5)
        self.assertEquals(supplierinfo_sup_02.price, 22.22)
        self.assertEquals(len(self.product_03.seller_ids), 1)
        supplierinfo_sup_03 = self.product_03.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_03.id)
        self.assertEquals(len(supplierinfo_sup_03), 1)
        self.assertEquals(supplierinfo_sup_03.product_name, 'supplier_name_03')
        self.assertEquals(supplierinfo_sup_03.product_code, 'supplier_code_03')
        self.assertEquals(supplierinfo_sup_03.min_qty, 15)
        self.assertEquals(supplierinfo_sup_03.price, 33.33)

    def test_import_error_missing_cols(self):
        fname = self.get_sample('sample_error_missing_cols.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_supplierinfo.template_supplierinfo').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        with self.assertRaises(UserError):
            wizard.open_template_form()

    def test_import_error_product_not_exists(self):
        fname = self.get_sample('sample_error_product_not_exists.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_supplierinfo.template_supplierinfo').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: The product \'xxxx\' does not exist, select one of the '
            'available ones.'), wizard.line_ids[0].name)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: The product \'xxxx\' does not exist, select one of the '
            'available ones.'), wizard.line_ids[0].name)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 1)
        supplierinfo_sup_02 = self.product_02.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_02.id)
        self.assertEquals(len(supplierinfo_sup_02), 1)
        self.assertEquals(supplierinfo_sup_02.product_name, 'supplier_name_02')
        self.assertEquals(supplierinfo_sup_02.product_code, 'supplier_code_02')

    def test_import_error_several_product(self):
        self.product_01_duply = self.env['product.product'].create({
            'name': 'Test Product 01 duply',
            'type': 'service',
            'default_code': 'PROD1TEST',
            'standard_price': 44,
            'list_price': 50,
        })
        self.product_03_duply = self.env['product.product'].create({
            'name': 'Test Product 01 duply',
            'type': 'service',
            'default_code': '1122334455667',
            'standard_price': 44,
            'list_price': 50,
        })
        fname = self.get_sample('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_supplierinfo.template_supplierinfo').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: More than one product found for PROD1TEST.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '4: More than one product found for 1122334455667.'),
            wizard.line_ids[1].name)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: More than one product found for PROD1TEST.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '4: More than one product found for 1122334455667.'),
            wizard.line_ids[1].name)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_03.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 1)
        supplierinfo_sup_02 = self.product_02.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_02.id)
        self.assertEquals(len(supplierinfo_sup_02), 1)
        self.assertEquals(supplierinfo_sup_02.product_name, 'supplier_name_02')
        self.assertEquals(supplierinfo_sup_02.product_code, 'supplier_code_02')

    def test_import_error_empty_default_code(self):
        fname = self.get_sample('sample_empty_default_code.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_supplierinfo.template_supplierinfo').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_('2: Product None not found.'), wizard.line_ids.name)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 0)
        self.assertEquals(len(self.product_03.seller_ids), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_('2: Product None not found.'), wizard.line_ids.name)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 1)
        supplierinfo_sup_02 = self.product_02.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_02.id)
        self.assertEquals(len(supplierinfo_sup_02), 1)
        self.assertEquals(supplierinfo_sup_02.product_name, 'supplier_name_02')
        self.assertEquals(supplierinfo_sup_02.product_code, 'supplier_code_02')
        self.assertEquals(len(self.product_03.seller_ids), 1)
        supplierinfo_sup_03 = self.product_03.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_03.id)
        self.assertEquals(len(supplierinfo_sup_03), 1)
        self.assertEquals(supplierinfo_sup_03.product_name, 'supplier_name_03')
        self.assertEquals(supplierinfo_sup_03.product_code, 'supplier_code_03')

    def test_import_error_empty_supplier_ref(self):
        fname = self.get_sample('sample_empty_supplier_ref.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_supplierinfo.template_supplierinfo').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: Supplier ref None not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: The \'name\' field is required, you must fill it with a valid '
            'value.'), wizard.line_ids[1].name)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: Supplier ref None not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: The \'name\' field is required, you must fill it with a valid '
            'value.'), wizard.line_ids[1].name)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 1)
        supplierinfo_sup_02 = self.product_02.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_02.id)
        self.assertEquals(len(supplierinfo_sup_02), 1)
        self.assertEquals(supplierinfo_sup_02.product_name, 'supplier_name_02')
        self.assertEquals(supplierinfo_sup_02.product_code, 'supplier_code_02')

    def test_import_error_empty_default_code_supplier_ref(self):
        fname = self.get_sample('sample_empty_default_code_supplier_ref.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_supplierinfo.template_supplierinfo').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_('2: Product None not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Supplier ref None not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '2: The \'name\' field is required, you must fill it with a valid '
            'value.'), wizard.line_ids[2].name)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_('2: Product None not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Supplier ref None not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '2: The \'name\' field is required, you must fill it with a valid '
            'value.'), wizard.line_ids[2].name)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 1)
        supplierinfo_sup_02 = self.product_02.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_02.id)
        self.assertEquals(len(supplierinfo_sup_02), 1)
        self.assertEquals(supplierinfo_sup_02.product_name, 'supplier_name_02')
        self.assertEquals(supplierinfo_sup_02.product_code, 'supplier_code_02')
        self.assertEquals(supplierinfo_sup_02.min_qty, 5)
        self.assertEquals(supplierinfo_sup_02.price, 22.22)

    def test_import_error_empty_values(self):
        fname = self.get_sample('sample_empty_values.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_supplierinfo.template_supplierinfo').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 0)
        wizard.action_import_from_simulation()
        supplierinfo_sup_01 = self.product_01.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_01.id)
        self.assertEquals(len(supplierinfo_sup_01), 1)
        self.assertEquals(supplierinfo_sup_01.product_name, '')
        self.assertEquals(supplierinfo_sup_01.product_code, '')
        self.assertEquals(supplierinfo_sup_01.min_qty, 0)
        self.assertEquals(supplierinfo_sup_01.price, 0)
        self.assertEquals(len(self.product_02.seller_ids), 1)
        supplierinfo_sup_02 = self.product_02.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_02.id)
        self.assertEquals(len(supplierinfo_sup_02), 1)
        self.assertEquals(supplierinfo_sup_02.product_name, 'supplier_name_02')
        self.assertEquals(supplierinfo_sup_02.product_code, 'supplier_code_02')
        self.assertEquals(supplierinfo_sup_02.min_qty, 5)
        self.assertEquals(supplierinfo_sup_02.price, 22.22)

    def test_new_fields_ok(self):
        fname = self.get_sample('sample_new_fields_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_supplierinfo.template_supplierinfo').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 0)
        wizard.action_import_from_simulation()
        supplierinfo_sup_01 = self.product_01.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_01.id)
        self.assertEquals(len(supplierinfo_sup_01), 1)
        self.assertEquals(supplierinfo_sup_01.product_name, 'supplier_name_01')
        self.assertEquals(supplierinfo_sup_01.product_code, 'supplier_code_01')
        self.assertEquals(supplierinfo_sup_01.min_qty, 10)
        self.assertEquals(supplierinfo_sup_01.price, 11.11)
        self.assertEquals(supplierinfo_sup_01.delay, 7)
        self.assertEquals(len(self.product_02.seller_ids), 1)
        supplierinfo_sup_02 = self.product_02.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_02.id)
        self.assertEquals(len(supplierinfo_sup_02), 1)
        self.assertEquals(supplierinfo_sup_02.product_name, 'supplier_name_02')
        self.assertEquals(supplierinfo_sup_02.product_code, 'supplier_code_02')
        self.assertEquals(supplierinfo_sup_02.min_qty, 5)
        self.assertEquals(supplierinfo_sup_02.price, 22.22)
        self.assertEquals(supplierinfo_sup_02.delay, 14)

    def test_new_fields_error(self):
        fname = self.get_sample('sample_new_fields_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_supplierinfo.template_supplierinfo').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '2: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '4: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.'), wizard.line_ids[2].name)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 0)
        self.assertEquals(len(self.product_03.seller_ids), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '2: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '4: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.'), wizard.line_ids[2].name)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 0)
        self.assertEquals(len(self.product_03.seller_ids), 0)

    def test_import_create_disordered_columns_ok(self):
        fname = self.get_sample('sample_disordered_columns.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_supplierinfo.template_supplierinfo').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_03.seller_ids), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.product_01.seller_ids), 1)
        supplierinfo_sup_01 = self.product_01.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_01.id)
        self.assertEquals(len(supplierinfo_sup_01), 1)
        self.assertEquals(supplierinfo_sup_01.product_name, 'supplier_name_01')
        self.assertEquals(supplierinfo_sup_01.product_code, 'supplier_code_01')
        self.assertEquals(supplierinfo_sup_01.min_qty, 10)
        self.assertEquals(len(self.product_02.seller_ids), 1)
        supplierinfo_sup_02 = self.product_02.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_02.id)
        self.assertEquals(len(supplierinfo_sup_02), 1)
        self.assertEquals(supplierinfo_sup_02.product_name, 'supplier_name_02')
        self.assertEquals(supplierinfo_sup_02.product_code, 'supplier_code_02')
        self.assertEquals(supplierinfo_sup_02.min_qty, 5)
        self.assertEquals(len(self.product_03.seller_ids), 1)
        supplierinfo_sup_03 = self.product_03.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_03.id)
        self.assertEquals(len(supplierinfo_sup_03), 1)
        self.assertEquals(supplierinfo_sup_03.product_name, 'supplier_name_03')
        self.assertEquals(supplierinfo_sup_03.product_code, 'supplier_code_03')
        self.assertEquals(supplierinfo_sup_03.product_code, 'supplier_code_03')
        self.assertEquals(
            supplierinfo_sup_03.product_id.barcode, '1122334455667')
        self.assertEquals(supplierinfo_sup_03.min_qty, 15)

    def test_import_write_disordered_columns_ok(self):
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.product_01.product_tmpl_id.id,
            'name': self.supplier_01.id,
            'product_name': 'Supplier name',
            'product_code': 'SUP_CODE',
            'min_qty': 12,
        })
        self.env['product.supplierinfo'].create({
            'product_id': self.product_02.id,
            'name': self.supplier_02.id,
        })
        fname = self.get_sample('sample_disordered_columns.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_supplierinfo.template_supplierinfo').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.product_01.seller_ids), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.product_01.seller_ids), 2)
        supplierinfo_sup_01 = self.product_01.seller_ids.filtered(
            lambda s: s.name == self.supplier_01
            and s.product_tmpl_id == self.product_01.product_tmpl_id
            and not s.product_id)
        self.assertEquals(len(supplierinfo_sup_01), 1)
        self.assertEquals(supplierinfo_sup_01.product_name, 'Supplier name')
        self.assertEquals(supplierinfo_sup_01.product_code, 'SUP_CODE')
        self.assertEquals(supplierinfo_sup_01.min_qty, 12)
        supplierinfo_sup_01_import = self.product_01.seller_ids.filtered(
            lambda s: s.name == self.supplier_01
            and s.product_tmpl_id == self.product_01.product_tmpl_id
            and s.product_id == self.product_01)
        self.assertEquals(len(supplierinfo_sup_01_import), 1)
        self.assertEquals(
            supplierinfo_sup_01_import.product_name, 'supplier_name_01')
        self.assertEquals(
            supplierinfo_sup_01_import.product_code, 'supplier_code_01')
        self.assertEquals(supplierinfo_sup_01_import.min_qty, 10)
        self.assertEquals(len(self.product_02.seller_ids), 1)
        supplierinfo_sup_02 = self.product_02.seller_ids.filtered(
            lambda s: s.name == self.supplier_02)
        self.assertEquals(len(supplierinfo_sup_02), 1)
        self.assertEquals(supplierinfo_sup_02.product_name, 'supplier_name_02')
        self.assertEquals(supplierinfo_sup_02.product_code, 'supplier_code_02')
        self.assertEquals(supplierinfo_sup_02.min_qty, 5)
        self.assertEquals(len(self.product_03.seller_ids), 1)
        supplierinfo_sup_03 = self.product_03.seller_ids.filtered(
            lambda s: s.name == self.supplier_03)
        self.assertEquals(len(supplierinfo_sup_03), 1)
        self.assertEquals(supplierinfo_sup_03.product_name, 'supplier_name_03')
        self.assertEquals(supplierinfo_sup_03.product_code, 'supplier_code_03')
        self.assertEquals(supplierinfo_sup_03.min_qty, 15)

    def test_import_create_variants_ok(self):
        fname = self.get_sample('sample_variants_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_supplierinfo.template_supplierinfo').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.product_tmpl_04.seller_ids), 0)
        self.assertEquals(len(self.product_04_black.seller_ids), 0)
        self.assertEquals(len(self.product_04_white.seller_ids), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.product_tmpl_04.seller_ids), 2)
        supplierinfo_sup_04_black = self.product_04_black.seller_ids.filtered(
            lambda s: s.name == self.supplier_01
            and s.product_tmpl_id == self.product_tmpl_04
            and s.product_id == self.product_04_black)
        self.assertEquals(len(supplierinfo_sup_04_black), 1)
        self.assertEquals(
            supplierinfo_sup_04_black.product_name, 'supplier_name_01_black')
        self.assertEquals(
            supplierinfo_sup_04_black.product_code, 'supplier_code_01B')
        self.assertEquals(supplierinfo_sup_04_black.min_qty, 10)
        self.assertEquals(supplierinfo_sup_04_black.price, 11.11)
        supplierinfo_sup_04_white = self.product_04_white.seller_ids.filtered(
            lambda s: s.name == self.supplier_01
            and s.product_tmpl_id == self.product_tmpl_04
            and s.product_id == self.product_04_white)
        self.assertEquals(len(supplierinfo_sup_04_white), 1)
        self.assertEquals(
            supplierinfo_sup_04_white.product_name, 'supplier_name_01_white')
        self.assertEquals(
            supplierinfo_sup_04_white.product_code, 'supplier_code_01W')
        self.assertEquals(supplierinfo_sup_04_white.min_qty, 10)
        self.assertEquals(supplierinfo_sup_04_white.price, 22.22)

    def test_import_write_variants_ok(self):
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.product_tmpl_04.id,
            'name': self.supplier_01.id,
            'product_name': 'Supplier name',
            'product_code': 'SUP_CODE',
            'min_qty': 12,
        })
        self.env['product.supplierinfo'].create({
            'product_id': self.product_04_black.id,
            'name': self.supplier_01.id,
        })
        fname = self.get_sample('sample_variants_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_supplierinfo.template_supplierinfo').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.product_tmpl_04.seller_ids), 1)
        supplierinfo_04_black = self.env['product.supplierinfo'].search([
            ('name', '=', self.supplier_01.id),
            ('product_id', '=', self.product_04_black.id),
            ('product_tmpl_id', '=', None),
        ])
        self.assertEquals(len(supplierinfo_04_black), 1)
        supplierinfo_04_white = self.env['product.supplierinfo'].search([
            ('name', '=', self.supplier_01.id),
            ('product_id', '=', self.product_04_white.id),
            ('product_tmpl_id', '=', None),
        ])
        self.assertEquals(len(supplierinfo_04_white), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.product_tmpl_04.seller_ids), 3)
        supplierinfo_sup_04 = self.product_tmpl_04.seller_ids.filtered(
            lambda s: s.name == self.supplier_01
            and s.product_tmpl_id == self.product_tmpl_04
            and not s.product_id)
        self.assertEquals(len(supplierinfo_sup_04), 1)
        self.assertEquals(supplierinfo_sup_04.product_name, 'Supplier name')
        self.assertEquals(supplierinfo_sup_04.product_code, 'SUP_CODE')
        self.assertEquals(supplierinfo_sup_04.min_qty, 12)
        self.assertEquals(supplierinfo_sup_04.price, 0)
        supplierinfo_sup_04_black = self.product_04_black.seller_ids.filtered(
            lambda s: s.name == self.supplier_01
            and s.product_tmpl_id == self.product_tmpl_04
            and s.product_id == self.product_04_black)
        self.assertEquals(len(supplierinfo_sup_04_black), 1)
        self.assertEquals(
            supplierinfo_sup_04_black.product_name, 'supplier_name_01_black')
        self.assertEquals(
            supplierinfo_sup_04_black.product_code, 'supplier_code_01B')
        self.assertEquals(supplierinfo_sup_04_black.min_qty, 10)
        self.assertEquals(supplierinfo_sup_04_black.price, 11.11)
        supplierinfo_sup_04_white = self.product_04_white.seller_ids.filtered(
            lambda s: s.name == self.supplier_01
            and s.product_tmpl_id == self.product_tmpl_04
            and s.product_id == self.product_04_white)
        self.assertEquals(len(supplierinfo_sup_04_white), 1)
        self.assertEquals(
            supplierinfo_sup_04_white.product_name, 'supplier_name_01_white')
        self.assertEquals(
            supplierinfo_sup_04_white.product_code, 'supplier_code_01W')
        self.assertEquals(supplierinfo_sup_04_white.min_qty, 10)
        self.assertEquals(supplierinfo_sup_04_white.price, 22.22)
