# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os

from openerp import _
from openerp.tests.common import TransactionCase


class TestImportTemplateProduct(TransactionCase):

    def setUp(self):
        super(TestImportTemplateProduct, self).setUp()
        self.categ_1 = self.env['product.category'].create({
            'name': 'Categ 1',
        })
        self.categ_1_1 = self.env['product.category'].create({
            'name': 'Categ 1.1',
            'parent_id': self.categ_1.id,
        })
        self.categ_1_1_1 = self.env['product.category'].create({
            'name': 'Categ 1.1.1',
            'parent_id': self.categ_1_1.id,
        })

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def get_file_name(self, fname):
        return fname.split('/')[-1:][0]

    def test_import_create_with_categ_base_no_variants_ok(self):
        fname = self.get_sample('sample_categ_base_no_variants_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        product_tmpl_1 = product_tmpls_1[0]
        self.assertEquals(product_tmpl_1.name, 'Product 1 test')
        self.assertEquals(product_tmpl_1.categ_id.name, 'Categ 1')
        self.assertEquals(product_tmpl_1.type, 'service')
        self.assertEquals(product_tmpl_1.sale_ok, True)
        self.assertEquals(product_tmpl_1.purchase_ok, True)
        self.assertEquals(product_tmpl_1.standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        product_tmpl_2 = product_tmpls_2[0]
        self.assertEquals(product_tmpl_2.name, 'Product 2 test')
        self.assertEquals(product_tmpl_2.categ_id.name, 'Categ 2')
        self.assertEquals(product_tmpl_2.type, 'service')
        self.assertEquals(product_tmpl_2.sale_ok, True)
        self.assertEquals(product_tmpl_2.purchase_ok, True)
        self.assertEquals(product_tmpl_2.standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)

    def test_import_create_with_categ_parent_no_variants_ok(self):
        fname = self.get_sample('sample_categ_parent_no_variants_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1_1_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1_1_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        product_tmpl_1 = product_tmpls_1[0]
        self.assertEquals(product_tmpl_1.name, 'Product 1 test')
        self.assertEquals(product_tmpl_1.categ_id.name, 'Categ 1.1.1')
        self.assertEquals(product_tmpl_1.type, 'service')
        self.assertEquals(product_tmpl_1.sale_ok, True)
        self.assertEquals(product_tmpl_1.purchase_ok, True)
        self.assertEquals(product_tmpl_1.standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        categs_1_1_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 1.1.2'),
            ('parent_id', '=', self.categ_1_1.id),
        ])
        self.assertEquals(len(categs_1_1_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_1_1_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        product_tmpl_2 = product_tmpls_2[0]
        self.assertEquals(product_tmpl_2.name, 'Product 2 test')
        self.assertEquals(product_tmpl_2.categ_id.name, 'Categ 1.1.2')
        self.assertEquals(product_tmpl_2.type, 'service')
        self.assertEquals(product_tmpl_2.sale_ok, True)
        self.assertEquals(product_tmpl_2.purchase_ok, True)
        self.assertEquals(product_tmpl_2.standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)

    def test_import_create_with_categ_base_variants_ok(self):
        fname = self.get_sample('sample_categ_base_variants_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        product_tmpl_1 = product_tmpls_1[0]
        self.assertEquals(len(product_tmpl_1.product_variant_ids), 6)
        self.assertEquals(product_tmpl_1.name, 'Product 1 test')
        self.assertEquals(product_tmpl_1.categ_id.name, 'Categ 1')
        self.assertEquals(product_tmpl_1.type, 'service')
        self.assertEquals(product_tmpl_1.sale_ok, True)
        self.assertEquals(product_tmpl_1.purchase_ok, True)
        self.assertEquals(product_tmpl_1.standard_price, 10.5)
        self.assertEquals(all(
            product_tmpl_1.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_1.product_variant_ids[0].standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        product_tmpl_2 = product_tmpls_2[0]
        self.assertEquals(len(product_tmpl_2.product_variant_ids), 4)
        self.assertEquals(product_tmpl_2.name, 'Product 2 test')
        self.assertEquals(product_tmpl_2.categ_id.name, 'Categ 2')
        self.assertEquals(product_tmpl_2.type, 'service')
        self.assertEquals(product_tmpl_2.sale_ok, True)
        self.assertEquals(product_tmpl_2.purchase_ok, True)
        self.assertEquals(product_tmpl_2.standard_price, 50)
        self.assertEquals(all(
            product_tmpl_2.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_2.product_variant_ids[0].standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)

    def test_import_create_with_categ_parent_variants_ok(self):
        fname = self.get_sample('sample_categ_parent_variants_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1_1_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1_1_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        product_tmpl_1 = product_tmpls_1[0]
        self.assertEquals(len(product_tmpl_1.product_variant_ids), 6)
        self.assertEquals(product_tmpl_1.name, 'Product 1 test')
        self.assertEquals(product_tmpl_1.categ_id.name, 'Categ 1.1.1')
        self.assertEquals(product_tmpl_1.type, 'service')
        self.assertEquals(product_tmpl_1.sale_ok, True)
        self.assertEquals(product_tmpl_1.purchase_ok, True)
        self.assertEquals(product_tmpl_1.standard_price, 10.5)
        self.assertEquals(all(
            product_tmpl_1.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_1.product_variant_ids[0].standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        categs_1_1_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 1.1.2'),
            ('parent_id', '=', self.categ_1_1.id),
        ])
        self.assertEquals(len(categs_1_1_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_1_1_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        product_tmpl_2 = product_tmpls_2[0]
        self.assertEquals(len(product_tmpl_2.product_variant_ids), 4)
        self.assertEquals(product_tmpl_2.name, 'Product 2 test')
        self.assertEquals(product_tmpl_2.categ_id.name, 'Categ 1.1.2')
        self.assertEquals(product_tmpl_2.type, 'service')
        self.assertEquals(product_tmpl_2.sale_ok, True)
        self.assertEquals(product_tmpl_2.purchase_ok, True)
        self.assertEquals(product_tmpl_2.standard_price, 50)
        self.assertEquals(all(
            product_tmpl_2.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_2.product_variant_ids[0].standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)

    def test_import_write_with_categ_base_no_variants_ok(self):
        self.env['product.product'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'default_code': 'PROD1TEST',
            'standard_price': 80,
            'list_price': 100,
            'categ_id': self.categ_1.id,
        })
        fname = self.get_sample('sample_categ_base_no_variants_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        product_tmpl_1 = product_tmpls_1[0]
        self.assertEquals(product_tmpl_1.name, 'Product 1 test')
        self.assertEquals(product_tmpl_1.categ_id.name, 'Categ 1')
        self.assertEquals(product_tmpl_1.type, 'service')
        self.assertEquals(product_tmpl_1.sale_ok, True)
        self.assertEquals(product_tmpl_1.purchase_ok, True)
        self.assertEquals(product_tmpl_1.standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        product_tmpl_2 = product_tmpls_2[0]
        self.assertEquals(product_tmpl_2.name, 'Product 2 test')
        self.assertEquals(product_tmpl_2.categ_id.name, 'Categ 2')
        self.assertEquals(product_tmpl_2.type, 'service')
        self.assertEquals(product_tmpl_2.sale_ok, True)
        self.assertEquals(product_tmpl_2.purchase_ok, True)
        self.assertEquals(product_tmpl_2.standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)

    def test_import_write_with_categ_parent_no_variants_ok(self):
        self.env['product.product'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'default_code': 'PROD1TEST',
            'standard_price': 80,
            'list_price': 100,
            'categ_id': self.categ_1_1_1.id,
        })
        fname = self.get_sample('sample_categ_parent_no_variants_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1_1_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1_1_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        product_tmpl_1 = product_tmpls_1[0]
        self.assertEquals(product_tmpl_1.name, 'Product 1 test')
        self.assertEquals(product_tmpl_1.categ_id.name, 'Categ 1.1.1')
        self.assertEquals(product_tmpl_1.type, 'service')
        self.assertEquals(product_tmpl_1.sale_ok, True)
        self.assertEquals(product_tmpl_1.purchase_ok, True)
        self.assertEquals(product_tmpl_1.standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        categs_1_1_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 1.1.2'),
            ('parent_id', '=', self.categ_1_1.id),
        ])
        self.assertEquals(len(categs_1_1_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_1_1_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        product_tmpl_2 = product_tmpls_2[0]
        self.assertEquals(product_tmpl_2.name, 'Product 2 test')
        self.assertEquals(product_tmpl_2.categ_id.name, 'Categ 1.1.2')
        self.assertEquals(product_tmpl_2.type, 'service')
        self.assertEquals(product_tmpl_2.sale_ok, True)
        self.assertEquals(product_tmpl_2.purchase_ok, True)
        self.assertEquals(product_tmpl_2.standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)

    def test_import_write_with_categ_base_variants_ok(self):
        self.env['product.product'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'default_code': 'PROD1TEST',
            'standard_price': 80,
            'list_price': 100,
            'categ_id': self.categ_1.id,
        })
        fname = self.get_sample('sample_categ_base_variants_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        product_tmpl_1 = product_tmpls_1[0]
        self.assertEquals(len(product_tmpl_1.product_variant_ids), 6)
        self.assertEquals(product_tmpl_1.name, 'Product 1 test')
        self.assertEquals(product_tmpl_1.categ_id.name, 'Categ 1')
        self.assertEquals(product_tmpl_1.type, 'service')
        self.assertEquals(product_tmpl_1.sale_ok, True)
        self.assertEquals(product_tmpl_1.purchase_ok, True)
        self.assertEquals(product_tmpl_1.standard_price, 10.5)
        self.assertEquals(all(
            product_tmpl_1.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_1.product_variant_ids[0].standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        product_tmpl_2 = product_tmpls_2[0]
        self.assertEquals(len(product_tmpl_2.product_variant_ids), 4)
        self.assertEquals(product_tmpl_2.name, 'Product 2 test')
        self.assertEquals(product_tmpl_2.categ_id.name, 'Categ 2')
        self.assertEquals(product_tmpl_2.type, 'service')
        self.assertEquals(product_tmpl_2.sale_ok, True)
        self.assertEquals(product_tmpl_2.purchase_ok, True)
        self.assertEquals(product_tmpl_2.standard_price, 50)
        self.assertEquals(all(
            product_tmpl_2.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_2.product_variant_ids[0].standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)

    def test_import_write_with_categ_parent_variants_ok(self):
        self.env['product.product'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'default_code': 'PROD1TEST',
            'standard_price': 80,
            'list_price': 100,
            'categ_id': self.categ_1_1_1.id,
        })
        fname = self.get_sample('sample_categ_parent_variants_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1_1_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1_1_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        product_tmpl_1 = product_tmpls_1[0]
        self.assertEquals(len(product_tmpl_1.product_variant_ids), 6)
        self.assertEquals(product_tmpl_1.type, 'service')
        self.assertEquals(product_tmpl_1.sale_ok, True)
        self.assertEquals(product_tmpl_1.purchase_ok, True)
        self.assertEquals(product_tmpl_1.standard_price, 10.5)
        self.assertEquals(all(
            product_tmpl_1.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_1.product_variant_ids[0].standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        categs_1_1_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 1.1.2'),
            ('parent_id', '=', self.categ_1_1.id),
        ])
        self.assertEquals(len(categs_1_1_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_1_1_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        product_tmpl_2 = product_tmpls_2[0]
        self.assertEquals(len(product_tmpl_2.product_variant_ids), 4)
        self.assertEquals(product_tmpl_2.name, 'Product 2 test')
        self.assertEquals(product_tmpl_2.categ_id.name, 'Categ 1.1.2')
        self.assertEquals(product_tmpl_2.type, 'service')
        self.assertEquals(product_tmpl_2.sale_ok, True)
        self.assertEquals(product_tmpl_2.purchase_ok, True)
        self.assertEquals(product_tmpl_2.standard_price, 50)
        self.assertEquals(all(
            product_tmpl_2.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_2.product_variant_ids[0].standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)

    def test_import_categ_empty_error(self):
        fname = self.get_sample('sample_categ_empty_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '3: Category None not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The \'categ_id\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[1].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 0)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
        ])
        self.assertEquals(len(product_tmpls_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '3: Category None not found.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The \'categ_id\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[1].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(product_tmpls_1.name, 'Product 1 test')
        self.assertEquals(product_tmpls_1.categ_id.name, 'Categ 1')
        self.assertEquals(product_tmpls_1.type, 'service')
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 1)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        self.assertEquals(product_tmpls_3.name, 'Product 3 test')
        self.assertEquals(product_tmpls_3.categ_id.name, 'Categ 2')
        self.assertEquals(product_tmpls_3.type, 'service')

    def test_import_create_with_attributes_variants_ok(self):
        attr_obj = self.env['product.attribute']
        attr_val_obj = self.env['product.attribute.value']
        attr = attr_obj.create({
            'name': 'Talla',
        })
        attr_val_obj.create({
            'attribute_id': attr.id,
            'name': 'S'
        })
        attr_val_obj.create({
            'attribute_id': attr.id,
            'name': 'M'
        })
        fname = self.get_sample('sample_categ_base_variants_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        product_tmpl_1 = product_tmpls_1[0]
        self.assertEquals(len(product_tmpl_1.product_variant_ids), 6)
        self.assertEquals(product_tmpl_1.name, 'Product 1 test')
        self.assertEquals(product_tmpl_1.categ_id.name, 'Categ 1')
        self.assertEquals(product_tmpl_1.type, 'service')
        self.assertEquals(product_tmpl_1.sale_ok, True)
        self.assertEquals(product_tmpl_1.purchase_ok, True)
        self.assertEquals(product_tmpl_1.standard_price, 10.5)
        self.assertEquals(all(
            product_tmpl_1.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_1.product_variant_ids[0].standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        attr_talla = attr_obj.search([('name', '=', 'Talla')])
        self.assertEquals(len(attr_talla), 1)
        self.assertEquals(len(attr.value_ids), 3)
        attr_val_talla = attr_val_obj.search([
            ('attribute_id', '=', attr_talla.id)])
        self.assertEquals(len(attr_val_talla), 3)
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        product_tmpl_2 = product_tmpls_2[0]
        self.assertEquals(len(product_tmpl_2.product_variant_ids), 4)
        self.assertEquals(product_tmpl_2.name, 'Product 2 test')
        self.assertEquals(product_tmpl_2.categ_id.name, 'Categ 2')
        self.assertEquals(product_tmpl_2.type, 'service')
        self.assertEquals(product_tmpl_2.sale_ok, True)
        self.assertEquals(product_tmpl_2.purchase_ok, True)
        self.assertEquals(product_tmpl_2.standard_price, 50)
        self.assertEquals(all(
            product_tmpl_2.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_2.product_variant_ids[0].standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)
        attr_talla = attr_obj.search([('name', '=', 'Talla')])
        self.assertEquals(len(attr_talla), 1)
        self.assertEquals(len(attr.value_ids), 3)
        attr_val_talla = attr_val_obj.search([
            ('attribute_id', '=', attr_talla.id)])
        self.assertEquals(len(attr_val_talla), 3)

    def test_attr_and_categ_duply_error(self):
        attr_obj = self.env['product.attribute']
        attr_val_obj = self.env['product.attribute.value']
        attr = attr_obj.create({
            'name': 'Talla',
        })
        attr_val_obj.create({
            'attribute_id': attr.id,
            'name': 'S'
        })
        attr_val_obj.create({
            'attribute_id': attr.id,
            'name': 'M'
        })
        attr2 = attr_obj.create({
            'name': 'Talla',
        })
        attr_val_obj.create({
            'attribute_id': attr2.id,
            'name': 'M'
        })
        self.env['product.category'].create({
            'name': 'Categ 1',
        })
        fname = self.get_sample('sample_attr_and_categ_duply_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '2: More than one category found for Categ 1.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '2: More than one attribute found for Talla.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '4: More than one attribute found for Talla.'),
            wizard.line_ids[2].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        categs_3 = self.env['product.category'].search([
            ('name', '=', 'Categ 3'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_3), 0)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
        ])
        self.assertEquals(len(product_tmpls_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '2: More than one category found for Categ 1.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '2: More than one attribute found for Talla.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '4: More than one attribute found for Talla.'),
            wizard.line_ids[2].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(len(product_tmpls_2.product_variant_ids), 1)
        categs_3 = self.env['product.category'].search([
            ('name', '=', 'Categ 3'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_3), 0)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
        ])
        self.assertEquals(len(product_tmpls_3), 0)

    def test_attributte_duply_error(self):
        attr_obj = self.env['product.attribute']
        attr_val_obj = self.env['product.attribute.value']
        attr = attr_obj.create({
            'name': 'Talla',
        })
        attr_val_obj.create({
            'attribute_id': attr.id,
            'name': 'S'
        })
        attr_val_obj.create({
            'attribute_id': attr.id,
            'name': 'M'
        })
        attr2 = attr_obj.create({
            'name': 'Talla',
        })
        attr_val_obj.create({
            'attribute_id': attr2.id,
            'name': 'M'
        })
        fname = self.get_sample('sample_categ_base_variants_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        for line in wizard.line_ids:
            self.assertIn(_('More than one attribute found'), line.name)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        for line in wizard.line_ids:
            self.assertIn(_('More than one attribute found'), line.name)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)

    def test_category_duply_error(self):
        self.env['product.category'].create({
            'name': 'Categ 1',
        })
        fname = self.get_sample('sample_categ_base_variants_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: More than one category found for Categ 1.'),
            wizard.line_ids[0].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        categ_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categ_2), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: More than one category found for Categ 1.'),
            wizard.line_ids[0].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(len(product_tmpls_2.product_variant_ids), 4)

    def test_float_type_errors(self):
        fname = self.get_sample('sample_float_type_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        categ_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categ_2), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(product_tmpls_1.standard_price, 11.11)
        self.assertEquals(product_tmpls_1.list_price, 15.99)
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(product_tmpls_2.standard_price, 50.50)
        self.assertEquals(product_tmpls_2.list_price, 70.70)

    def test_selection_type_errors(self):
        fname = self.get_sample('sample_selection_type_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        categ_1 = self.env['product.category'].search([
            ('name', '=', 'Categ 1'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categ_1), 1)
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: The \'type\' field is required, you must fill it with a valid '
            'value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '5: The \'type\' field is required, you must fill it with a valid '
            'value.'), wizard.line_ids[1].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        categ_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categ_2), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        self.assertEquals(len(product_tmpls_2), 0)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
        ])
        self.assertEquals(len(product_tmpls_3), 0)
        product_tmpls_4 = self.env['product.template'].search([
            ('name', '=', 'Product 4 test'),
        ])
        self.assertEquals(len(product_tmpls_4), 0)
        product_tmpls_5 = self.env['product.template'].search([
            ('name', '=', 'Product 5 test'),
        ])
        self.assertEquals(len(product_tmpls_5), 0)
        product_tmpls_6 = self.env['product.template'].search([
            ('name', '=', 'Product 6 test'),
        ])
        self.assertEquals(len(product_tmpls_6), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: The \'type\' field is required, you must fill it with a valid '
            'value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '5: The \'type\' field is required, you must fill it with a valid '
            'value.'), wizard.line_ids[1].name)

        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(product_tmpls_2.type, 'service')
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        product_tmpls_4 = self.env['product.template'].search([
            ('name', '=', 'Product 4 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_4), 0)
        product_tmpls_5 = self.env['product.template'].search([
            ('name', '=', 'Product 5 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_5), 1)
        self.assertEquals(product_tmpls_5.purchase_ok, True)
        product_tmpls_6 = self.env['product.template'].search([
            ('name', '=', 'Product 6 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_6), 1)
        self.assertEquals(product_tmpls_6.purchase_ok, False)

    def test_new_fields_ok(self):
        fname = self.get_sample('sample_new_fields_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        categ_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categ_2), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
        ])
        self.assertEquals(len(product_tmpls_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertIn(_(
            'Description for prod 1.'), product_tmpls_1.description_sale)
        self.assertEquals(product_tmpls_1.weight, 0)
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertIn(_(
            'Description for prod 2.'), product_tmpls_2.description_sale)
        self.assertEquals(product_tmpls_2.weight, 10)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        self.assertEquals(product_tmpls_3.description_sale, '')
        self.assertEquals(product_tmpls_3.weight, 20)

    def test_new_fields_error(self):
        fname = self.get_sample('sample_new_fields_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 6)
        self.assertIn(_(
            '2: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: The \'packaging_ids\' column is a relational field and there '
            'is no defined function to convert it.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '3: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '3: The \'packaging_ids\' column is a relational field and there '
            'is no defined function to convert it.'), wizard.line_ids[3].name)
        self.assertIn(_(
            '4: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.'), wizard.line_ids[4].name)
        self.assertIn(_(
            '4: The \'packaging_ids\' column is a relational field and there '
            'is no defined function to convert it.'), wizard.line_ids[5].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        categ_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categ_2), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
        ])
        self.assertEquals(len(product_tmpls_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 6)
        self.assertIn(_(
            '2: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '2: The \'packaging_ids\' column is a relational field and there '
            'is no defined function to convert it.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '3: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '3: The \'packaging_ids\' column is a relational field and there '
            'is no defined function to convert it.'), wizard.line_ids[3].name)
        self.assertIn(_(
            '4: The \'company_id\' column is a relational field and there is '
            'no defined function to convert it.'), wizard.line_ids[4].name)
        self.assertIn(_(
            '4: The \'packaging_ids\' column is a relational field and there '
            'is no defined function to convert it.'), wizard.line_ids[5].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
        ])
        self.assertEquals(len(product_tmpls_3), 0)

    def test_new_fields_ean_ok(self):
        fname = self.get_sample('sample_new_fields_ean_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        categ_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categ_2), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
        ])
        self.assertEquals(len(product_tmpls_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertIn(_(
            'Description for prod 1.'), product_tmpls_1.description_sale)
        self.assertEquals(product_tmpls_1.weight, 0)
        self.assertEquals(product_tmpls_1.ean13, '9735940564824')
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertIn(_(
            'Description for prod 2.'), product_tmpls_2.description_sale)
        self.assertEquals(product_tmpls_2.weight, 10)
        self.assertEquals(product_tmpls_2.ean13, False)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        self.assertEquals(product_tmpls_3.description_sale, '')
        self.assertEquals(product_tmpls_3.weight, 20)
        self.assertEquals(product_tmpls_3.ean13, '7501031311309')

    def test_new_fields_ean_duply_no_error(self):
        self.env['product.template'].create({
            'name': 'Pt duply ean',
            'ean13': '7501031311309',
        })
        fname = self.get_sample('sample_new_fields_ean_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        categ_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categ_2), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
        ])
        self.assertEquals(len(product_tmpls_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertIn(_(
            'Description for prod 1.'), product_tmpls_1.description_sale)
        self.assertEquals(product_tmpls_1.weight, 0)
        self.assertEquals(product_tmpls_1.ean13, '9735940564824')
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertIn(_(
            'Description for prod 2.'), product_tmpls_2.description_sale)
        self.assertEquals(product_tmpls_2.weight, 10)
        self.assertEquals(product_tmpls_2.ean13, False)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        self.assertEquals(product_tmpls_3.description_sale, '')
        self.assertEquals(product_tmpls_3.weight, 20)
        self.assertEquals(product_tmpls_3.ean13, '7501031311309')

    def test_new_fields_ean_error(self):
        self.env['product.template'].create({
            'name': 'Pt duply ean',
            'ean13': '7501031311309',
        })
        fname = self.get_sample('sample_new_fields_ean_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        categ_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categ_2), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
        ])
        self.assertEquals(len(product_tmpls_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'orm_error')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '2: (\'ValidateError\', u\'Field(s) `ean13` failed against a '
            'constraint: You provided an invalid "EAN13 Barcode" reference. '
            'You may use the "Internal Reference" field instead.\')'),
            wizard.line_ids[0].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertIn(_(
            'Description for prod 2.'), product_tmpls_2.description_sale)
        self.assertEquals(product_tmpls_2.weight, 10)
        self.assertEquals(product_tmpls_2.ean13, False)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        self.assertEquals(product_tmpls_3.description_sale, '')
        self.assertEquals(product_tmpls_3.weight, 20)
        self.assertEquals(product_tmpls_3.ean13, '7501031311309')

    def test_new_fields_uom_empty_error(self):
        fname = self.get_sample('sample_new_fields_uom_empty_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 4)
        self.assertIn(_('3: Uom None not found.'), wizard.line_ids[0].name)
        self.assertIn(_('3: Uom None not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '3: The \'uom_id\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '3: The \'uom_po_id\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[3].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        categ_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categ_2), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
        ])
        self.assertEquals(len(product_tmpls_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 4)
        self.assertIn(_('3: Uom None not found.'), wizard.line_ids[0].name)
        self.assertIn(_('3: Uom None not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '3: The \'uom_id\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '3: The \'uom_po_id\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[3].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertIn(_(
            'Description for prod 1.'), product_tmpls_1.description_sale)
        self.assertEquals(product_tmpls_1.weight, 0)
        self.assertEquals(product_tmpls_1.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.uom_po_id.name, 'Unit(s)')
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        self.assertEquals(product_tmpls_3.description_sale, '')
        self.assertEquals(product_tmpls_3.weight, 20)
        self.assertEquals(product_tmpls_3.uom_id.name, 'cm')
        self.assertEquals(product_tmpls_3.uom_po_id.name, 'm')

    def test_new_fields_uom_not_exist_error(self):
        fname = self.get_sample('sample_new_fields_uom_not_exist_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 4)
        self.assertIn(_(
            '3: The unit of measure \'new_unit1\' does not exist, select one '
            'of the available ones.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The unit of measure \'new_unit2\' does not exist, select one '
            'of the available ones.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '3: The \'uom_id\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '3: The \'uom_po_id\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[3].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        categ_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categ_2), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
        ])
        self.assertEquals(len(product_tmpls_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 4)
        self.assertIn(_(
            '3: The unit of measure \'new_unit1\' does not exist, select one '
            'of the available ones.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The unit of measure \'new_unit2\' does not exist, select one '
            'of the available ones.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '3: The \'uom_id\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '3: The \'uom_po_id\' field is required, you must fill it with a '
            'valid value.'), wizard.line_ids[3].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertIn(_(
            'Description for prod 1.'), product_tmpls_1.description_sale)
        self.assertEquals(product_tmpls_1.weight, 0)
        self.assertEquals(product_tmpls_1.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.uom_po_id.name, 'Unit(s)')
        categs_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categs_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        self.assertEquals(product_tmpls_3.description_sale, '')
        self.assertEquals(product_tmpls_3.weight, 20)
        self.assertEquals(product_tmpls_3.uom_id.name, 'cm')
        self.assertEquals(product_tmpls_3.uom_po_id.name, 'm')

    def test_import_create_disordered_columns_ok(self):
        fname = self.get_sample('sample_disordered_columns.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1_1_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1_1_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        product_tmpl_1 = product_tmpls_1[0]
        self.assertEquals(len(product_tmpl_1.product_variant_ids), 6)
        self.assertEquals(product_tmpl_1.name, 'Product 1 test')
        self.assertEquals(product_tmpl_1.categ_id.name, 'Categ 1.1.1')
        self.assertEquals(product_tmpl_1.type, 'service')
        self.assertEquals(product_tmpl_1.sale_ok, True)
        self.assertEquals(product_tmpl_1.purchase_ok, True)
        self.assertEquals(product_tmpl_1.standard_price, 10.5)
        self.assertEquals(all(
            product_tmpl_1.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_1.product_variant_ids[0].standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        categs_1_1_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 1.1.2'),
            ('parent_id', '=', self.categ_1_1.id),
        ])
        self.assertEquals(len(categs_1_1_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_1_1_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        product_tmpl_2 = product_tmpls_2[0]
        self.assertEquals(len(product_tmpl_2.product_variant_ids), 4)
        self.assertEquals(product_tmpl_2.name, 'Product 2 test')
        self.assertEquals(product_tmpl_2.categ_id.name, 'Categ 1.1.2')
        self.assertEquals(product_tmpl_2.type, 'service')
        self.assertEquals(product_tmpl_2.sale_ok, True)
        self.assertEquals(product_tmpl_2.purchase_ok, True)
        self.assertEquals(product_tmpl_2.standard_price, 50)
        self.assertEquals(all(
            product_tmpl_2.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_2.product_variant_ids[0].standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)

    def test_import_write_disordered_columns_ok(self):
        self.env['product.product'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'default_code': 'PROD1TEST',
            'standard_price': 80,
            'list_price': 100,
            'categ_id': self.categ_1_1_1.id,
        })
        fname = self.get_sample('sample_disordered_columns.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1_1_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 2)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1_1_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        product_tmpl_1 = product_tmpls_1[0]
        self.assertEquals(len(product_tmpl_1.product_variant_ids), 6)
        self.assertEquals(product_tmpl_1.type, 'service')
        self.assertEquals(product_tmpl_1.sale_ok, True)
        self.assertEquals(product_tmpl_1.purchase_ok, True)
        self.assertEquals(product_tmpl_1.standard_price, 10.5)
        self.assertEquals(all(
            product_tmpl_1.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_1.product_variant_ids[0].standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        categs_1_1_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 1.1.2'),
            ('parent_id', '=', self.categ_1_1.id),
        ])
        self.assertEquals(len(categs_1_1_2), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', categs_1_1_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        product_tmpl_2 = product_tmpls_2[0]
        self.assertEquals(len(product_tmpl_2.product_variant_ids), 4)
        self.assertEquals(product_tmpl_2.name, 'Product 2 test')
        self.assertEquals(product_tmpl_2.categ_id.name, 'Categ 1.1.2')
        self.assertEquals(product_tmpl_2.type, 'service')
        self.assertEquals(product_tmpl_2.sale_ok, True)
        self.assertEquals(product_tmpl_2.purchase_ok, True)
        self.assertEquals(product_tmpl_2.standard_price, 50)
        self.assertEquals(all(
            product_tmpl_2.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_2.product_variant_ids[0].standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)
