###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestProductAutoDefaultCodeByCodeSeqType(TransactionCase):

    def setUp(self):
        super().setUp()
        self.all_category = self.env.ref('product.product_category_all')

    def test_constraint_check_code_seq(self):
        self.all_category.code_seq = 'AB'
        with self.assertRaises(ValidationError) as result:
            self.env['product.category'].create({
                'name': 'Test category',
                'code_seq': 'AB',
            })
        self.assertIn(
            'Error! Code already exists. The code must be unique.',
            result.exception.args[0])

    def test_constraint_check_default_code(self):
        product_tmpl_01 = self.env['product.template'].create({
            'name': 'Test product 1',
            'detailed_type': 'service',
            'code_seq_type': 'C',
            'categ_id': self.all_category.id,
        })
        default_code = 'C-XX%s' % str(
            product_tmpl_01.product_variant_id.id).zfill(5)
        self.assertEqual(product_tmpl_01.default_code, default_code)
        with self.assertRaises(ValidationError) as result:
            self.env['product.template'].create({
                'name': 'Test product duply',
                'detailed_type': 'service',
                'code_seq_type': 'C',
                'categ_id': self.all_category.id,
                'default_code': default_code,
            })
        self.assertIn(
            'Error! The default code %s already exists.' % default_code,
            result.exception.args[0])

    def test_create_auto_default_code_from_product_tmpl_without_code_suffix(
            self):
        product_tmpl_01 = self.env['product.template'].create({
            'name': 'Test product 1',
            'detailed_type': 'service',
            'code_seq_type': 'C',
            'categ_id': self.all_category.id,
        })
        self.assertEqual(product_tmpl_01.products_count, 1)
        default_code = 'C-XX%s' % str(
            product_tmpl_01.product_variant_id.id).zfill(5)
        self.assertEqual(product_tmpl_01.default_code, default_code)
        self.all_category.code_seq = 'AB'
        product_tmpl_02 = self.env['product.template'].create({
            'name': 'Test product 2',
            'detailed_type': 'service',
            'code_seq_type': 'C',
            'categ_id': self.all_category.id,
        })
        self.assertEqual(product_tmpl_02.products_count, 1)
        default_code2 = 'C-AB%s' % str(
            product_tmpl_02.product_variant_id.id).zfill(5)
        self.assertEqual(product_tmpl_02.default_code, default_code2)

    def test_write_auto_default_code_from_product_tmpl_without_code_suffix(
            self):
        product_tmpl_01 = self.env['product.template'].create({
            'name': 'Test product 1',
            'detailed_type': 'service',
            'code_seq_type': 'C',
            'categ_id': self.all_category.id,
        })
        self.assertEqual(product_tmpl_01.products_count, 1)
        default_code = 'C-XX%s' % str(
            product_tmpl_01.product_variant_id.id).zfill(5)
        self.assertEqual(product_tmpl_01.default_code, default_code)
        product_tmpl_01.name = 'Test product 1 modified'
        self.assertEqual(product_tmpl_01.default_code, default_code)

    def test_create_auto_default_code_from_product_product_with_code_suffix(
            self):
        product_01 = self.env['product.product'].create({
            'name': 'Test product 1',
            'detailed_type': 'service',
            'code_suffix': 'SF',
            'code_seq_type': 'C',
            'categ_id': self.all_category.id,
        })
        self.assertEqual(product_01.product_tmpl_id.products_count, 1)
        default_code = 'C-XX%s-SF' % str(product_01.id).zfill(5)
        self.assertEqual(product_01.default_code, default_code)
        self.all_category.code_seq = 'AB'
        product_02 = self.env['product.product'].create({
            'name': 'Test product 2',
            'detailed_type': 'service',
            'code_seq_type': 'C',
            'categ_id': self.all_category.id,
        })
        self.assertEqual(product_02.product_tmpl_id.products_count, 1)
        default_code2 = 'C-AB%s' % str(product_02.id).zfill(5)
        self.assertEqual(product_02.default_code, default_code2)

    def test_write_auto_default_code_from_product_product_with_code_suffix(
            self):
        product_01 = self.env['product.product'].create({
            'name': 'Test product 1',
            'detailed_type': 'service',
            'code_suffix': 'SF',
            'code_seq_type': 'C',
            'categ_id': self.all_category.id,
        })
        self.assertEqual(product_01.product_tmpl_id.products_count, 1)
        default_code = 'C-XX%s-SF' % str(product_01.id).zfill(5)
        self.assertEqual(product_01.default_code, default_code)
        product_01.name = 'Test product 1 modified'
        self.assertEqual(product_01.default_code, default_code)

    def test_create_auto_default_code_product_tmpl_variants(self):
        attr = self.env['product.attribute'].create({
            'name': 'Attribute test',
        })
        for value in ['A', 'B']:
            self.env['product.attribute.value'].create({
                'attribute_id': attr.id,
                'name': value,
            })
        product_tmpl_01 = self.env['product.template'].create({
            'name': 'Test product with variants',
            'detailed_type': 'service',
            'code_seq_type': 'C',
            'categ_id': self.all_category.id,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': attr.id,
                    'value_ids': [(6, 0, attr.value_ids.ids)],
                }),
            ],
        })
        self.assertEqual(len(product_tmpl_01.product_variant_ids), 2)
        self.assertEqual(product_tmpl_01.products_count, 2)
        default_code_variant_1 = 'C-XX%s' % str(
            product_tmpl_01.product_variant_ids[0].id).zfill(5)
        default_code_variant_2 = 'C-XX%s' % str(
            product_tmpl_01.product_variant_ids[1].id).zfill(5)
        self.assertIn(default_code_variant_1, product_tmpl_01.default_code)
        self.assertIn(default_code_variant_2, product_tmpl_01.default_code)
        self.assertEqual(
            product_tmpl_01.product_variant_ids[0].default_code,
            default_code_variant_1)
        self.assertEqual(
            product_tmpl_01.product_variant_ids[1].default_code,
            default_code_variant_2)
        product_tmpl_01.product_variant_ids[0].default_code = 'Wrongcode1'
        product_tmpl_01.product_variant_ids[1].default_code = 'Wrongcode2'
        product_tmpl_01.product_variant_ids.write({'default_code': False})
        self.assertEqual(
            product_tmpl_01.product_variant_ids[0].default_code,
            default_code_variant_1)
        self.assertEqual(
            product_tmpl_01.product_variant_ids[1].default_code,
            default_code_variant_2)
