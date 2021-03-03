# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os

from openerp import _
from openerp.tests.common import TransactionCase


class TestImportTemplateSupplierInfo(TransactionCase):

    def setUp(self):
        super(TestImportTemplateSupplierInfo, self).setUp()
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
            'default_code': 'PROD3TEST',
            'standard_price': 10,
            'list_price': 15,
        })

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
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 2)
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

    def test_import_write_ok(self):
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.product_01.product_tmpl_id.id,
            'name': self.supplier_01.id,
            'product_name': 'Supplier name',
            'product_code': 'SUP_CODE',
            'min_qty': 12,
        })
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.product_02.product_tmpl_id.id,
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
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.product_01.seller_ids), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 2)
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

    def test_import_error_missing_cols(self):
        fname = self.get_sample('sample_error_missing_cols.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_supplierinfo.template_supplierinfo').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        self.assertRaises(Exception, wizard.open_template_form)

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
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: The product template \'xxxx\' does not exist, select one of '
            'the available ones.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: The \'product_tmpl_id\' field is required, you must fill it '
            'with a valid value.'), wizard.line_ids[1].name)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: The product template \'xxxx\' does not exist, select one of '
            'the available ones.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: The \'product_tmpl_id\' field is required, you must fill it '
            'with a valid value.'), wizard.line_ids[1].name)
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
        fname = self.get_sample('sample_ok.xlsx')
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
            '2: More than one product template found for PROD1TEST.'),
            wizard.line_ids.name)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: More than one product template found for PROD1TEST.'),
            wizard.line_ids.name)
        self.assertEquals(len(self.product_01.seller_ids), 0)
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
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: Product template None not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: The \'product_tmpl_id\' field is required, you must fill it '
            'with a valid value.'), wizard.line_ids[1].name)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: Product template None not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: The \'product_tmpl_id\' field is required, you must fill it '
            'with a valid value.'), wizard.line_ids[1].name)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 1)
        supplierinfo_sup_02 = self.product_02.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_02.id)
        self.assertEquals(len(supplierinfo_sup_02), 1)
        self.assertEquals(supplierinfo_sup_02.product_name, 'supplier_name_02')
        self.assertEquals(supplierinfo_sup_02.product_code, 'supplier_code_02')

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
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 4)
        self.assertIn(_(
            '2: Product template None not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Supplier ref None not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '2: The \'product_tmpl_id\' field is required, you must fill it '
            'with a valid value.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '2: The \'name\' field is required, you must fill it with a valid '
            'value.'), wizard.line_ids[3].name)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 4)
        self.assertIn(_(
            '2: Product template None not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: Supplier ref None not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '2: The \'product_tmpl_id\' field is required, you must fill it '
            'with a valid value.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '2: The \'name\' field is required, you must fill it with a valid '
            'value.'), wizard.line_ids[3].name)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        self.assertEquals(len(self.product_02.seller_ids), 1)
        supplierinfo_sup_02 = self.product_02.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_02.id)
        self.assertEquals(len(supplierinfo_sup_02), 1)
        self.assertEquals(supplierinfo_sup_02.product_name, 'supplier_name_02')
        self.assertEquals(supplierinfo_sup_02.product_code, 'supplier_code_02')
        self.assertEquals(supplierinfo_sup_02.min_qty, 5)

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
        self.assertEquals(len(self.product_02.seller_ids), 1)
        supplierinfo_sup_02 = self.product_02.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_02.id)
        self.assertEquals(len(supplierinfo_sup_02), 1)
        self.assertEquals(supplierinfo_sup_02.product_name, 'supplier_name_02')
        self.assertEquals(supplierinfo_sup_02.product_code, 'supplier_code_02')
        self.assertEquals(supplierinfo_sup_02.min_qty, 5)

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
        self.assertEquals(supplierinfo_sup_01.delay, 7)
        self.assertEquals(len(self.product_02.seller_ids), 1)
        supplierinfo_sup_02 = self.product_02.seller_ids.filtered(
            lambda s: s.name.id == self.supplier_02.id)
        self.assertEquals(len(supplierinfo_sup_02), 1)
        self.assertEquals(supplierinfo_sup_02.product_name, 'supplier_name_02')
        self.assertEquals(supplierinfo_sup_02.product_code, 'supplier_code_02')
        self.assertEquals(supplierinfo_sup_02.min_qty, 5)
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
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.product_01.seller_ids), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 2)
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

    def test_import_write_disordered_columns_ok(self):
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.product_01.product_tmpl_id.id,
            'name': self.supplier_01.id,
            'product_name': 'Supplier name',
            'product_code': 'SUP_CODE',
            'min_qty': 12,
        })
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.product_02.product_tmpl_id.id,
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
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.product_01.seller_ids), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 2)
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
