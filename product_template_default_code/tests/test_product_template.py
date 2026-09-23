###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductTemplate(TransactionCase):

    def test_product_template(self):
        template = self.env['product.template'].create({
            'name': 'Test Purchase Product',
            'default_code': 'TEST',
        })
        self.assertEqual(len(template.product_variant_ids), 1)
        template.default_code = 'TEST'
        self.assertEqual(template.default_code, 'TEST')
        self.assertEqual(template.product_variant_id.default_code, 'TEST')
        template.product_variant_id.default_code = 'TEST-VARIANT'
        self.assertEqual(template.default_code, 'TEST-VARIANT')
        self.assertEqual(template.default_code_template, 'TEST-VARIANT')
        self.assertEqual(
            template.product_variant_id.default_code, 'TEST-VARIANT')
        template.default_code = 'TEST'
        self.assertEqual(template.default_code, 'TEST')
        self.assertEqual(template.product_variant_id.default_code, 'TEST')
        first_variant = template.product_variant_id
        attr = self.env['product.attribute'].create({
            'name': 'Attribute test',
        })
        for value in ['A', 'B', 'C']:
            self.env['product.attribute.value'].create({
                'attribute_id': attr.id,
                'name': value,
            })
        template.attribute_line_ids = [
            (0, 0, {
                'attribute_id': attr.id,
                'value_ids': [(6, 0, attr.value_ids.ids)],
            }),
        ]
        self.assertEqual(len(template.product_variant_ids), 3)
        self.assertFalse(first_variant.exists())
        self.assertNotIn(first_variant, template.product_variant_ids)
        self.assertEqual(template.default_code, 'TEST')
        template.default_code = 'TEST-OTHER'
        self.assertEqual(template.default_code, 'TEST-OTHER')
        default_codes = template.product_variant_ids.mapped('default_code')
        self.assertFalse(any(default_codes))
        template.product_variant_ids[0].default_code = 'TEST-A'
        self.assertEqual(template.default_code, 'TEST-OTHER')
        self.assertIn(
            'TEST-A', template.product_variant_ids.mapped('default_code'))
        template.product_variant_ids[1].default_code = 'TEST-B'
        self.assertEqual(template.default_code, 'TEST-OTHER')
        self.assertIn(
            'TEST-B', template.product_variant_ids.mapped('default_code'))
        template.product_variant_ids[2].default_code = 'TEST-C'
        self.assertEqual(template.default_code, 'TEST-OTHER')
        self.assertIn(
            'TEST-C', template.product_variant_ids.mapped('default_code'))
