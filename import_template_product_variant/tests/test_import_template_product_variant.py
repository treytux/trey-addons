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
        self.attr_color = self.env['product.attribute'].search([
            ('name', '=', 'Color'),
        ])
        if self.attr_color:
            self.assertEquals(len(self.attr_color), 1)
            self.assertEquals(len(self.attr_color.value_ids), 2)
            color_value_white = self.attr_color.value_ids.filtered(
                lambda v: v.name == 'White')
            self.assertEquals(len(color_value_white), 1)
            color_value_black = self.attr_color.value_ids.filtered(
                lambda v: v.name == 'Black')
            self.assertEquals(len(color_value_black), 1)
        else:
            self.attr_color = self.env['product.attribute'].create({
                'name': 'Color',
            })
            for value in ['White', 'Black']:
                self.env['product.attribute.value'].create({
                    'attribute_id': self.attr_color.id,
                    'name': value,
                })
        self.attr_size = self.env['product.attribute'].search([
            ('name', '=', 'Size'),
        ])
        self.assertEquals(len(self.attr_size), 0)
        self.attr_size = self.env['product.attribute'].create({
            'name': 'Size',
        })
        for value in ['S', 'M', 'L']:
            self.env['product.attribute.value'].create({
                'attribute_id': self.attr_size.id,
                'name': value,
            })
        self.attr_lenght = self.env['product.attribute'].search([
            ('name', '=', 'Lenght'),
        ])
        self.assertEquals(len(self.attr_lenght), 0)
        self.attr_lenght = self.env['product.attribute'].create({
            'name': 'Lenght',
        })
        for value in ['10', '20']:
            self.env['product.attribute.value'].create({
                'attribute_id': self.attr_lenght.id,
                'name': value,
            })
        self.attr_gender = self.env['product.attribute'].create({
            'name': 'Gender',
            'create_variant': 'no_variant',
        })
        for value in ['male', 'female']:
            self.env['product.attribute.value'].create({
                'attribute_id': self.attr_gender.id,
                'name': value,
            })
        self.brand_1 = self.env['product.brand'].create({
            'name': 'Brand 1',
        })

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def get_file_name(self, fname):
        return fname.split('/')[-1:][0]

    def test_product_tmpl_code_unique(self):
        self.env['product.template'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'standard_price': 80,
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPLDUPLY',
        })
        with self.assertRaises(Exception):
            self.env['product.template'].create({
                'name': 'Product 1 duply test',
                'type': 'service',
                'standard_price': 80,
                'list_price': 100,
                'product_tmpl_code': 'PRODTMPLDUPLY',
            })

    def test_import_create_no_product_tmpl_code(self):
        fname = self.get_sample('sample_no_product_tmpl_code.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '2: The \'product_tmpl_code\' field is required, you must fill it '
            'with a valid value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The \'product_tmpl_code\' field is required, you must fill it '
            'with a valid value.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '4: The \'product_tmpl_code\' field is required, you must fill it '
            'with a valid value.'), wizard.line_ids[2].name)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '2: The \'product_tmpl_code\' field is required, you must fill it '
            'with a valid value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The \'product_tmpl_code\' field is required, you must fill it '
            'with a valid value.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '4: The \'product_tmpl_code\' field is required, you must fill it '
            'with a valid value.'), wizard.line_ids[2].name)

    def test_import_write_no_product_tmpl_code(self):
        self.env['product.template'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'list_price': 100,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr_color.id,
                    'value_ids': [(6, 0, self.attr_color.value_ids.ids)],
                }),
                (0, 0, {
                    'attribute_id': self.attr_size.id,
                    'value_ids': [(6, 0, self.attr_size.value_ids.ids)],
                }),
            ],
        })
        fname = self.get_sample('sample_no_product_tmpl_code.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '2: The \'product_tmpl_code\' field is required, you must fill it '
            'with a valid value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The \'product_tmpl_code\' field is required, you must fill it '
            'with a valid value.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '4: The \'product_tmpl_code\' field is required, you must fill it '
            'with a valid value.'), wizard.line_ids[2].name)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '2: The \'product_tmpl_code\' field is required, you must fill it '
            'with a valid value.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: The \'product_tmpl_code\' field is required, you must fill it '
            'with a valid value.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '4: The \'product_tmpl_code\' field is required, you must fill it '
            'with a valid value.'), wizard.line_ids[2].name)

    def test_import_write_same_variants_exists(self):
        pt_01 = self.env['product.template'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL1TEST',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr_color.id,
                    'value_ids': [(6, 0, self.attr_color.value_ids.ids)],
                }),
                (0, 0, {
                    'attribute_id': self.attr_size.id,
                    'value_ids': [(6, 0, self.attr_size.value_ids.ids)],
                }),
            ],
        })
        self.assertEquals(len(pt_01.product_variant_ids), 6)
        fname = self.get_sample('sample_variants_exists.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(product_tmpls_1.name, 'Template 1')
        self.assertEquals(product_tmpls_1.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_1.categ_id.parent_id)
        self.assertEquals(product_tmpls_1.type, 'service')
        self.assertTrue(product_tmpls_1.sale_ok)
        self.assertFalse(product_tmpls_1.purchase_ok)
        self.assertEquals(product_tmpls_1.list_price, 15.99)
        self.assertEquals(product_tmpls_1.invoice_policy, 'delivery')
        self.assertTrue(product_tmpls_1.image)
        self.assertTrue(product_tmpls_1.product_image_ids)
        for product in product_tmpls_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['White', 'S']:
                self.assertTrue(product.image_variant)
            else:
                self.assertFalse(product.image_variant)
        self.assertEquals(
            product_tmpls_1.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_1.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_1.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.product_brand_id, self.brand_1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 6)
        variant_WS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'S'])
        self.assertEquals(len(variant_WS), 1)
        self.assertEquals(variant_WS.default_code, 'PROD1_WS')
        self.assertEquals(variant_WS.barcode, '4050119164021')
        self.assertEquals(variant_WS.standard_price, 10.5)
        variant_WM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'M'])
        self.assertEquals(len(variant_WM), 1)
        self.assertEquals(variant_WM.default_code, 'PROD1_WM')
        self.assertEquals(variant_WM.barcode, '4050119164038')
        self.assertEquals(variant_WM.standard_price, 20)
        variant_WL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'L'])
        self.assertEquals(len(variant_WL), 1)
        self.assertEquals(variant_WL.default_code, 'PROD1_WL')
        self.assertEquals(variant_WL.barcode, '4050119164106')
        self.assertEquals(variant_WL.standard_price, 25)
        variant_BS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'S'])
        self.assertEquals(len(variant_BS), 1)
        self.assertEquals(variant_BS.default_code, 'PROD1_BS')
        self.assertEquals(variant_BS.barcode, '4050119164144')
        self.assertEquals(variant_BS.standard_price, 10)
        variant_BM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'M'])
        self.assertEquals(len(variant_BM), 1)
        self.assertEquals(variant_BM.default_code, 'PROD1_BM')
        self.assertEquals(variant_BM.barcode, '4050119164298')
        self.assertEquals(variant_BM.standard_price, 12)
        variant_BL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'L'])
        self.assertEquals(len(variant_BL), 1)
        self.assertEquals(variant_BL.default_code, 'PROD1_BL')
        self.assertEquals(variant_BL.barcode, '4050119164069')
        self.assertEquals(variant_BL.standard_price, 14)

    def test_import_write_diff_variants_exists(self):
        value_black = self.attr_color.value_ids.filtered(
            lambda v: v.name == 'Black')
        self.assertEquals(len(value_black), 1)
        pt_01 = self.env['product.template'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL1TEST',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr_color.id,
                    'value_ids': [(6, 0, value_black.ids)],
                }),
                (0, 0, {
                    'attribute_id': self.attr_lenght.id,
                    'value_ids': [(6, 0, self.attr_lenght.value_ids.ids)],
                }),
            ],
        })
        self.assertEquals(len(pt_01.product_variant_ids), 2)
        fname = self.get_sample('sample_variants_exists.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 2)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 6)
        msg_error = _(
            'The \'Size\' attribute of the file does not match the '
            'attributes of the product template; you must review it.')
        for i in range(1, wizard.total_error + 1):
            self.assertIn(_(
                '%s: %s' % (i + 1, msg_error)), wizard.line_ids[i - 1].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 2)

    def test_import_write_diff_variants_exists_attribute_no_variant(self):
        value_black = self.attr_color.value_ids.filtered(
            lambda v: v.name == 'Black')
        self.assertEquals(len(value_black), 1)
        pt_01 = self.env['product.template'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL1TEST',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr_color.id,
                    'value_ids': [(6, 0, value_black.ids)],
                }),
                (0, 0, {
                    'attribute_id': self.attr_size.id,
                    'value_ids': [(6, 0, self.attr_size.value_ids.ids)],
                }),
                (0, 0, {
                    'attribute_id': self.attr_gender.id,
                    'value_ids': [(6, 0, self.attr_gender.value_ids.ids)],
                }),
            ],
        })
        self.assertEquals(len(pt_01.product_variant_ids), 3)
        fname = self.get_sample(
            'sample_variants_exists_attribute_no_variant.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 3)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(product_tmpls_1.name, 'Template 1')
        self.assertEquals(product_tmpls_1.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_1.categ_id.parent_id)
        self.assertEquals(product_tmpls_1.type, 'service')
        self.assertTrue(product_tmpls_1.sale_ok)
        self.assertFalse(product_tmpls_1.purchase_ok)
        self.assertEquals(product_tmpls_1.list_price, 15.99)
        self.assertEquals(product_tmpls_1.invoice_policy, 'delivery')
        self.assertTrue(product_tmpls_1.image)
        self.assertTrue(product_tmpls_1.product_image_ids)
        for product in product_tmpls_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['White', 'S']:
                self.assertTrue(product.image_variant)
            else:
                self.assertFalse(product.image_variant)
        self.assertEquals(
            product_tmpls_1.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_1.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_1.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.product_brand_id, self.brand_1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 6)
        variant_WS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'S'])
        self.assertEquals(len(variant_WS), 1)
        self.assertEquals(variant_WS.default_code, 'PROD1_WS')
        self.assertEquals(variant_WS.barcode, '4050119164021')
        self.assertEquals(variant_WS.standard_price, 10.5)
        variant_WM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'M'])
        self.assertEquals(len(variant_WM), 1)
        self.assertEquals(variant_WM.default_code, 'PROD1_WM')
        self.assertEquals(variant_WM.barcode, '4050119164038')
        self.assertEquals(variant_WM.standard_price, 20)
        variant_WL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'L'])
        self.assertEquals(len(variant_WL), 1)
        self.assertEquals(variant_WL.default_code, 'PROD1_WL')
        self.assertEquals(variant_WL.barcode, '4050119164106')
        self.assertEquals(variant_WL.standard_price, 25)
        variant_BS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'S'])
        self.assertEquals(len(variant_BS), 1)
        self.assertEquals(variant_BS.default_code, 'PROD1_BS')
        self.assertEquals(variant_BS.barcode, '4050119164144')
        self.assertEquals(variant_BS.standard_price, 10)
        variant_BM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'M'])
        self.assertEquals(len(variant_BM), 1)
        self.assertEquals(variant_BM.default_code, 'PROD1_BM')
        self.assertEquals(variant_BM.barcode, '4050119164298')
        self.assertEquals(variant_BM.standard_price, 12)
        variant_BL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'L'])
        self.assertEquals(len(variant_BL), 1)
        self.assertEquals(variant_BL.default_code, 'PROD1_BL')
        self.assertEquals(variant_BL.barcode, '4050119164069')
        self.assertEquals(variant_BL.standard_price, 14)

    def test_import_write_diff_variants_exists_import_attribute_no_variant(
            self):
        value_black = self.attr_color.value_ids.filtered(
            lambda v: v.name == 'Black')
        self.assertEquals(len(value_black), 1)
        pt_01 = self.env['product.template'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL1TEST',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr_color.id,
                    'value_ids': [(6, 0, value_black.ids)],
                }),
                (0, 0, {
                    'attribute_id': self.attr_size.id,
                    'value_ids': [(6, 0, self.attr_size.value_ids.ids)],
                }),
            ],
        })
        self.assertEquals(len(pt_01.product_variant_ids), 3)
        fname = self.get_sample(
            'sample_variants_exists_import_attribute_no_variant.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 3)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(product_tmpls_1.name, 'Template 1')
        self.assertEquals(product_tmpls_1.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_1.categ_id.parent_id)
        self.assertEquals(product_tmpls_1.type, 'service')
        self.assertTrue(product_tmpls_1.sale_ok)
        self.assertFalse(product_tmpls_1.purchase_ok)
        self.assertEquals(product_tmpls_1.list_price, 15.99)
        self.assertEquals(product_tmpls_1.invoice_policy, 'delivery')
        self.assertTrue(product_tmpls_1.image)
        self.assertTrue(product_tmpls_1.product_image_ids)
        for product in product_tmpls_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['White', 'S']:
                self.assertTrue(product.image_variant)
            else:
                self.assertFalse(product.image_variant)
        self.assertEquals(
            product_tmpls_1.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_1.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_1.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.product_brand_id, self.brand_1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 6)
        variant_WS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'S'])
        self.assertEquals(len(variant_WS), 1)
        self.assertEquals(variant_WS.default_code, 'PROD1_WS')
        self.assertEquals(variant_WS.barcode, '4050119164021')
        self.assertEquals(variant_WS.standard_price, 10.5)
        variant_WM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'M'])
        self.assertEquals(len(variant_WM), 1)
        self.assertEquals(variant_WM.default_code, 'PROD1_WM')
        self.assertEquals(variant_WM.barcode, '4050119164038')
        self.assertEquals(variant_WM.standard_price, 20)
        variant_WL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'L'])
        self.assertEquals(len(variant_WL), 1)
        self.assertEquals(variant_WL.default_code, 'PROD1_WL')
        self.assertEquals(variant_WL.barcode, '4050119164106')
        self.assertEquals(variant_WL.standard_price, 25)
        variant_BS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'S'])
        self.assertEquals(len(variant_BS), 1)
        self.assertEquals(variant_BS.default_code, 'PROD1_BS')
        self.assertEquals(variant_BS.barcode, '4050119164144')
        self.assertEquals(variant_BS.standard_price, 10)
        variant_BM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'M'])
        self.assertEquals(len(variant_BM), 1)
        self.assertEquals(variant_BM.default_code, 'PROD1_BM')
        self.assertEquals(variant_BM.barcode, '4050119164298')
        self.assertEquals(variant_BM.standard_price, 12)
        variant_BL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'L'])
        self.assertEquals(len(variant_BL), 1)
        self.assertEquals(variant_BL.default_code, 'PROD1_BL')
        self.assertEquals(variant_BL.barcode, '4050119164069')
        self.assertEquals(variant_BL.standard_price, 14)

    def test_import_write_exists_not_variants(self):
        pt_02 = self.env['product.template'].create({
            'name': 'Product 2 test',
            'type': 'service',
            'standard_price': 80,
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL2TEST',
        })
        self.assertEquals(len(pt_02.product_variant_ids), 1)
        fname = self.get_sample('sample_exists_not_variants.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 6)
        msg_color_error = _(
            'The \'Color\' attribute of the file does not match the '
            'attributes of the product template; you must review it.')
        msg_size_error = _(
            'The \'Size\' attribute of the file does not match the '
            'attributes of the product template; you must review it.')
        self.assertIn(_('2: %s' % msg_color_error), wizard.line_ids[0].name)
        self.assertIn(_('2: %s' % msg_size_error), wizard.line_ids[1].name)
        self.assertIn(_('3: %s' % msg_color_error), wizard.line_ids[2].name)
        self.assertIn(_('3: %s' % msg_size_error), wizard.line_ids[3].name)
        self.assertIn(_('4: %s' % msg_color_error), wizard.line_ids[4].name)
        self.assertIn(_('4: %s' % msg_size_error), wizard.line_ids[5].name)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(len(product_tmpls_2.attribute_line_ids), 0)

    def test_import_create_three_attributes_exists(self):
        fname = self.get_sample('sample_three_attributes_exists.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 6)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '3: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '4: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[2].name)
        self.assertIn(_(
            '5: Product template \'Template 2\' not found, will be created.'),
            wizard.line_ids[3].name)
        self.assertIn(_(
            '6: Product template \'Template 2\' not found, will be created.'),
            wizard.line_ids[4].name)
        self.assertIn(_(
            '7: Product template \'Template 2\' not found, will be created.'),
            wizard.line_ids[5].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '5: Product template \'Template 2\' not found, will be created.'),
            wizard.line_ids[1].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(product_tmpls_1.name, 'Template 1')
        self.assertEquals(product_tmpls_1.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_1.categ_id.parent_id)
        self.assertEquals(product_tmpls_1.type, 'service')
        self.assertTrue(product_tmpls_1.sale_ok)
        self.assertFalse(product_tmpls_1.purchase_ok)
        self.assertEquals(product_tmpls_1.list_price, 15.99)
        self.assertEquals(product_tmpls_1.invoice_policy, 'delivery')
        self.assertTrue(product_tmpls_1.image)
        self.assertTrue(product_tmpls_1.product_image_ids)
        for product in product_tmpls_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['White', 'S']:
                self.assertTrue(product.image_variant)
            else:
                self.assertFalse(product.image_variant)
        self.assertEquals(
            product_tmpls_1.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_1.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_1.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.product_brand_id, self.brand_1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 3)
        variant_WS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'S'])
        self.assertEquals(len(variant_WS), 1)
        self.assertEquals(variant_WS.default_code, 'PROD1_WS')
        self.assertEquals(variant_WS.barcode, '4050119164021')
        self.assertEquals(variant_WS.standard_price, 10.5)
        variant_WM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'M'])
        self.assertEquals(len(variant_WM), 1)
        self.assertEquals(variant_WM.default_code, 'PROD1_WM')
        self.assertEquals(variant_WM.barcode, '4050119164038')
        self.assertEquals(variant_WM.standard_price, 20)
        variant_WL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'L'])
        self.assertEquals(len(variant_WL), 1)
        self.assertEquals(variant_WL.default_code, 'PROD1_WL')
        self.assertEquals(variant_WL.barcode, '4050119164106')
        self.assertEquals(variant_WL.standard_price, 25)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(len(product_tmpls_2.attribute_line_ids), 2)
        self.assertEquals(product_tmpls_2.name, 'Template 2')
        self.assertEquals(product_tmpls_2.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_2.categ_id.parent_id)
        self.assertEquals(product_tmpls_2.type, 'service')
        self.assertTrue(product_tmpls_2.sale_ok)
        self.assertFalse(product_tmpls_2.purchase_ok)
        self.assertEquals(product_tmpls_2.list_price, 15.99)
        self.assertEquals(product_tmpls_2.invoice_policy, 'delivery')
        self.assertFalse(product_tmpls_2.image)
        self.assertFalse(product_tmpls_2.product_image_ids)
        self.assertEquals(
            product_tmpls_2.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_2.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_2.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_2.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_2.product_brand_id, self.brand_1)
        color_line = product_tmpls_2.attribute_line_ids.filtered(
            lambda ln: ln.attribute_id.name == 'Color')
        self.assertEquals(len(color_line), 1)
        color_values = color_line.value_ids.mapped('name')
        self.assertEquals(len(color_values), 2)
        self.assertIn('White', color_values)
        self.assertIn('Red', color_values)
        lenght_line = product_tmpls_2.attribute_line_ids.filtered(
            lambda ln: ln.attribute_id.name == 'Lenght')
        self.assertEquals(len(lenght_line), 1)
        lenght_values = lenght_line.value_ids.mapped('name')
        self.assertEquals(len(lenght_values), 2)
        self.assertIn('10', lenght_values)
        self.assertIn('50', lenght_values)
        self.assertEquals(len(product_tmpls_2.product_variant_ids), 4)
        variant_W10 = product_tmpls_2.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', '10'])
        self.assertEquals(len(variant_W10), 1)
        self.assertEquals(variant_W10.default_code, 'PROD2_W10')
        self.assertEquals(variant_W10.barcode, '4050119164083')
        self.assertEquals(variant_W10.standard_price, 10.5)
        variant_R10 = product_tmpls_2.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Red', '10'])
        self.assertEquals(len(variant_R10), 1)
        self.assertEquals(variant_R10.default_code, 'PROD2_R10')
        self.assertEquals(variant_R10.barcode, '4050119164090')
        self.assertEquals(variant_R10.standard_price, 20)
        variant_R50 = product_tmpls_2.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Red', '50'])
        self.assertEquals(len(variant_R50), 1)
        self.assertEquals(variant_R50.default_code, '')
        self.assertEquals(variant_R50.barcode, '')
        self.assertEquals(variant_R50.standard_price, 25)
        attr_val_50 = self.env['product.attribute.value'].search([
            ('name', '=', '50'),
            ('attribute_id', '=', self.attr_lenght.id),
        ])
        self.assertEquals(len(attr_val_50), 1)
        attr_val_red = self.env['product.attribute.value'].search([
            ('name', '=', 'Red'),
            ('attribute_id', '=', self.attr_color.id),
        ])
        self.assertEquals(len(attr_val_red), 1)

    def test_import_write_three_attributes_exists(self):
        self.env['product.template'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL1TEST',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr_color.id,
                    'value_ids': [(6, 0, self.attr_color.value_ids.ids)],
                }),
                (0, 0, {
                    'attribute_id': self.attr_size.id,
                    'value_ids': [(6, 0, self.attr_size.value_ids.ids)],
                }),
            ],
        })
        self.env['product.template'].create({
            'name': 'Product 2 test',
            'type': 'service',
            'standard_price': 80,
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL2TEST',
        })
        fname = self.get_sample('sample_three_attributes_exists.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 6)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(len(product_tmpls_2.product_variant_ids), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 6)
        msg_color_error = _(
            'The \'Color\' attribute of the file does not match the '
            'attributes of the product template; you must review it.')
        msg_lenght_error = _(
            'The \'Lenght\' attribute of the file does not match the '
            'attributes of the product template; you must review it.')
        self.assertIn(_('5: %s' % msg_color_error), wizard.line_ids[0].name)
        self.assertIn(_('5: %s' % msg_lenght_error), wizard.line_ids[1].name)
        self.assertIn(_('6: %s' % msg_color_error), wizard.line_ids[2].name)
        self.assertIn(_('6: %s' % msg_lenght_error), wizard.line_ids[3].name)
        self.assertIn(_('7: %s' % msg_color_error), wizard.line_ids[4].name)
        self.assertIn(_('7: %s' % msg_lenght_error), wizard.line_ids[5].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(product_tmpls_1.name, 'Template 1')
        self.assertEquals(product_tmpls_1.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_1.categ_id.parent_id)
        self.assertEquals(product_tmpls_1.type, 'service')
        self.assertTrue(product_tmpls_1.sale_ok)
        self.assertFalse(product_tmpls_1.purchase_ok)
        self.assertEquals(product_tmpls_1.list_price, 15.99)
        self.assertEquals(product_tmpls_1.invoice_policy, 'delivery')
        self.assertTrue(product_tmpls_1.image)
        self.assertTrue(product_tmpls_1.product_image_ids)
        for product in product_tmpls_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['White', 'S']:
                self.assertTrue(product.image_variant)
            else:
                self.assertFalse(product.image_variant)
        self.assertEquals(
            product_tmpls_1.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_1.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_1.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.product_brand_id, self.brand_1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 6)
        variant_WS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'S'])
        self.assertEquals(len(variant_WS), 1)
        self.assertEquals(variant_WS.default_code, 'PROD1_WS')
        self.assertEquals(variant_WS.barcode, '4050119164021')
        variant_WM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'M'])
        self.assertEquals(len(variant_WM), 1)
        self.assertEquals(variant_WM.default_code, 'PROD1_WM')
        self.assertEquals(variant_WM.barcode, '4050119164038')
        variant_WL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'L'])
        self.assertEquals(len(variant_WL), 1)
        self.assertEquals(variant_WL.default_code, 'PROD1_WL')
        self.assertEquals(variant_WL.barcode, '4050119164106')
        remainder_variants = (
            product_tmpls_1.product_variant_ids - variant_WS - variant_WM
            - variant_WL)
        for variant in remainder_variants:
            self.assertFalse(variant.default_code)
            self.assertFalse(variant.barcode)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(len(product_tmpls_2.attribute_line_ids), 0)

    def test_import_create_three_attributes_not_exists(self):
        fname = self.get_sample('sample_three_attributes_not_exists.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 6)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '3: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '4: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[2].name)
        self.assertIn(_(
            '5: Product template \'Template 2\' not found, will be created.'),
            wizard.line_ids[3].name)
        self.assertIn(_(
            '6: Product template \'Template 2\' not found, will be created.'),
            wizard.line_ids[4].name)
        self.assertIn(_(
            '7: Product template \'Template 2\' not found, will be created.'),
            wizard.line_ids[5].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '5: Product template \'Template 2\' not found, will be created.'),
            wizard.line_ids[1].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(product_tmpls_1.name, 'Template 1')
        self.assertEquals(product_tmpls_1.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_1.categ_id.parent_id)
        self.assertEquals(product_tmpls_1.type, 'service')
        self.assertTrue(product_tmpls_1.sale_ok)
        self.assertFalse(product_tmpls_1.purchase_ok)
        self.assertEquals(product_tmpls_1.list_price, 15.99)
        self.assertEquals(product_tmpls_1.invoice_policy, 'delivery')
        self.assertTrue(product_tmpls_1.image)
        self.assertTrue(product_tmpls_1.product_image_ids)
        for product in product_tmpls_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['White', 'S']:
                self.assertTrue(product.image_variant)
            else:
                self.assertFalse(product.image_variant)
        self.assertEquals(
            product_tmpls_1.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_1.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_1.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.product_brand_id, self.brand_1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 3)
        variant_WS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'S'])
        self.assertEquals(len(variant_WS), 1)
        self.assertEquals(variant_WS.default_code, 'PROD1_WS')
        self.assertEquals(variant_WS.barcode, '4050119164021')
        self.assertEquals(variant_WS.standard_price, 10.5)
        variant_WM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'M'])
        self.assertEquals(len(variant_WM), 1)
        self.assertEquals(variant_WM.default_code, 'PROD1_WM')
        self.assertEquals(variant_WM.barcode, '4050119164038')
        self.assertEquals(variant_WM.standard_price, 20)
        variant_WL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'L'])
        self.assertEquals(len(variant_WL), 1)
        self.assertEquals(variant_WL.default_code, 'PROD1_WL')
        self.assertEquals(variant_WL.barcode, '4050119164106')
        self.assertEquals(variant_WL.standard_price, 25)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(product_tmpls_2.name, 'Template 2')
        self.assertEquals(product_tmpls_2.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_2.categ_id.parent_id)
        self.assertEquals(product_tmpls_2.type, 'service')
        self.assertTrue(product_tmpls_2.sale_ok)
        self.assertFalse(product_tmpls_2.purchase_ok)
        self.assertEquals(product_tmpls_2.list_price, 15.99)
        self.assertEquals(product_tmpls_2.invoice_policy, 'delivery')
        self.assertFalse(product_tmpls_2.image)
        self.assertFalse(product_tmpls_2.product_image_ids)
        self.assertEquals(
            product_tmpls_2.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_2.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_2.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_2.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_2.product_brand_id, self.brand_1)
        self.assertEquals(len(product_tmpls_2.attribute_line_ids), 2)
        color_line = product_tmpls_2.attribute_line_ids.filtered(
            lambda ln: ln.attribute_id.name == 'Color')
        self.assertEquals(len(color_line), 1)
        color_values = color_line.value_ids.mapped('name')
        self.assertEquals(len(color_values), 2)
        self.assertIn('White', color_values)
        self.assertIn('Red', color_values)
        width_line = product_tmpls_2.attribute_line_ids.filtered(
            lambda ln: ln.attribute_id.name == 'Width')
        self.assertEquals(len(width_line), 1)
        width_values = width_line.value_ids.mapped('name')
        self.assertEquals(len(width_values), 2)
        self.assertIn('11.5', width_values)
        self.assertIn('22.5', width_values)
        self.assertEquals(len(product_tmpls_2.product_variant_ids), 4)
        variant_W11_5 = product_tmpls_2.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', '11.5'])
        self.assertEquals(len(variant_W11_5), 1)
        self.assertEquals(variant_W11_5.default_code, 'PROD2_W10')
        self.assertEquals(variant_W11_5.barcode, '4050119164083')
        self.assertEquals(variant_W11_5.standard_price, 10.5)
        variant_R11_5 = product_tmpls_2.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Red', '11.5'])
        self.assertEquals(len(variant_R11_5), 1)
        self.assertEquals(variant_R11_5.default_code, 'PROD2_R10')
        self.assertEquals(variant_R11_5.barcode, '4050119164090')
        self.assertEquals(variant_R11_5.standard_price, 20)
        variant_R22_5 = product_tmpls_2.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Red', '22.5'])
        self.assertEquals(len(variant_R22_5), 1)
        self.assertEquals(variant_R22_5.default_code, '')
        self.assertEquals(variant_R22_5.barcode, '')
        self.assertEquals(variant_R22_5.standard_price, 25)
        attr_width = self.env['product.attribute'].search([
            ('name', '=', 'Width'),
        ])
        self.assertEquals(len(attr_width), 1)
        attr_val_11_5 = self.env['product.attribute.value'].search([
            ('name', '=', '11.5'),
            ('attribute_id', '=', attr_width.id),
        ])
        self.assertEquals(len(attr_val_11_5), 1)
        attr_val_22_5 = self.env['product.attribute.value'].search([
            ('name', '=', '22.5'),
            ('attribute_id', '=', attr_width.id),
        ])
        self.assertEquals(len(attr_val_22_5), 1)
        attr_val_red = self.env['product.attribute.value'].search([
            ('name', '=', 'Red'),
            ('attribute_id', '=', self.attr_color.id),
        ])
        self.assertEquals(len(attr_val_red), 1)

    def test_import_write_three_attributes_not_exists(self):
        self.env['product.template'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL1TEST',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr_color.id,
                    'value_ids': [(6, 0, self.attr_color.value_ids.ids)],
                }),
                (0, 0, {
                    'attribute_id': self.attr_size.id,
                    'value_ids': [(6, 0, self.attr_size.value_ids.ids)],
                }),
            ],
        })
        self.env['product.template'].create({
            'name': 'Product 2 test',
            'type': 'service',
            'standard_price': 80,
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL2TEST',
        })
        fname = self.get_sample('sample_three_attributes_not_exists.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 6)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(len(product_tmpls_2.product_variant_ids), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 6)
        msg_color_error = _(
            'The \'Color\' attribute of the file does not match the '
            'attributes of the product template; you must review it.')
        msg_width_error = _(
            'The \'Width\' attribute of the file does not match the '
            'attributes of the product template; you must review it.')
        self.assertIn(_('5: %s' % msg_color_error), wizard.line_ids[0].name)
        self.assertIn(_('5: %s' % msg_width_error), wizard.line_ids[1].name)
        self.assertIn(_('6: %s' % msg_color_error), wizard.line_ids[2].name)
        self.assertIn(_('6: %s' % msg_width_error), wizard.line_ids[3].name)
        self.assertIn(_('7: %s' % msg_color_error), wizard.line_ids[4].name)
        self.assertIn(_('7: %s' % msg_width_error), wizard.line_ids[5].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(product_tmpls_1.name, 'Template 1')
        self.assertEquals(product_tmpls_1.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_1.categ_id.parent_id)
        self.assertEquals(product_tmpls_1.type, 'service')
        self.assertTrue(product_tmpls_1.sale_ok)
        self.assertFalse(product_tmpls_1.purchase_ok)
        self.assertEquals(product_tmpls_1.list_price, 15.99)
        self.assertEquals(product_tmpls_1.invoice_policy, 'delivery')
        self.assertTrue(product_tmpls_1.image)
        self.assertTrue(product_tmpls_1.product_image_ids)
        for product in product_tmpls_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['White', 'S']:
                self.assertTrue(product.image_variant)
            else:
                self.assertFalse(product.image_variant)
        self.assertEquals(
            product_tmpls_1.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_1.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_1.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.product_brand_id, self.brand_1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 6)
        variant_WS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'S'])
        self.assertEquals(len(variant_WS), 1)
        self.assertEquals(variant_WS.default_code, 'PROD1_WS')
        self.assertEquals(variant_WS.barcode, '4050119164021')
        self.assertEquals(variant_WS.standard_price, 10.5)
        variant_WM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'M'])
        self.assertEquals(len(variant_WM), 1)
        self.assertEquals(variant_WM.default_code, 'PROD1_WM')
        self.assertEquals(variant_WM.barcode, '4050119164038')
        self.assertEquals(variant_WM.standard_price, 20)
        variant_WL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'L'])
        self.assertEquals(len(variant_WL), 1)
        self.assertEquals(variant_WL.default_code, 'PROD1_WL')
        self.assertEquals(variant_WL.barcode, '4050119164106')
        self.assertEquals(variant_WL.standard_price, 25)
        remainder_variants = (
            product_tmpls_1.product_variant_ids - variant_WS - variant_WM
            - variant_WL)
        for variant in remainder_variants:
            self.assertFalse(variant.default_code)
            self.assertFalse(variant.barcode)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(len(product_tmpls_2.attribute_line_ids), 0)

    def test_import_write_three_attributes_disordered_exists(self):
        self.env['product.template'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL1TEST',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr_color.id,
                    'value_ids': [(6, 0, self.attr_color.value_ids.ids)],
                }),
                (0, 0, {
                    'attribute_id': self.attr_size.id,
                    'value_ids': [(6, 0, self.attr_size.value_ids.ids)],
                }),
            ],
        })
        self.env['product.template'].create({
            'name': 'Product 2 test',
            'type': 'service',
            'standard_price': 80,
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL2TEST',
        })
        fname = self.get_sample(
            'sample_three_attributes_disordered_exists.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 6)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(len(product_tmpls_2.product_variant_ids), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 6)
        msg_color_error = _(
            'The \'Color\' attribute of the file does not match the '
            'attributes of the product template; you must review it.')
        msg_lenght_error = _(
            'The \'Lenght\' attribute of the file does not match the '
            'attributes of the product template; you must review it.')
        self.assertIn(_('5: %s' % msg_lenght_error), wizard.line_ids[0].name)
        self.assertIn(_('5: %s' % msg_color_error), wizard.line_ids[1].name)
        self.assertIn(_('6: %s' % msg_lenght_error), wizard.line_ids[2].name)
        self.assertIn(_('6: %s' % msg_color_error), wizard.line_ids[3].name)
        self.assertIn(_('7: %s' % msg_lenght_error), wizard.line_ids[4].name)
        self.assertIn(_('7: %s' % msg_color_error), wizard.line_ids[5].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(product_tmpls_1.name, 'Template 1')
        self.assertEquals(product_tmpls_1.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_1.categ_id.parent_id)
        self.assertEquals(product_tmpls_1.type, 'service')
        self.assertTrue(product_tmpls_1.sale_ok)
        self.assertFalse(product_tmpls_1.purchase_ok)
        self.assertEquals(product_tmpls_1.list_price, 15.99)
        self.assertEquals(product_tmpls_1.invoice_policy, 'delivery')
        self.assertTrue(product_tmpls_1.image)
        self.assertTrue(product_tmpls_1.product_image_ids)
        for product in product_tmpls_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['White', 'S']:
                self.assertTrue(product.image_variant)
            else:
                self.assertFalse(product.image_variant)
        self.assertEquals(
            product_tmpls_1.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_1.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_1.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.product_brand_id, self.brand_1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 6)
        variant_WS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'S'])
        self.assertEquals(len(variant_WS), 1)
        self.assertEquals(variant_WS.default_code, 'PROD1_WS')
        self.assertEquals(variant_WS.standard_price, 10.5)
        self.assertEquals(variant_WS.barcode, '4050119164021')
        variant_WM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'M'])
        self.assertEquals(len(variant_WM), 1)
        self.assertEquals(variant_WM.default_code, 'PROD1_WM')
        self.assertEquals(variant_WM.barcode, '4050119164038')
        self.assertEquals(variant_WM.standard_price, 20)
        variant_WL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'L'])
        self.assertEquals(len(variant_WL), 1)
        self.assertEquals(variant_WL.default_code, 'PROD1_WL')
        self.assertEquals(variant_WL.barcode, '4050119164106')
        self.assertEquals(variant_WL.standard_price, 25)
        remainder_variants = (
            product_tmpls_1.product_variant_ids - variant_WS - variant_WM
            - variant_WL)
        for variant in remainder_variants:
            self.assertFalse(variant.default_code)
            self.assertFalse(variant.barcode)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(len(product_tmpls_2.attribute_line_ids), 0)

    def test_import_write_three_attributes_disordered_not_exists(self):
        self.env['product.template'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL1TEST',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr_color.id,
                    'value_ids': [(6, 0, self.attr_color.value_ids.ids)],
                }),
                (0, 0, {
                    'attribute_id': self.attr_size.id,
                    'value_ids': [(6, 0, self.attr_size.value_ids.ids)],
                }),
            ],
        })
        self.env['product.template'].create({
            'name': 'Product 2 test',
            'type': 'service',
            'standard_price': 80,
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL2TEST',
        })
        fname = self.get_sample(
            'sample_three_attributes_disordered_not_exists.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 6)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(len(product_tmpls_2.product_variant_ids), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 6)
        msg_color_error = _(
            'The \'Color\' attribute of the file does not match the '
            'attributes of the product template; you must review it.')
        msg_width_error = _(
            'The \'Width\' attribute of the file does not match the '
            'attributes of the product template; you must review it.')
        self.assertIn(_('5: %s' % msg_width_error), wizard.line_ids[0].name)
        self.assertIn(_('5: %s' % msg_color_error), wizard.line_ids[1].name)
        self.assertIn(_('6: %s' % msg_width_error), wizard.line_ids[2].name)
        self.assertIn(_('6: %s' % msg_color_error), wizard.line_ids[3].name)
        self.assertIn(_('7: %s' % msg_width_error), wizard.line_ids[4].name)
        self.assertIn(_('7: %s' % msg_color_error), wizard.line_ids[5].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(product_tmpls_1.name, 'Template 1')
        self.assertEquals(product_tmpls_1.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_1.categ_id.parent_id)
        self.assertEquals(product_tmpls_1.type, 'service')
        self.assertTrue(product_tmpls_1.sale_ok)
        self.assertFalse(product_tmpls_1.purchase_ok)
        self.assertEquals(product_tmpls_1.list_price, 15.99)
        self.assertEquals(product_tmpls_1.invoice_policy, 'delivery')
        self.assertTrue(product_tmpls_1.image)
        self.assertTrue(product_tmpls_1.product_image_ids)
        for product in product_tmpls_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['White', 'S']:
                self.assertTrue(product.image_variant)
            else:
                self.assertFalse(product.image_variant)
        self.assertEquals(
            product_tmpls_1.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_1.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_1.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.product_brand_id, self.brand_1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 6)
        variant_WS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'S'])
        self.assertEquals(len(variant_WS), 1)
        self.assertEquals(variant_WS.default_code, 'PROD1_WS')
        self.assertEquals(variant_WS.barcode, '4050119164021')
        self.assertEquals(variant_WS.standard_price, 10.5)
        variant_WM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'M'])
        self.assertEquals(len(variant_WM), 1)
        self.assertEquals(variant_WM.default_code, 'PROD1_WM')
        self.assertEquals(variant_WM.barcode, '4050119164038')
        self.assertEquals(variant_WM.standard_price, 20)
        variant_WL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'L'])
        self.assertEquals(len(variant_WL), 1)
        self.assertEquals(variant_WL.default_code, 'PROD1_WL')
        self.assertEquals(variant_WL.barcode, '4050119164106')
        self.assertEquals(variant_WL.standard_price, 25)
        remainder_variants = (
            product_tmpls_1.product_variant_ids - variant_WS - variant_WM
            - variant_WL)
        for variant in remainder_variants:
            self.assertFalse(variant.default_code)
            self.assertFalse(variant.barcode)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(len(product_tmpls_2.attribute_line_ids), 0)

    def test_import_write_diff_variants_attributes_disordered_exists(self):
        value_black = self.attr_color.value_ids.filtered(
            lambda v: v.name == 'Black')
        self.assertEquals(len(value_black), 1)
        pt_01 = self.env['product.template'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL1TEST',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr_size.id,
                    'value_ids': [(6, 0, self.attr_size.value_ids.ids)],
                }),
                (0, 0, {
                    'attribute_id': self.attr_color.id,
                    'value_ids': [(6, 0, value_black.ids)],
                }),
            ],
        })
        self.assertEquals(len(pt_01.product_variant_ids), 3)
        fname = self.get_sample('sample_variants_attributes_disordered.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 3)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(product_tmpls_1.name, 'Template 1')
        self.assertEquals(product_tmpls_1.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_1.categ_id.parent_id)
        self.assertEquals(product_tmpls_1.type, 'service')
        self.assertTrue(product_tmpls_1.sale_ok)
        self.assertFalse(product_tmpls_1.purchase_ok)
        self.assertEquals(product_tmpls_1.list_price, 15.99)
        self.assertEquals(product_tmpls_1.invoice_policy, 'delivery')
        self.assertTrue(product_tmpls_1.image)
        self.assertTrue(product_tmpls_1.product_image_ids)
        for product in product_tmpls_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['White', 'S']:
                self.assertTrue(product.image_variant)
            else:
                self.assertFalse(product.image_variant)
        self.assertEquals(
            product_tmpls_1.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_1.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_1.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.product_brand_id, self.brand_1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 6)
        variant_WS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'S'])
        self.assertEquals(len(variant_WS), 1)
        self.assertEquals(variant_WS.default_code, 'PROD1_WS')
        self.assertEquals(variant_WS.barcode, '4050119164021')
        self.assertEquals(variant_WS.standard_price, 10.5)
        variant_WM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'M'])
        self.assertEquals(len(variant_WM), 1)
        self.assertEquals(variant_WM.default_code, 'PROD1_WM')
        self.assertEquals(variant_WM.barcode, '4050119164038')
        self.assertEquals(variant_WM.standard_price, 20)
        variant_WL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'L'])
        self.assertEquals(len(variant_WL), 1)
        self.assertEquals(variant_WL.default_code, 'PROD1_WL')
        self.assertEquals(variant_WL.barcode, '4050119164106')
        self.assertEquals(variant_WL.standard_price, 25)
        variant_BS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'S'])
        self.assertEquals(len(variant_BS), 1)
        self.assertEquals(variant_BS.default_code, 'PROD1_BS')
        self.assertEquals(variant_BS.barcode, '4050119164144')
        self.assertEquals(variant_BS.standard_price, 10)
        variant_BM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'M'])
        self.assertEquals(len(variant_BM), 1)
        self.assertEquals(variant_BM.default_code, 'PROD1_BM')
        self.assertEquals(variant_BM.barcode, '4050119164298')
        self.assertEquals(variant_BM.standard_price, 12)
        variant_BL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'L'])
        self.assertEquals(len(variant_BL), 1)
        self.assertEquals(variant_BL.default_code, 'PROD1_BL')
        self.assertEquals(variant_BL.barcode, '4050119164069')
        self.assertEquals(variant_BL.standard_price, 14)

    def test_import_create_template_without_variants(self):
        fname = self.get_sample('sample_template_without_variants.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 1)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[0].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 1)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[0].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 1)
        self.assertEquals(
            product_tmpls_1.product_variant_ids.default_code, 'PROD1_UNIQUE')
        self.assertEquals(
            product_tmpls_1.product_variant_ids.barcode, '4050119164021')
        self.assertTrue(product_tmpls_1.image)
        self.assertTrue(product_tmpls_1.product_image_ids)
        self.assertFalse(product_tmpls_1.product_variant_ids.image_variant)

    def test_import_write_template_without_variants(self):
        pt_01 = self.env['product.template'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'standard_price': 80,
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL1TEST',
        })
        self.assertEquals(len(pt_01.product_variant_ids), 1)
        fname = self.get_sample('sample_template_without_variants.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 1)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 1)
        self.assertFalse(product_tmpls_1.product_variant_ids.default_code)
        self.assertFalse(product_tmpls_1.product_variant_ids.barcode)
        self.assertEquals(len(product_tmpls_1), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 1)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(product_tmpls_1.name, 'Template 1')
        self.assertEquals(product_tmpls_1.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_1.categ_id.parent_id)
        self.assertEquals(product_tmpls_1.type, 'service')
        self.assertTrue(product_tmpls_1.sale_ok)
        self.assertFalse(product_tmpls_1.purchase_ok)
        self.assertEquals(product_tmpls_1.list_price, 15.99)
        self.assertEquals(product_tmpls_1.invoice_policy, 'delivery')
        self.assertEquals(
            product_tmpls_1.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_1.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_1.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.product_brand_id, self.brand_1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 1)
        self.assertEquals(
            product_tmpls_1.product_variant_ids.default_code, 'PROD1_UNIQUE')
        self.assertEquals(
            product_tmpls_1.product_variant_ids.barcode, '4050119164021')
        self.assertEquals(
            product_tmpls_1.product_variant_ids.standard_price, 10.5)
        self.assertTrue(product_tmpls_1.image)
        self.assertTrue(product_tmpls_1.product_image_ids)
        self.assertFalse(product_tmpls_1.product_variant_ids.image_variant)

    def test_import_create_only_required_columns(self):
        fname = self.get_sample('sample_only_required_columns.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 4)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '3: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '4: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[2].name)
        self.assertIn(_(
            '5: Product template \'Template 2\' not found, will be created.'),
            wizard.line_ids[3].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '5: Product template \'Template 2\' not found, will be created.'),
            wizard.line_ids[1].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(product_tmpls_1.name, 'Template 1')
        self.assertEquals(product_tmpls_1.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_1.categ_id.parent_id)
        self.assertEquals(product_tmpls_1.type, 'service')
        self.assertTrue(product_tmpls_1.sale_ok)
        self.assertTrue(product_tmpls_1.purchase_ok)
        self.assertEquals(product_tmpls_1.list_price, 1.0)
        self.assertEquals(product_tmpls_1.invoice_policy, 'order')
        self.assertFalse(product_tmpls_1.image)
        self.assertFalse(product_tmpls_1.product_image_ids)
        self.assertFalse(product_tmpls_1.description_sale)
        self.assertFalse(product_tmpls_1.description_purchase)
        self.assertEquals(product_tmpls_1.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.uom_po_id.name, 'Unit(s)')
        self.assertFalse(product_tmpls_1.product_brand_id)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 3)
        variant_WS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'S'])
        self.assertEquals(len(variant_WS), 1)
        self.assertEquals(variant_WS.default_code, 'PROD1_WS')
        self.assertEquals(variant_WS.barcode, '4050119164021')
        self.assertEquals(variant_WS.standard_price, 0)
        variant_WM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'M'])
        self.assertEquals(len(variant_WM), 1)
        self.assertEquals(variant_WM.default_code, 'PROD1_WM')
        self.assertEquals(variant_WM.barcode, '4050119164038')
        self.assertEquals(variant_WM.standard_price, 0)
        variant_WL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'L'])
        self.assertEquals(len(variant_WL), 1)
        self.assertEquals(variant_WL.default_code, 'PROD1_WL')
        self.assertEquals(variant_WL.barcode, '4050119164106')
        self.assertEquals(variant_WL.standard_price, 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(len(product_tmpls_2.product_variant_ids), 1)
        self.assertEquals(
            product_tmpls_2.product_variant_ids.default_code, 'PROD2')
        self.assertEquals(
            product_tmpls_2.product_variant_ids.barcode, '4050119164090')
        self.assertFalse(product_tmpls_2.image)
        self.assertFalse(product_tmpls_2.product_image_ids)
        self.assertFalse(product_tmpls_2.product_variant_ids.image_variant)

    def test_import_write_only_required_columns(self):
        pt_01 = self.env['product.template'].create({
            'name': 'Product 1 test',
            'product_tmpl_code': 'PRODTMPL1TEST',
            'type': 'service',
            'list_price': 100,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr_color.id,
                    'value_ids': [(6, 0, self.attr_color.value_ids.ids)],
                }),
                (0, 0, {
                    'attribute_id': self.attr_size.id,
                    'value_ids': [(6, 0, self.attr_size.value_ids.ids)],
                }),
            ],
        })
        self.assertEquals(len(pt_01.product_variant_ids), 6)
        pt_02 = self.env['product.template'].create({
            'name': 'Product 2 test',
            'type': 'service',
            'standard_price': 80,
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL2TEST',
        })
        self.assertEquals(len(pt_02.product_variant_ids), 1)
        fname = self.get_sample('sample_only_required_columns.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(product_tmpls_1.name, 'Template 1')
        self.assertEquals(product_tmpls_1.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_1.categ_id.parent_id)
        self.assertEquals(product_tmpls_1.type, 'service')
        self.assertTrue(product_tmpls_1.sale_ok)
        self.assertTrue(product_tmpls_1.purchase_ok)
        self.assertEquals(product_tmpls_1.list_price, 100)
        self.assertEquals(product_tmpls_1.invoice_policy, 'order')
        self.assertFalse(product_tmpls_1.image)
        self.assertFalse(product_tmpls_1.product_image_ids)
        self.assertFalse(product_tmpls_1.description_sale)
        self.assertFalse(product_tmpls_1.description_purchase)
        self.assertEquals(product_tmpls_1.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.uom_po_id.name, 'Unit(s)')
        self.assertFalse(product_tmpls_1.product_brand_id)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 6)
        variant_WS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'S'])
        self.assertEquals(len(variant_WS), 1)
        self.assertEquals(variant_WS.default_code, 'PROD1_WS')
        self.assertEquals(variant_WS.barcode, '4050119164021')
        self.assertEquals(variant_WS.standard_price, 0)
        variant_WM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'M'])
        self.assertEquals(len(variant_WM), 1)
        self.assertEquals(variant_WM.default_code, 'PROD1_WM')
        self.assertEquals(variant_WM.barcode, '4050119164038')
        self.assertEquals(variant_WM.standard_price, 0)
        variant_WL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'L'])
        self.assertEquals(len(variant_WL), 1)
        self.assertEquals(variant_WL.default_code, 'PROD1_WL')
        self.assertEquals(variant_WL.barcode, '4050119164106')
        self.assertEquals(variant_WL.standard_price, 0)
        variant_BS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'S'])
        self.assertEquals(len(variant_BS), 1)
        self.assertFalse(variant_BS.default_code)
        self.assertFalse(variant_BS.barcode)
        self.assertEquals(variant_BS.standard_price, 0)
        variant_BM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'M'])
        self.assertEquals(len(variant_BM), 1)
        self.assertFalse(variant_BM.default_code)
        self.assertFalse(variant_BM.barcode)
        self.assertEquals(variant_BM.standard_price, 0)
        variant_BL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'L'])
        self.assertEquals(len(variant_BL), 1)
        self.assertFalse(variant_BL.default_code)
        self.assertFalse(variant_BL.barcode)
        self.assertEquals(variant_BL.standard_price, 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(product_tmpls_2.name, 'Template 2')
        self.assertEquals(product_tmpls_2.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_2.categ_id.parent_id)
        self.assertEquals(product_tmpls_2.type, 'service')
        self.assertTrue(product_tmpls_2.sale_ok)
        self.assertTrue(product_tmpls_2.purchase_ok)
        self.assertEquals(product_tmpls_2.standard_price, 0)
        self.assertEquals(product_tmpls_2.list_price, 100)
        self.assertEquals(product_tmpls_2.invoice_policy, 'order')
        self.assertFalse(product_tmpls_2.image)
        self.assertFalse(product_tmpls_2.product_image_ids)
        self.assertFalse(product_tmpls_2.description_sale)
        self.assertFalse(product_tmpls_2.description_purchase)
        self.assertEquals(product_tmpls_2.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_2.uom_po_id.name, 'Unit(s)')
        self.assertFalse(product_tmpls_2.product_brand_id)
        self.assertEquals(len(product_tmpls_2.product_variant_ids), 1)
        self.assertEquals(
            product_tmpls_2.product_variant_ids.default_code, 'PROD2')
        self.assertEquals(
            product_tmpls_2.product_variant_ids.barcode, '4050119164090')
        self.assertEquals(
            product_tmpls_2.product_variant_ids.standard_price, 0)

    def test_import_create_new_columns(self):
        fname = self.get_sample('sample_new_columns.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 6)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '3: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '4: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[2].name)
        self.assertIn(_(
            '5: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[3].name)
        self.assertIn(_(
            '6: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[4].name)
        self.assertIn(_(
            '7: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[5].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 1)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[0].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(product_tmpls_1.name, 'Template 1')
        self.assertEquals(product_tmpls_1.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_1.categ_id.parent_id)
        self.assertEquals(product_tmpls_1.type, 'service')
        self.assertTrue(product_tmpls_1.sale_ok)
        self.assertFalse(product_tmpls_1.purchase_ok)
        self.assertEquals(product_tmpls_1.list_price, 15.99)
        self.assertEquals(product_tmpls_1.invoice_policy, 'delivery')
        self.assertTrue(product_tmpls_1.image)
        self.assertTrue(product_tmpls_1.product_image_ids)
        for product in product_tmpls_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['White', 'S']:
                self.assertTrue(product.image_variant)
            else:
                self.assertFalse(product.image_variant)
        self.assertEquals(
            product_tmpls_1.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_1.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_1.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.product_brand_id, self.brand_1)
        self.assertEquals(product_tmpls_1.weight, 0)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 6)
        variant_WS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'S'])
        self.assertEquals(len(variant_WS), 1)
        self.assertEquals(variant_WS.default_code, 'PROD1_WS')
        self.assertEquals(variant_WS.barcode, '4050119164021')
        self.assertEquals(variant_WS.standard_price, 10.5)
        self.assertEquals(variant_WS.weight, 11)
        variant_WM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'M'])
        self.assertEquals(len(variant_WM), 1)
        self.assertEquals(variant_WM.default_code, 'PROD1_WM')
        self.assertEquals(variant_WM.barcode, '4050119164038')
        self.assertEquals(variant_WM.standard_price, 20)
        self.assertEquals(variant_WM.weight, 11.5)
        variant_WL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'L'])
        self.assertEquals(len(variant_WL), 1)
        self.assertEquals(variant_WL.default_code, 'PROD1_WL')
        self.assertEquals(variant_WL.barcode, '4050119164106')
        self.assertEquals(variant_WL.standard_price, 25)
        self.assertEquals(variant_WL.weight, 12)
        variant_BS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'S'])
        self.assertEquals(len(variant_BS), 1)
        self.assertEquals(variant_BS.default_code, 'PROD1_BS')
        self.assertEquals(variant_BS.barcode, '4050119164144')
        self.assertEquals(variant_BS.standard_price, 10)
        self.assertEquals(variant_BS.weight, 13)
        variant_BM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'M'])
        self.assertEquals(len(variant_BM), 1)
        self.assertEquals(variant_BM.default_code, 'PROD1_BM')
        self.assertEquals(variant_BM.barcode, '4050119164298')
        self.assertEquals(variant_BM.standard_price, 12)
        self.assertEquals(variant_BM.weight, 14)
        variant_BL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'L'])
        self.assertEquals(len(variant_BL), 1)
        self.assertEquals(variant_BL.default_code, 'PROD1_BL')
        self.assertEquals(variant_BL.barcode, '4050119164069')
        self.assertEquals(variant_BL.standard_price, 14)
        self.assertEquals(variant_BL.weight, 15)

    def test_import_write_new_columns(self):
        pt_01 = self.env['product.template'].create({
            'name': 'Product 1 test',
            'product_tmpl_code': 'PRODTMPL1TEST',
            'type': 'service',
            'list_price': 100,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr_color.id,
                    'value_ids': [(6, 0, self.attr_color.value_ids.ids)],
                }),
                (0, 0, {
                    'attribute_id': self.attr_size.id,
                    'value_ids': [(6, 0, self.attr_size.value_ids.ids)],
                }),
            ],
        })
        self.assertEquals(len(pt_01.product_variant_ids), 6)
        pt_02 = self.env['product.template'].create({
            'name': 'Product 2 test',
            'type': 'service',
            'standard_price': 80,
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL2TEST',
        })
        self.assertEquals(len(pt_02.product_variant_ids), 1)
        fname = self.get_sample('sample_new_columns.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(product_tmpls_1.name, 'Template 1')
        self.assertEquals(product_tmpls_1.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_1.categ_id.parent_id)
        self.assertEquals(product_tmpls_1.type, 'service')
        self.assertTrue(product_tmpls_1.sale_ok)
        self.assertFalse(product_tmpls_1.purchase_ok)
        self.assertEquals(product_tmpls_1.list_price, 15.99)
        self.assertEquals(product_tmpls_1.invoice_policy, 'delivery')
        self.assertTrue(product_tmpls_1.image)
        self.assertTrue(product_tmpls_1.product_image_ids)
        for product in product_tmpls_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['White', 'S']:
                self.assertTrue(product.image_variant)
            else:
                self.assertFalse(product.image_variant)
        self.assertEquals(
            product_tmpls_1.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_1.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_1.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.product_brand_id, self.brand_1)
        self.assertEquals(product_tmpls_1.weight, 0)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 6)
        variant_WS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'S'])
        self.assertEquals(len(variant_WS), 1)
        self.assertEquals(variant_WS.default_code, 'PROD1_WS')
        self.assertEquals(variant_WS.barcode, '4050119164021')
        self.assertEquals(variant_WS.standard_price, 10.5)
        self.assertEquals(variant_WS.weight, 11)
        variant_WM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'M'])
        self.assertEquals(len(variant_WM), 1)
        self.assertEquals(variant_WM.default_code, 'PROD1_WM')
        self.assertEquals(variant_WM.barcode, '4050119164038')
        self.assertEquals(variant_WM.standard_price, 20)
        self.assertEquals(variant_WM.weight, 11.5)
        variant_WL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'L'])
        self.assertEquals(len(variant_WL), 1)
        self.assertEquals(variant_WL.default_code, 'PROD1_WL')
        self.assertEquals(variant_WL.barcode, '4050119164106')
        self.assertEquals(variant_WL.standard_price, 25)
        self.assertEquals(variant_WL.weight, 12)
        variant_BS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'S'])
        self.assertEquals(len(variant_BS), 1)
        self.assertEquals(variant_BS.default_code, 'PROD1_BS')
        self.assertEquals(variant_BS.barcode, '4050119164144')
        self.assertEquals(variant_BS.standard_price, 10)
        self.assertEquals(variant_BS.weight, 13)
        variant_BM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'M'])
        self.assertEquals(len(variant_BM), 1)
        self.assertEquals(variant_BM.default_code, 'PROD1_BM')
        self.assertEquals(variant_BM.barcode, '4050119164298')
        self.assertEquals(variant_BM.standard_price, 12)
        self.assertEquals(variant_BM.weight, 14)
        variant_BL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Black', 'L'])
        self.assertEquals(len(variant_BL), 1)
        self.assertEquals(variant_BL.default_code, 'PROD1_BL')
        self.assertEquals(variant_BL.barcode, '4050119164069')
        self.assertEquals(variant_BL.standard_price, 14)
        self.assertEquals(variant_BL.weight, 15)

    def test_import_create_without_images(self):
        fname = self.get_sample('sample_images_empty_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 6)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '3: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[1].name)
        self.assertIn(_(
            '4: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[2].name)
        self.assertIn(_(
            '5: Product template \'Template 2\' not found, will be created.'),
            wizard.line_ids[3].name)
        self.assertIn(_(
            '6: Product template \'Template 2\' not found, will be created.'),
            wizard.line_ids[4].name)
        self.assertIn(_(
            '7: Product template \'Template 2\' not found, will be created.'),
            wizard.line_ids[5].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 2)
        self.assertEquals(wizard.total_error, 0)
        self.assertIn(_(
            '2: Product template \'Template 1\' not found, will be created.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '5: Product template \'Template 2\' not found, will be created.'),
            wizard.line_ids[1].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(product_tmpls_1.name, 'Template 1')
        self.assertEquals(product_tmpls_1.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_1.categ_id.parent_id)
        self.assertEquals(product_tmpls_1.type, 'service')
        self.assertTrue(product_tmpls_1.sale_ok)
        self.assertFalse(product_tmpls_1.purchase_ok)
        self.assertEquals(product_tmpls_1.list_price, 15.99)
        self.assertEquals(product_tmpls_1.invoice_policy, 'delivery')
        self.assertFalse(product_tmpls_1.image)
        self.assertFalse(product_tmpls_1.product_image_ids)
        for product in product_tmpls_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['White', 'S']:
                self.assertTrue(product.image_variant)
            else:
                self.assertFalse(product.image_variant)
        self.assertEquals(
            product_tmpls_1.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_1.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_1.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.product_brand_id, self.brand_1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 3)
        variant_WS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'S'])
        self.assertEquals(len(variant_WS), 1)
        self.assertEquals(variant_WS.default_code, 'PROD1_WS')
        self.assertEquals(variant_WS.barcode, '4050119164021')
        self.assertEquals(variant_WS.standard_price, 10.5)
        variant_WM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'M'])
        self.assertEquals(len(variant_WM), 1)
        self.assertEquals(variant_WM.default_code, 'PROD1_WM')
        self.assertEquals(variant_WM.barcode, '4050119164038')
        self.assertEquals(variant_WM.standard_price, 20)
        variant_WL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'L'])
        self.assertEquals(len(variant_WL), 1)
        self.assertEquals(variant_WL.default_code, 'PROD1_WL')
        self.assertEquals(variant_WL.barcode, '4050119164106')
        self.assertEquals(variant_WL.standard_price, 25)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(len(product_tmpls_2.attribute_line_ids), 2)
        self.assertEquals(product_tmpls_2.name, 'Template 2')
        self.assertEquals(product_tmpls_2.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_2.categ_id.parent_id)
        self.assertEquals(product_tmpls_2.type, 'service')
        self.assertTrue(product_tmpls_2.sale_ok)
        self.assertFalse(product_tmpls_2.purchase_ok)
        self.assertEquals(product_tmpls_2.list_price, 15.99)
        self.assertEquals(product_tmpls_2.invoice_policy, 'delivery')
        self.assertFalse(product_tmpls_2.image)
        self.assertFalse(product_tmpls_2.product_image_ids)
        for product in product_tmpls_2.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['White', '10']:
                self.assertTrue(product.image_variant)
            else:
                self.assertFalse(product.image_variant)
        self.assertEquals(
            product_tmpls_2.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_2.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_2.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_2.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_2.product_brand_id, self.brand_1)
        color_line = product_tmpls_2.attribute_line_ids.filtered(
            lambda ln: ln.attribute_id.name == 'Color')
        self.assertEquals(len(color_line), 1)
        color_values = color_line.value_ids.mapped('name')
        self.assertEquals(len(color_values), 2)
        self.assertIn('White', color_values)
        self.assertIn('Red', color_values)
        lenght_line = product_tmpls_2.attribute_line_ids.filtered(
            lambda ln: ln.attribute_id.name == 'Lenght')
        self.assertEquals(len(lenght_line), 1)
        lenght_values = lenght_line.value_ids.mapped('name')
        self.assertEquals(len(lenght_values), 2)
        self.assertIn('10', lenght_values)
        self.assertIn('50', lenght_values)
        self.assertEquals(len(product_tmpls_2.product_variant_ids), 4)
        variant_W10 = product_tmpls_2.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', '10'])
        self.assertEquals(len(variant_W10), 1)
        self.assertEquals(variant_W10.default_code, 'PROD2_W10')
        self.assertEquals(variant_W10.barcode, '4050119164083')
        self.assertEquals(variant_W10.standard_price, 10.5)
        variant_R10 = product_tmpls_2.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Red', '10'])
        self.assertEquals(len(variant_R10), 1)
        self.assertEquals(variant_R10.default_code, 'PROD2_R10')
        self.assertEquals(variant_R10.barcode, '4050119164090')
        self.assertEquals(variant_R10.standard_price, 20)
        variant_R50 = product_tmpls_2.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Red', '50'])
        self.assertEquals(len(variant_R50), 1)
        self.assertEquals(variant_R50.default_code, '')
        self.assertEquals(variant_R50.barcode, '')
        self.assertEquals(variant_R50.standard_price, 25)
        attr_val_50 = self.env['product.attribute.value'].search([
            ('name', '=', '50'),
            ('attribute_id', '=', self.attr_lenght.id),
        ])
        self.assertEquals(len(attr_val_50), 1)
        attr_val_red = self.env['product.attribute.value'].search([
            ('name', '=', 'Red'),
            ('attribute_id', '=', self.attr_color.id),
        ])
        self.assertEquals(len(attr_val_red), 1)

    def test_import_write_without_images(self):
        self.env['product.template'].create({
            'name': 'Product 1 test',
            'type': 'service',
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL1TEST',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr_color.id,
                    'value_ids': [(6, 0, self.attr_color.value_ids.ids)],
                }),
                (0, 0, {
                    'attribute_id': self.attr_size.id,
                    'value_ids': [(6, 0, self.attr_size.value_ids.ids)],
                }),
            ],
        })
        self.env['product.template'].create({
            'name': 'Product 2 test',
            'type': 'service',
            'standard_price': 80,
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL2TEST',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': self.attr_color.id,
                    'value_ids': [(6, 0, self.attr_color.value_ids.ids)],
                }),
                (0, 0, {
                    'attribute_id': self.attr_lenght.id,
                    'value_ids': [(6, 0, self.attr_lenght.value_ids.ids)],
                }),
            ],
        })
        fname = self.get_sample('sample_images_empty_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        self.assertEquals(product_tmpls_1.name, 'Template 1')
        self.assertEquals(product_tmpls_1.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_1.categ_id.parent_id)
        self.assertEquals(product_tmpls_1.type, 'service')
        self.assertTrue(product_tmpls_1.sale_ok)
        self.assertFalse(product_tmpls_1.purchase_ok)
        self.assertEquals(product_tmpls_1.list_price, 15.99)
        self.assertEquals(product_tmpls_1.invoice_policy, 'delivery')
        self.assertFalse(product_tmpls_1.image)
        self.assertFalse(product_tmpls_1.product_image_ids)
        for product in product_tmpls_1.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['White', 'S']:
                self.assertTrue(product.image_variant)
            else:
                self.assertFalse(product.image_variant)
        self.assertEquals(
            product_tmpls_1.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_1.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_1.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_1.product_brand_id, self.brand_1)
        self.assertEquals(len(product_tmpls_1.product_variant_ids), 6)
        variant_WS = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'S'])
        self.assertEquals(len(variant_WS), 1)
        self.assertEquals(variant_WS.default_code, 'PROD1_WS')
        self.assertEquals(variant_WS.barcode, '4050119164021')
        self.assertEquals(variant_WS.standard_price, 10.5)
        variant_WM = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'M'])
        self.assertEquals(len(variant_WM), 1)
        self.assertEquals(variant_WM.default_code, 'PROD1_WM')
        self.assertEquals(variant_WM.barcode, '4050119164038')
        self.assertEquals(variant_WM.standard_price, 20)
        variant_WL = product_tmpls_1.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', 'L'])
        self.assertEquals(len(variant_WL), 1)
        self.assertEquals(variant_WL.default_code, 'PROD1_WL')
        self.assertEquals(variant_WL.barcode, '4050119164106')
        self.assertEquals(variant_WL.standard_price, 25)
        variants_black = product_tmpls_1.product_variant_ids.filtered(
            lambda p: 'Black' in p.attribute_value_ids.mapped('name'))
        self.assertEquals(len(variants_black), 3)
        for variant_black in variants_black:
            self.assertFalse(variant_black.image_variant)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertEquals(len(product_tmpls_2.attribute_line_ids), 2)
        self.assertEquals(product_tmpls_2.name, 'Template 2')
        self.assertEquals(product_tmpls_2.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_2.categ_id.parent_id)
        self.assertEquals(product_tmpls_2.type, 'service')
        self.assertTrue(product_tmpls_2.sale_ok)
        self.assertFalse(product_tmpls_2.purchase_ok)
        self.assertEquals(product_tmpls_2.list_price, 15.99)
        self.assertEquals(product_tmpls_2.invoice_policy, 'delivery')
        self.assertFalse(product_tmpls_2.image)
        self.assertFalse(product_tmpls_2.product_image_ids)
        for product in product_tmpls_2.product_variant_ids:
            if product.attribute_value_ids.mapped('name') == ['White', '10']:
                self.assertTrue(product.image_variant)
            else:
                self.assertFalse(product.image_variant)
        self.assertEquals(
            product_tmpls_2.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_2.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_2.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_2.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_2.product_brand_id, self.brand_1)
        color_line = product_tmpls_2.attribute_line_ids.filtered(
            lambda ln: ln.attribute_id.name == 'Color')
        self.assertEquals(len(color_line), 1)
        color_values = color_line.value_ids.mapped('name')
        self.assertEquals(len(color_values), 3)
        self.assertIn('White', color_values)
        self.assertIn('Black', color_values)
        self.assertIn('Red', color_values)
        lenght_line = product_tmpls_2.attribute_line_ids.filtered(
            lambda ln: ln.attribute_id.name == 'Lenght')
        self.assertEquals(len(lenght_line), 1)
        lenght_values = lenght_line.value_ids.mapped('name')
        self.assertEquals(len(lenght_values), 3)
        self.assertIn('10', lenght_values)
        self.assertIn('20', lenght_values)
        self.assertIn('50', lenght_values)
        self.assertEquals(len(product_tmpls_2.product_variant_ids), 9)
        variant_W10 = product_tmpls_2.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['White', '10'])
        self.assertEquals(len(variant_W10), 1)
        self.assertEquals(variant_W10.default_code, 'PROD2_W10')
        self.assertEquals(variant_W10.barcode, '4050119164083')
        self.assertEquals(variant_W10.standard_price, 10.5)
        variant_R10 = product_tmpls_2.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Red', '10'])
        self.assertEquals(len(variant_R10), 1)
        self.assertEquals(variant_R10.default_code, 'PROD2_R10')
        self.assertEquals(variant_R10.barcode, '4050119164090')
        self.assertEquals(variant_R10.standard_price, 20)
        variant_R50 = product_tmpls_2.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Red', '50'])
        self.assertEquals(len(variant_R50), 1)
        self.assertEquals(variant_R50.default_code, '')
        self.assertEquals(variant_R50.barcode, '')
        self.assertEquals(variant_R50.standard_price, 25)
        attr_val_50 = self.env['product.attribute.value'].search([
            ('name', '=', '50'),
            ('attribute_id', '=', self.attr_lenght.id),
        ])
        self.assertEquals(len(attr_val_50), 1)
        attr_val_red = self.env['product.attribute.value'].search([
            ('name', '=', 'Red'),
            ('attribute_id', '=', self.attr_color.id),
        ])
        self.assertEquals(len(attr_val_red), 1)
