###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os

from odoo import _
from odoo.tests.common import TransactionCase


class TestImportTemplateProduct(TransactionCase):

    def setUp(self):
        super().setUp()
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
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        self.assertTrue(product_tmpl_1.image)
        self.assertTrue(product_tmpl_1.product_image_ids)
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
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertFalse(product_tmpl_2.image)
        self.assertFalse(product_tmpl_2.product_image_ids)

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
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        self.assertTrue(product_tmpl_1.image)
        self.assertTrue(product_tmpl_1.product_image_ids)
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
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertFalse(product_tmpl_2.image)
        self.assertFalse(product_tmpl_2.product_image_ids)

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
        self.assertEquals(product_tmpl_1.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_1.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_1.product_variant_ids[0].standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        self.assertTrue(product_tmpl_1.image)
        self.assertTrue(product_tmpl_1.product_image_ids)
        for product in product_tmpl_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['Blanco', 'S']:
                self.assertFalse(product.image_variant)
            else:
                self.assertTrue(product.image_variant)
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
        self.assertEquals(product_tmpl_2.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_2.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_2.product_variant_ids[0].standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertFalse(product_tmpl_2.image)
        self.assertFalse(product_tmpl_2.product_image_ids)

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
        self.assertEquals(product_tmpl_1.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_1.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_1.product_variant_ids[0].standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        self.assertTrue(product_tmpl_1.image)
        self.assertTrue(product_tmpl_1.product_image_ids)
        for product in product_tmpl_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['Blanco', 'S']:
                self.assertFalse(product.image_variant)
            else:
                self.assertTrue(product.image_variant)
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
        self.assertEquals(product_tmpl_2.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_2.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_2.product_variant_ids[0].standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertFalse(product_tmpl_2.image)
        self.assertFalse(product_tmpl_2.product_image_ids)

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
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        self.assertTrue(product_tmpl_1.image)
        self.assertTrue(product_tmpl_1.product_image_ids)
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
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertFalse(product_tmpl_2.image)
        self.assertFalse(product_tmpl_2.product_image_ids)

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
        self.assertFalse(product_tmpls_1.image)
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
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        self.assertTrue(product_tmpl_1.image)
        self.assertTrue(product_tmpl_1.product_image_ids)
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
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertFalse(product_tmpl_2.image)
        self.assertFalse(product_tmpl_2.product_image_ids)

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
        self.assertFalse(product_tmpls_1.image)
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
        self.assertEquals(product_tmpl_1.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_1.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_1.product_variant_ids[0].standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        self.assertTrue(product_tmpl_1.image)
        self.assertTrue(product_tmpl_1.product_image_ids)
        for product in product_tmpl_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['Blanco', 'S']:
                self.assertFalse(product.image_variant)
            else:
                self.assertTrue(product.image_variant)
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
        self.assertEquals(product_tmpl_2.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_2.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_2.product_variant_ids[0].standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertFalse(product_tmpl_2.image)
        self.assertFalse(product_tmpl_2.product_image_ids)

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
        self.assertFalse(product_tmpls_1.image)
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
        self.assertEquals(product_tmpl_1.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_1.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_1.product_variant_ids[0].standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        categs_1_1_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 1.1.2'),
            ('parent_id', '=', self.categ_1_1.id),
        ])
        self.assertEquals(len(categs_1_1_2), 1)
        self.assertTrue(product_tmpl_1.image)
        self.assertTrue(product_tmpl_1.product_image_ids)
        for product in product_tmpl_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['Blanco', 'S']:
                self.assertFalse(product.image_variant)
            else:
                self.assertTrue(product.image_variant)
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
        self.assertEquals(product_tmpl_2.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_2.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_2.product_variant_ids[0].standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertFalse(product_tmpl_2.image)
        self.assertFalse(product_tmpl_2.product_image_ids)

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
        self.assertEquals(product_tmpl_1.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_1.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_1.product_variant_ids[0].standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        attr_talla = attr_obj.search([('name', '=', 'Talla')])
        self.assertEquals(len(attr_talla), 1)
        self.assertEquals(len(attr.value_ids), 3)
        attr_val_talla = attr_val_obj.search([
            ('attribute_id', '=', attr_talla.id)])
        self.assertEquals(len(attr_val_talla), 3)
        self.assertTrue(product_tmpl_1.image)
        self.assertTrue(product_tmpl_1.product_image_ids)
        for product in product_tmpl_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['Blanco', 'S']:
                self.assertFalse(product.image_variant)
            else:
                self.assertTrue(product.image_variant)
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
        self.assertEquals(product_tmpl_2.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_2.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_2.product_variant_ids[0].standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        attr_talla = attr_obj.search([('name', '=', 'Talla')])
        self.assertEquals(len(attr_talla), 1)
        self.assertEquals(len(attr.value_ids), 3)
        attr_val_talla = attr_val_obj.search([
            ('attribute_id', '=', attr_talla.id)])
        self.assertEquals(len(attr_val_talla), 3)
        self.assertFalse(product_tmpl_2.image)
        self.assertFalse(product_tmpl_2.product_image_ids)

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
        self.assertEquals(wizard.total_rows, 7)
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
        self.assertEquals(wizard.total_rows, 7)
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
        product_tmpls_7 = self.env['product.template'].search([
            ('name', '=', 'Product 7 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_7), 1)
        self.assertEquals(product_tmpls_7.invoice_policy, 'order')

    def test_import_create_new_fields_no_variants_ok(self):
        fname = self.get_sample('sample_new_fields_no_variants_ok.xlsx')
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
        self.assertEquals(product_tmpls_1.product_variant_id.weight, 0)
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
        self.assertEquals(product_tmpls_2.product_variant_id.weight, 10)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        self.assertEquals(product_tmpls_3.description_sale, '')
        self.assertEquals(product_tmpls_3.weight, 20)
        self.assertEquals(product_tmpls_3.product_variant_id.weight, 20)

    def test_import_write_new_fields_variants_ok(self):
        self.env['product.product'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'default_code': 'PROD1TEST',
            'standard_price': 80,
            'list_price': 100,
            'categ_id': self.categ_1_1_1.id,
            'weight': 33,
        })
        self.env['product.product'].create({
            'name': 'Product 2 test',
            'type': 'service',
            'default_code': 'PROD2TEST',
            'standard_price': 80,
            'list_price': 100,
            'categ_id': self.categ_1_1_1.id,
            'weight': 44,
        })
        self.env['product.product'].create({
            'name': 'Product 3 test',
            'type': 'service',
            'default_code': 'PROD3TEST',
            'standard_price': 80,
            'list_price': 100,
            'categ_id': self.categ_1_1_1.id,
        })
        fname = self.get_sample('sample_new_fields_variants_ok.xlsx')
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
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        categ_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categ_2), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
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
        for variant in product_tmpls_1.product_variant_ids:
            self.assertEquals(variant.weight, 0)
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
        self.assertEquals(product_tmpls_2.weight, 0)
        for variant in product_tmpls_2.product_variant_ids:
            self.assertEquals(variant.weight, 10)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        self.assertEquals(product_tmpls_3.description_sale, '')
        self.assertEquals(product_tmpls_3.weight, 0)
        for variant in product_tmpls_3.product_variant_ids:
            self.assertEquals(variant.weight, 20)

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

    def test_new_fields_ean_create_ok(self):
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
        self.assertEquals(product_tmpls_1.product_variant_id.weight, 0)
        self.assertEquals(product_tmpls_1.barcode, '1234')
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
        self.assertEquals(product_tmpls_2.product_variant_id.weight, 10)
        self.assertEquals(product_tmpls_2.barcode, False)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        self.assertEquals(product_tmpls_3.description_sale, '')
        self.assertEquals(product_tmpls_3.weight, 20)
        self.assertEquals(product_tmpls_3.product_variant_id.weight, 20)
        self.assertEquals(product_tmpls_3.barcode, '7501031311309')

    def test_new_fields_ean_write_ok(self):
        self.env['product.product'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'default_code': 'PROD1TEST',
            'standard_price': 80,
            'list_price': 100,
            'categ_id': self.categ_1.id,
        })
        self.env['product.product'].create({
            'name': 'Product 2 test',
            'type': 'service',
            'default_code': 'PROD2TEST',
            'standard_price': 80,
            'list_price': 100,
            'categ_id': self.categ_1.id,
            'barcode': '',
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
        self.assertEquals(len(product_tmpls_1), 1)
        categ_2 = self.env['product.category'].search([
            ('name', '=', 'Categ 2'),
            ('parent_id', '=', None),
        ])
        self.assertEquals(len(categ_2), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
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
        self.assertEquals(product_tmpls_1.product_variant_id.weight, 0)
        self.assertEquals(product_tmpls_1.barcode, '1234')
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
        self.assertEquals(product_tmpls_2.product_variant_id.weight, 10)
        self.assertEquals(product_tmpls_2.barcode, '')
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        self.assertEquals(product_tmpls_3.description_sale, '')
        self.assertEquals(product_tmpls_3.weight, 20)
        self.assertEquals(product_tmpls_3.product_variant_id.weight, 20)
        self.assertEquals(product_tmpls_3.barcode, '7501031311309')

    def test_new_fields_ean_duply_error(self):
        self.env['product.template'].create({
            'name': 'Pt duply ean',
            'barcode': '7501031311309',
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
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            'Key (barcode)=(7501031311309) already exists.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '4: duplicate key value violates unique constraint '
            '"product_product_barcode_uniq"'), wizard.line_ids[0].name)
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
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            'Key (barcode)=(7501031311309) already exists.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '4: duplicate key value violates unique constraint '
            '"product_product_barcode_uniq"'), wizard.line_ids[0].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertIn(_(
            'Description for prod 1.'), product_tmpls_1.description_sale)
        self.assertEquals(product_tmpls_1.weight, 0)
        self.assertEquals(product_tmpls_1.product_variant_id.weight, 0)
        self.assertEquals(product_tmpls_1.barcode, '1234')
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
        self.assertEquals(product_tmpls_2.product_variant_id.weight, 10)
        self.assertEquals(product_tmpls_2.barcode, False)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 0)

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
        self.assertEquals(product_tmpls_1.product_variant_id.weight, 0)
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
        self.assertEquals(product_tmpls_3.product_variant_id.weight, 20)
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
        self.assertEquals(product_tmpls_1.product_variant_id.weight, 0)
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
        self.assertEquals(product_tmpls_3.product_variant_id.weight, 20)
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
        self.assertEquals(product_tmpl_1.standard_price, 0)
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
        self.assertEquals(product_tmpl_2.standard_price, 0)
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
        self.assertEquals(product_tmpl_1.standard_price, 0)
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
        self.assertEquals(product_tmpl_2.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_2.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_2.product_variant_ids[0].standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)

    def test_import_create_with_brand_ok(self):
        self.env['product.brand'].create({
            'name': 'Brand 1',
        })
        fname = self.get_sample('sample_brand_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '4: The product brand \'New brand\' does not exist, select one of '
            'the available ones.'), wizard.line_ids[0].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
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
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '4: The product brand \'New brand\' does not exist, select one of '
            'the available ones.'), wizard.line_ids[0].name)
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
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        self.assertFalse(product_tmpl_1.product_brand_id.exists())
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
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertEquals(product_tmpl_2.product_brand_id.name, 'Brand 1')
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 0)

    def test_import_write_with_brand_ok(self):
        brand_1 = self.env['product.brand'].create({
            'name': 'Brand 1',
        })
        self.env['product.product'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'default_code': 'PROD1TEST',
            'standard_price': 80,
            'list_price': 100,
            'categ_id': self.categ_1.id,
            'product_brand_id': brand_1.id,
        })
        fname = self.get_sample('sample_brand_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '4: The product brand \'New brand\' does not exist, select one of '
            'the available ones.'), wizard.line_ids[0].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
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
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '4: The product brand \'New brand\' does not exist, select one of '
            'the available ones.'), wizard.line_ids[0].name)
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
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        self.assertFalse(product_tmpl_1.product_brand_id.exists())
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
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertEquals(product_tmpl_2.product_brand_id.name, 'Brand 1')
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 0)

    def test_image_error_create_ok(self):
        fname = self.get_sample('sample_image_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 4)
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
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
        ])
        self.assertEquals(len(product_tmpls_3), 0)
        product_tmpls_4 = self.env['product.template'].search([
            ('name', '=', 'Product 4 test'),
        ])
        self.assertEquals(len(product_tmpls_4), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 4)
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
        self.assertEquals(product_tmpl_1.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_1.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_1.product_variant_ids[0].standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        self.assertFalse(product_tmpl_1.image)
        self.assertFalse(product_tmpl_1.product_image_ids)
        for product in product_tmpl_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['Blanco', 'S']:
                self.assertFalse(product.image_variant)
            else:
                self.assertTrue(product.image_variant)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        product_tmpl_2 = product_tmpls_2[0]
        self.assertEquals(len(product_tmpl_2.product_variant_ids), 4)
        self.assertEquals(product_tmpl_2.name, 'Product 2 test')
        self.assertEquals(product_tmpl_2.categ_id.name, 'Categ 1')
        self.assertEquals(product_tmpl_2.type, 'service')
        self.assertEquals(product_tmpl_2.sale_ok, True)
        self.assertEquals(product_tmpl_2.purchase_ok, True)
        self.assertEquals(product_tmpl_2.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_2.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_2.product_variant_ids[0].standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertTrue(product_tmpl_2.image)
        self.assertTrue(product_tmpl_2.product_image_ids)
        for product in product_tmpl_2.product_variant_ids:
            self.assertFalse(product.image_variant)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        product_tmpl_3 = product_tmpls_3[0]
        self.assertEquals(len(product_tmpl_3.product_variant_ids), 1)
        self.assertEquals(product_tmpl_3.name, 'Product 3 test')
        self.assertEquals(product_tmpl_3.categ_id.name, 'Categ 1')
        self.assertEquals(product_tmpl_3.type, 'service')
        self.assertEquals(product_tmpl_3.sale_ok, True)
        self.assertEquals(product_tmpl_3.purchase_ok, True)
        self.assertEquals(product_tmpl_3.standard_price, 100)
        self.assertEquals(product_tmpl_3.list_price, 150)
        self.assertEquals(product_tmpl_3.invoice_policy, 'order')
        self.assertTrue(product_tmpl_3.image)
        self.assertTrue(product_tmpl_3.product_image_ids)
        product_tmpls_4 = self.env['product.template'].search([
            ('name', '=', 'Product 4 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_4), 1)
        product_tmpl_4 = product_tmpls_4[0]
        self.assertEquals(len(product_tmpl_4.product_variant_ids), 4)
        self.assertEquals(product_tmpl_4.name, 'Product 4 test')
        self.assertEquals(product_tmpl_4.categ_id.name, 'Categ 1')
        self.assertEquals(product_tmpl_4.type, 'service')
        self.assertEquals(product_tmpl_4.sale_ok, True)
        self.assertEquals(product_tmpl_4.purchase_ok, True)
        self.assertEquals(product_tmpl_4.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_4.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_4.product_variant_ids[0].standard_price, 100)
        self.assertEquals(product_tmpl_4.list_price, 150)
        self.assertEquals(product_tmpl_4.invoice_policy, 'order')
        self.assertTrue(product_tmpl_4.image)
        self.assertTrue(product_tmpl_4.product_image_ids)
        for product in product_tmpl_4.product_variant_ids:
            self.assertFalse(product.image_variant)

    def test_image_error_write_ok(self):
        self.env['product.product'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'default_code': 'PROD1TEST',
            'standard_price': 80,
            'list_price': 100,
            'categ_id': self.categ_1.id,
        })
        self.env['product.product'].create({
            'name': 'Product 2 test',
            'type': 'service',
            'default_code': 'PROD2TEST',
            'standard_price': 80,
            'list_price': 100,
            'categ_id': self.categ_1.id,
        })
        self.env['product.product'].create({
            'name': 'Product 3 test',
            'type': 'service',
            'default_code': 'PROD3TEST',
            'standard_price': 80,
            'list_price': 100,
            'categ_id': self.categ_1.id,
        })
        self.env['product.product'].create({
            'name': 'Product 4 test',
            'type': 'service',
            'default_code': 'PROD4TEST',
            'standard_price': 80,
            'list_price': 100,
            'categ_id': self.categ_1.id,
        })
        fname = self.get_sample('sample_image_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 4)
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
        self.assertEquals(len(product_tmpls_2), 1)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        product_tmpls_4 = self.env['product.template'].search([
            ('name', '=', 'Product 4 test'),
        ])
        self.assertEquals(len(product_tmpls_4), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 4)
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
        self.assertEquals(product_tmpl_1.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_1.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_1.product_variant_ids[0].standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        self.assertFalse(product_tmpl_1.image)
        self.assertFalse(product_tmpl_1.product_image_ids)
        for product in product_tmpl_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['Blanco', 'S']:
                self.assertFalse(product.image_variant)
            else:
                self.assertTrue(product.image_variant)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        product_tmpl_2 = product_tmpls_2[0]
        self.assertEquals(len(product_tmpl_2.product_variant_ids), 4)
        self.assertEquals(product_tmpl_2.name, 'Product 2 test')
        self.assertEquals(product_tmpl_2.categ_id.name, 'Categ 1')
        self.assertEquals(product_tmpl_2.type, 'service')
        self.assertEquals(product_tmpl_2.sale_ok, True)
        self.assertEquals(product_tmpl_2.purchase_ok, True)
        self.assertEquals(product_tmpl_2.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_2.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_2.product_variant_ids[0].standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertTrue(product_tmpl_2.image)
        self.assertTrue(product_tmpl_2.product_image_ids)
        for product in product_tmpl_2.product_variant_ids:
            self.assertFalse(product.image_variant)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        product_tmpl_3 = product_tmpls_3[0]
        self.assertEquals(len(product_tmpl_3.product_variant_ids), 1)
        self.assertEquals(product_tmpl_3.name, 'Product 3 test')
        self.assertEquals(product_tmpl_3.categ_id.name, 'Categ 1')
        self.assertEquals(product_tmpl_3.type, 'service')
        self.assertEquals(product_tmpl_3.sale_ok, True)
        self.assertEquals(product_tmpl_3.purchase_ok, True)
        self.assertEquals(product_tmpl_3.standard_price, 100)
        self.assertEquals(product_tmpl_3.list_price, 150)
        self.assertEquals(product_tmpl_3.invoice_policy, 'order')
        self.assertTrue(product_tmpl_3.image)
        self.assertTrue(product_tmpl_3.product_image_ids)
        product_tmpls_4 = self.env['product.template'].search([
            ('name', '=', 'Product 4 test'),
            ('categ_id', '=', self.categ_1.id),
        ])
        self.assertEquals(len(product_tmpls_4), 1)
        product_tmpl_4 = product_tmpls_4[0]
        self.assertEquals(len(product_tmpl_4.product_variant_ids), 4)
        self.assertEquals(product_tmpl_4.name, 'Product 4 test')
        self.assertEquals(product_tmpl_4.categ_id.name, 'Categ 1')
        self.assertEquals(product_tmpl_4.type, 'service')
        self.assertEquals(product_tmpl_4.sale_ok, True)
        self.assertEquals(product_tmpl_4.purchase_ok, True)
        self.assertEquals(product_tmpl_4.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_4.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_4.product_variant_ids[0].standard_price, 100)
        self.assertEquals(product_tmpl_4.list_price, 150)
        self.assertEquals(product_tmpl_4.invoice_policy, 'order')
        self.assertTrue(product_tmpl_4.image)
        self.assertTrue(product_tmpl_4.product_image_ids)
        for product in product_tmpl_4.product_variant_ids:
            self.assertFalse(product.image_variant)

    def test_import_two_files_write_existent_product_tmpl_no_variants(self):
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
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        self.assertTrue(product_tmpl_1.image)
        self.assertTrue(product_tmpl_1.product_image_ids)
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
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertFalse(product_tmpl_2.image)
        self.assertFalse(product_tmpl_2.product_image_ids)
        fname2 = self.get_sample('sample_categ_base_variants_ok.xlsx')
        file2 = base64.b64encode(open(fname2, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file2,
            'file_filename': self.get_file_name(fname2),
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
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('name', '=', 'Product 2 test'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(len(product_tmpls_2.product_variant_ids), 1)
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
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 6)
        self.assertEquals(product_tmpl_1.name, 'Product 1 test')
        self.assertEquals(product_tmpl_1.categ_id.name, 'Categ 1')
        self.assertEquals(product_tmpl_1.type, 'service')
        self.assertEquals(product_tmpl_1.sale_ok, True)
        self.assertEquals(product_tmpl_1.purchase_ok, True)
        self.assertEquals(product_tmpl_1.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_1.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_1.product_variant_ids[0].standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        self.assertTrue(product_tmpl_1.image)
        self.assertTrue(product_tmpl_1.product_image_ids)
        for product in product_tmpl_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['Blanco', 'S']:
                self.assertFalse(product.image_variant)
            else:
                self.assertTrue(product.image_variant)
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
        self.assertEquals(product_tmpl_2.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_2.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_2.product_variant_ids[0].standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertFalse(product_tmpl_2.image)
        self.assertFalse(product_tmpl_2.product_image_ids)

    def test_import_two_files_write_existent_product_tmpl_variants(self):
        fname = self.get_sample('sample_categ_base_variants_ok2.xlsx')
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
        product_tmpl_1 = product_tmpls_1[0]
        self.assertEquals(len(product_tmpl_1.product_variant_ids), 6)
        self.assertEquals(product_tmpl_1.name, 'Product 1 test')
        self.assertEquals(product_tmpl_1.categ_id.name, 'Categ 1')
        self.assertEquals(product_tmpl_1.type, 'service')
        self.assertEquals(product_tmpl_1.sale_ok, True)
        self.assertEquals(product_tmpl_1.purchase_ok, True)
        self.assertEquals(product_tmpl_1.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_1.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_1.product_variant_ids[0].standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        self.assertTrue(product_tmpl_1.image)
        self.assertTrue(product_tmpl_1.product_image_ids)
        for product in product_tmpl_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['Blanco', 'S']:
                self.assertFalse(product.image_variant)
            else:
                self.assertTrue(product.image_variant)
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
        self.assertEquals(product_tmpl_2.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_2.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_2.product_variant_ids[0].standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertFalse(product_tmpl_2.image)
        self.assertFalse(product_tmpl_2.product_image_ids)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        product_tmpl_3 = product_tmpls_3[0]
        self.assertEquals(len(product_tmpl_3.product_variant_ids), 4)
        self.assertEquals(product_tmpl_3.name, 'Product 3 test')
        self.assertEquals(product_tmpl_3.categ_id.name, 'Categ 2')
        self.assertEquals(product_tmpl_3.type, 'service')
        self.assertEquals(product_tmpl_3.sale_ok, True)
        self.assertEquals(product_tmpl_3.purchase_ok, True)
        self.assertEquals(product_tmpl_3.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_3.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_3.product_variant_ids[0].standard_price, 20)
        self.assertEquals(product_tmpl_3.list_price, 30)
        self.assertEquals(product_tmpl_3.invoice_policy, 'order')
        self.assertTrue(product_tmpl_3.image)
        self.assertTrue(product_tmpl_3.product_image_ids)
        for product in product_tmpl_3.product_variant_ids:
            if product.attribute_value_ids.mapped(
                    'name') in (['Azul', 'M'], ['Azul', 'L'], ):
                self.assertFalse(product.image_variant)
            else:
                self.assertTrue(product.image_variant)
        fname2 = self.get_sample('sample_categ_base_variants_ok3.xlsx')
        file2 = base64.b64encode(open(fname2, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product.template_product').id,
            'file': file2,
            'file_filename': self.get_file_name(fname2),
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
        self.assertEquals(len(product_tmpls_1), 1)
        product_tmpl_1 = product_tmpls_1[0]
        self.assertEquals(len(product_tmpl_1.product_variant_ids), 6)
        self.assertEquals(product_tmpl_1.name, 'Product 1 test')
        self.assertEquals(product_tmpl_1.categ_id.name, 'Categ 1')
        self.assertEquals(product_tmpl_1.type, 'service')
        self.assertEquals(product_tmpl_1.sale_ok, True)
        self.assertEquals(product_tmpl_1.purchase_ok, True)
        self.assertEquals(product_tmpl_1.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_1.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_1.product_variant_ids[0].standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        self.assertTrue(product_tmpl_1.image)
        self.assertTrue(product_tmpl_1.product_image_ids)
        for product in product_tmpl_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['Blanco', 'S']:
                self.assertFalse(product.image_variant)
            else:
                self.assertTrue(product.image_variant)
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
        self.assertEquals(product_tmpl_2.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_2.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_2.product_variant_ids[0].standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertFalse(product_tmpl_2.image)
        self.assertFalse(product_tmpl_2.product_image_ids)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        product_tmpl_3 = product_tmpls_3[0]
        self.assertEquals(len(product_tmpl_3.product_variant_ids), 4)
        self.assertEquals(product_tmpl_3.name, 'Product 3 test')
        self.assertEquals(product_tmpl_3.categ_id.name, 'Categ 2')
        self.assertEquals(product_tmpl_3.type, 'service')
        self.assertEquals(product_tmpl_3.sale_ok, True)
        self.assertEquals(product_tmpl_3.purchase_ok, True)
        self.assertEquals(product_tmpl_3.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_3.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_3.product_variant_ids[0].standard_price, 20)
        self.assertEquals(product_tmpl_3.list_price, 30)
        self.assertEquals(product_tmpl_3.invoice_policy, 'order')
        self.assertTrue(product_tmpl_3.image)
        self.assertTrue(product_tmpl_3.product_image_ids)
        for product in product_tmpl_3.product_variant_ids:
            if product.attribute_value_ids.mapped(
                    'name') in (['Azul', 'M'], ['Azul', 'L'], ):
                self.assertFalse(product.image_variant)
            else:
                self.assertTrue(product.image_variant)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 3)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: The product template with default_code \'PROD1TEST\' already '
            'had variant attributes. Review it, they have not been '
            'overwritten.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The product template with default_code \'PROD2TEST\' already '
            'had variant attributes. Review it, they have not been '
            'overwritten.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '4: The product template with default_code \'PROD3TEST\' already '
            'had variant attributes. Review it, they have not been '
            'overwritten.'), wizard.line_ids[2].name)
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
        self.assertEquals(product_tmpl_1.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_1.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_1.product_variant_ids[0].standard_price, 88)
        self.assertEquals(product_tmpl_1.list_price, 99)
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        self.assertTrue(product_tmpl_1.image)
        self.assertTrue(product_tmpl_1.product_image_ids)
        for product in product_tmpl_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['Blanco', 'S']:
                self.assertFalse(product.image_variant)
            else:
                self.assertTrue(product.image_variant)
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
        self.assertEquals(product_tmpl_2.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_2.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_2.product_variant_ids[0].standard_price, 10)
        self.assertEquals(product_tmpl_2.list_price, 20)
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertTrue(product_tmpl_2.image)
        self.assertTrue(product_tmpl_2.product_image_ids)
        for product in product_tmpl_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['Blanco', 'S']:
                self.assertFalse(product.image_variant)
            else:
                self.assertTrue(product.image_variant)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        product_tmpl_3 = product_tmpls_3[0]
        self.assertEquals(len(product_tmpl_3.product_variant_ids), 4)
        self.assertEquals(product_tmpl_3.name, 'Product 3 test')
        self.assertEquals(product_tmpl_3.categ_id.name, 'Categ 2')
        self.assertEquals(product_tmpl_3.type, 'service')
        self.assertEquals(product_tmpl_3.sale_ok, True)
        self.assertEquals(product_tmpl_3.purchase_ok, True)
        self.assertEquals(product_tmpl_3.standard_price, 0)
        self.assertEquals(all(
            product_tmpl_3.product_variant_ids.mapped('standard_price')), True)
        self.assertEquals(
            product_tmpl_3.product_variant_ids[0].standard_price, 66)
        self.assertEquals(product_tmpl_3.list_price, 69)
        self.assertEquals(product_tmpl_3.invoice_policy, 'order')
        self.assertFalse(product_tmpl_3.image)
        self.assertFalse(product_tmpl_3.product_image_ids)
        for product in product_tmpl_3.product_variant_ids:
            self.assertFalse(product.image_variant)

    def test_write_inactive_product_template(self):
        pt_01 = self.env['product.template'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'default_code': 'PROD1TEST',
            'standard_price': 80,
            'list_price': 100,
            'categ_id': self.categ_1.id,
        })
        pt_01.active = False
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
        product_tmpls_1_inactive = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
            ('active', '=', False),
        ])
        self.assertEquals(len(product_tmpls_1_inactive), 1)
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
        product_tmpls_1_inactive = self.env['product.template'].search([
            ('name', '=', 'Product 1 test'),
            ('categ_id', '=', self.categ_1.id),
            ('active', '=', False),
        ])
        self.assertEquals(len(product_tmpls_1_inactive), 1)
        product_tmpl_1_inactive = product_tmpls_1_inactive[0]
        self.assertEquals(product_tmpl_1_inactive.name, 'Product 1 test')
        self.assertEquals(product_tmpl_1_inactive.categ_id.name, 'Categ 1')
        self.assertEquals(product_tmpl_1_inactive.type, 'service')
        self.assertEquals(product_tmpl_1_inactive.sale_ok, True)
        self.assertEquals(product_tmpl_1_inactive.purchase_ok, True)
        self.assertEquals(product_tmpl_1_inactive.standard_price, 10.5)
        self.assertEquals(product_tmpl_1_inactive.list_price, 15.99)
        self.assertEquals(product_tmpl_1_inactive.invoice_policy, 'order')
        self.assertTrue(product_tmpl_1_inactive.image)
        self.assertTrue(product_tmpl_1_inactive.product_image_ids)
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
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertFalse(product_tmpl_2.image)
        self.assertFalse(product_tmpl_2.product_image_ids)

    def test_create_default_code_strip(self):
        fname = self.get_sample('sample_default_code_strip.xlsx')
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
        self.assertEquals(product_tmpl_1.default_code, 'PROD1TEST')
        self.assertEquals(product_tmpl_1.categ_id.name, 'Categ 1')
        self.assertEquals(product_tmpl_1.type, 'service')
        self.assertEquals(product_tmpl_1.sale_ok, True)
        self.assertEquals(product_tmpl_1.purchase_ok, True)
        self.assertEquals(product_tmpl_1.standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        self.assertTrue(product_tmpl_1.image)
        self.assertTrue(product_tmpl_1.product_image_ids)
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
        self.assertEquals(product_tmpl_2.default_code, 'PROD2TEST')
        self.assertEquals(product_tmpl_2.categ_id.name, 'Categ 2')
        self.assertEquals(product_tmpl_2.type, 'service')
        self.assertEquals(product_tmpl_2.sale_ok, True)
        self.assertEquals(product_tmpl_2.purchase_ok, True)
        self.assertEquals(product_tmpl_2.standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertFalse(product_tmpl_2.image)
        self.assertFalse(product_tmpl_2.product_image_ids)

    def test_write_default_code_strip(self):
        self.env['product.product'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'default_code': 'PROD1TEST',
            'standard_price': 80,
            'list_price': 100,
            'categ_id': self.categ_1.id,
        })
        fname = self.get_sample('sample_default_code_strip.xlsx')
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
        self.assertEquals(product_tmpls_1.standard_price, 80)
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
        self.assertEquals(product_tmpl_1.default_code, 'PROD1TEST')
        self.assertEquals(product_tmpl_1.categ_id.name, 'Categ 1')
        self.assertEquals(product_tmpl_1.type, 'service')
        self.assertEquals(product_tmpl_1.sale_ok, True)
        self.assertEquals(product_tmpl_1.purchase_ok, True)
        self.assertEquals(product_tmpl_1.standard_price, 10.5)
        self.assertEquals(product_tmpl_1.list_price, 15.99)
        self.assertEquals(product_tmpl_1.invoice_policy, 'order')
        self.assertTrue(product_tmpl_1.image)
        self.assertTrue(product_tmpl_1.product_image_ids)
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
        self.assertEquals(product_tmpl_2.default_code, 'PROD2TEST')
        self.assertEquals(product_tmpl_2.categ_id.name, 'Categ 2')
        self.assertEquals(product_tmpl_2.type, 'service')
        self.assertEquals(product_tmpl_2.sale_ok, True)
        self.assertEquals(product_tmpl_2.purchase_ok, True)
        self.assertEquals(product_tmpl_2.standard_price, 50)
        self.assertEquals(product_tmpl_2.list_price, 70)
        self.assertEquals(product_tmpl_2.invoice_policy, 'order')
        self.assertFalse(product_tmpl_2.image)
        self.assertFalse(product_tmpl_2.product_image_ids)
