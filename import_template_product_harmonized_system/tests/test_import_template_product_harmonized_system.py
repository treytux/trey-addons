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

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def get_file_name(self, fname):
        return fname.split('/')[-1:][0]

    def test_import_create_with_origin_country_id_ok(self):
        fname = self.get_sample('sample_new_fields_origin_country_id_ok.xlsx')
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
            '4: The country \'New country\' does not exist, select one '
            'of the available ones.'), wizard.line_ids[0].name)
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
            '4: The country \'New country\' does not exist, select one '
            'of the available ones.'), wizard.line_ids[0].name)
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
        self.assertEquals(product_tmpl_1.origin_country_id.name, 'Spain')
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
        self.assertFalse(product_tmpl_2.origin_country_id)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 0)

    def test_import_write_with_origin_country_id_ok(self):
        country_1 = self.env['res.country'].create({
            'name': 'Test country',
        })
        self.env['product.product'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'default_code': 'PROD1TEST',
            'standard_price': 80,
            'list_price': 100,
            'categ_id': self.categ_1.id,
            'origin_country_id': country_1.id,
        })
        fname = self.get_sample('sample_new_fields_origin_country_id_ok.xlsx')
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
            '4: The country \'New country\' does not exist, select one of '
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
            '4: The country \'New country\' does not exist, select one of '
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
        self.assertEquals(product_tmpl_1.origin_country_id.name, 'Spain')
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
        self.assertFalse(product_tmpl_2.origin_country_id)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 0)

    def test_import_create_with_hs_code_id_ok(self):
        self.env['hs.code'].create({
            'local_code': '847150',
        })
        fname = self.get_sample('sample_new_fields_hs_code_id_ok.xlsx')
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
            '4: The HS code with local code \'123456\' does not exist, '
            'select one of the available ones.'), wizard.line_ids[0].name)
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
            '4: The HS code with local code \'123456\' does not exist, '
            'select one of the available ones.'), wizard.line_ids[0].name)
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
        self.assertEquals(product_tmpl_1.hs_code_id.local_code, '847150')
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
        self.assertFalse(product_tmpl_2.hs_code_id)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 0)

    def test_import_write_with_hs_code_id_ok(self):
        self.env['hs.code'].create({
            'local_code': '847150',
        })
        hs_code_1 = self.env['hs.code'].create({
            'local_code': '111222',
        })
        self.env['product.product'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'default_code': 'PROD1TEST',
            'standard_price': 80,
            'list_price': 100,
            'categ_id': self.categ_1.id,
            'hs_code_id': hs_code_1.id,
        })
        fname = self.get_sample('sample_new_fields_hs_code_id_ok.xlsx')
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
            '4: The HS code with local code \'123456\' does not exist, '
            'select one of the available ones.'), wizard.line_ids[0].name)
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
        wizard.with_context(debug=True).action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(_(
            '4: The HS code with local code \'123456\' does not exist, '
            'select one of the available ones.'), wizard.line_ids[0].name)
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
        self.assertEquals(product_tmpl_1.hs_code_id.local_code, '847150')
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
        self.assertFalse(product_tmpl_2.hs_code_id)
        product_tmpls_3 = self.env['product.template'].search([
            ('name', '=', 'Product 3 test'),
            ('categ_id', '=', categs_2[0].id),
        ])
        self.assertEquals(len(product_tmpls_3), 0)
