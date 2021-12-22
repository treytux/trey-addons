###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os

from odoo import _
from odoo.tests.common import TransactionCase


class TestImportTemplateProductVariant(TransactionCase):

    def setUp(self):
        super().setUp()
        self.categ_1 = self.env['product.category'].create({
            'name': 'Categ 1',
        })
        self.brand_1 = self.env['product.brand'].create({
            'name': 'Brand 1',
        })
        self.env['hs.code'].create({
            'local_code': '847150',
        })
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

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def get_file_name(self, fname):
        return fname.split('/')[-1:][0]

    def test_import_create_with_country_and_origin_country_id(self):
        fname = self.get_sample('sample_three_attributes_exists_harmonized.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 7)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 6)
        self.assertIn(_(
            '5: The HS code with local code \'123456\' does not exist, '
            'select one of the available ones.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '5: The country \'New country\' does not exist, select one '
            'of the available ones.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '6: The HS code with local code \'123456\' does not exist, '
            'select one of the available ones.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '6: The country \'New country\' does not exist, select one '
            'of the available ones.'), wizard.line_ids[3].name)
        self.assertIn(_(
            '7: The HS code with local code \'123456\' does not exist, '
            'select one of the available ones.'), wizard.line_ids[4].name)
        self.assertIn(_(
            '7: The country \'New country\' does not exist, select one '
            'of the available ones.'), wizard.line_ids[5].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 0)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 0)
        product_tmpls_3 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL3TEST'),
        ])
        self.assertEquals(len(product_tmpls_3), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 7)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 6)
        self.assertIn(_(
            '5: The HS code with local code \'123456\' does not exist, '
            'select one of the available ones.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '5: The country \'New country\' does not exist, select one '
            'of the available ones.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '6: The HS code with local code \'123456\' does not exist, '
            'select one of the available ones.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '6: The country \'New country\' does not exist, select one '
            'of the available ones.'), wizard.line_ids[3].name)
        self.assertIn(_(
            '7: The HS code with local code \'123456\' does not exist, '
            'select one of the available ones.'), wizard.line_ids[4].name)
        self.assertIn(_(
            '7: The country \'New country\' does not exist, select one '
            'of the available ones.'), wizard.line_ids[5].name)
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
        self.assertEquals(product_tmpls_1.origin_country_id.name, 'Spain')
        self.assertEquals(product_tmpls_1.hs_code_id.local_code, '847150')
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
        self.assertEquals(len(product_tmpls_2), 0)
        product_tmpls_3 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL3TEST'),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        self.assertEquals(len(product_tmpls_3.attribute_line_ids), 2)
        self.assertEquals(product_tmpls_3.name, 'PRODTMPL3TEST')
        self.assertEquals(product_tmpls_3.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_3.categ_id.parent_id)
        self.assertEquals(product_tmpls_3.type, 'service')
        self.assertTrue(product_tmpls_3.sale_ok)
        self.assertFalse(product_tmpls_3.purchase_ok)
        self.assertEquals(product_tmpls_3.list_price, 15.99)
        self.assertEquals(product_tmpls_3.invoice_policy, 'delivery')
        self.assertFalse(product_tmpls_3.image)
        self.assertFalse(product_tmpls_3.product_image_ids)
        self.assertEquals(
            product_tmpls_3.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_3.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_3.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_3.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_3.product_brand_id, self.brand_1)
        self.assertFalse(product_tmpls_3.origin_country_id.name)
        self.assertFalse(product_tmpls_3.hs_code_id.local_code)
        color_line = product_tmpls_3.attribute_line_ids.filtered(
            lambda ln: ln.attribute_id.name == 'Color')
        self.assertEquals(len(color_line), 1)
        color_values = color_line.value_ids.mapped('name')
        self.assertEquals(len(color_values), 1)
        self.assertIn('Red', color_values)
        lenght_line = product_tmpls_3.attribute_line_ids.filtered(
            lambda ln: ln.attribute_id.name == 'Lenght')
        self.assertEquals(len(lenght_line), 1)
        lenght_values = lenght_line.value_ids.mapped('name')
        self.assertEquals(len(lenght_values), 1)
        self.assertIn('50', lenght_values)
        self.assertEquals(len(product_tmpls_3.product_variant_ids), 1)
        variant_R50 = product_tmpls_3.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Red', '50'])
        self.assertEquals(variant_R50.default_code, '')
        self.assertEquals(variant_R50.barcode, '')
        self.assertEquals(variant_R50.standard_price, 25)

    def test_import_write_with_country_and_origin_country_id(self):
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
        self.env['product.template'].create({
            'name': 'Product 3 test',
            'type': 'service',
            'standard_price': 80,
            'list_price': 100,
            'product_tmpl_code': 'PRODTMPL3TEST',
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
        fname = self.get_sample('sample_three_attributes_exists_harmonized.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_product_variant.template_product_variant').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 7)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 6)
        self.assertIn(_(
            '5: The HS code with local code \'123456\' does not exist, '
            'select one of the available ones.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '5: The country \'New country\' does not exist, select one '
            'of the available ones.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '6: The HS code with local code \'123456\' does not exist, '
            'select one of the available ones.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '6: The country \'New country\' does not exist, select one '
            'of the available ones.'), wizard.line_ids[3].name)
        self.assertIn(_(
            '7: The HS code with local code \'123456\' does not exist, '
            'select one of the available ones.'), wizard.line_ids[4].name)
        self.assertIn(_(
            '7: The country \'New country\' does not exist, select one '
            'of the available ones.'), wizard.line_ids[5].name)
        product_tmpls_1 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL1TEST'),
        ])
        self.assertEquals(len(product_tmpls_1), 1)
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        product_tmpls_3 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL3TEST'),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.state, 'step_done')
        self.assertEquals(wizard.total_rows, 7)
        self.assertEquals(len(wizard.line_ids), 6)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 6)
        self.assertIn(_(
            '5: The HS code with local code \'123456\' does not exist, '
            'select one of the available ones.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '5: The country \'New country\' does not exist, select one '
            'of the available ones.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '6: The HS code with local code \'123456\' does not exist, '
            'select one of the available ones.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '6: The country \'New country\' does not exist, select one '
            'of the available ones.'), wizard.line_ids[3].name)
        self.assertIn(_(
            '7: The HS code with local code \'123456\' does not exist, '
            'select one of the available ones.'), wizard.line_ids[4].name)
        self.assertIn(_(
            '7: The country \'New country\' does not exist, select one '
            'of the available ones.'), wizard.line_ids[5].name)
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
        self.assertEquals(product_tmpls_1.origin_country_id.name, 'Spain')
        self.assertEquals(product_tmpls_1.hs_code_id.local_code, '847150')
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
        product_tmpls_2 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL2TEST'),
        ])
        self.assertEquals(len(product_tmpls_2), 1)
        self.assertFalse(product_tmpls_2.origin_country_id)
        self.assertFalse(product_tmpls_2.hs_code_id)
        product_tmpls_3 = self.env['product.template'].search([
            ('product_tmpl_code', '=', 'PRODTMPL3TEST'),
        ])
        self.assertEquals(len(product_tmpls_3), 1)
        self.assertEquals(len(product_tmpls_3.attribute_line_ids), 2)
        self.assertEquals(product_tmpls_3.name, 'Template 3')
        self.assertEquals(product_tmpls_3.categ_id.name, 'Categ 1')
        self.assertFalse(product_tmpls_3.categ_id.parent_id)
        self.assertEquals(product_tmpls_3.type, 'service')
        self.assertTrue(product_tmpls_3.sale_ok)
        self.assertFalse(product_tmpls_3.purchase_ok)
        self.assertEquals(product_tmpls_3.list_price, 15.99)
        self.assertEquals(product_tmpls_3.invoice_policy, 'delivery')
        self.assertFalse(product_tmpls_3.image)
        self.assertFalse(product_tmpls_3.product_image_ids)
        self.assertEquals(
            product_tmpls_3.description_sale, 'Description for customers.')
        self.assertEquals(
            product_tmpls_3.description_purchase, 'Description for suppliers.')
        self.assertEquals(product_tmpls_3.uom_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_3.uom_po_id.name, 'Unit(s)')
        self.assertEquals(product_tmpls_3.product_brand_id, self.brand_1)
        self.assertFalse(product_tmpls_3.origin_country_id.name)
        self.assertFalse(product_tmpls_3.hs_code_id.local_code)
        color_line = product_tmpls_3.attribute_line_ids.filtered(
            lambda ln: ln.attribute_id.name == 'Color')
        self.assertEquals(len(color_line), 1)
        color_values = color_line.value_ids.mapped('name')
        self.assertEquals(len(color_values), 3)
        self.assertIn('Red', color_values)
        lenght_line = product_tmpls_3.attribute_line_ids.filtered(
            lambda ln: ln.attribute_id.name == 'Lenght')
        self.assertEquals(len(lenght_line), 1)
        lenght_values = lenght_line.value_ids.mapped('name')
        self.assertEquals(len(lenght_values), 3)
        self.assertIn('50', lenght_values)
        self.assertEquals(len(product_tmpls_3.product_variant_ids), 9)
        variant_R50 = product_tmpls_3.product_variant_ids.filtered(
            lambda p: p.attribute_value_ids.mapped('name') == ['Red', '50'])
        self.assertEquals(variant_R50.default_code, '')
        self.assertEquals(variant_R50.barcode, '')
        self.assertEquals(variant_R50.standard_price, 25)
