###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestVariantTemplateAttachments(TransactionCase):
    def setUp(self):
        super().setUp()
        product_template_obj = self.env['product.template']
        self.product_template = product_template_obj.create({
            'name': 'Test Product Template',
            'sale_ok': True,
            'purchase_ok': True,
            'type': 'consu',
            'attribute_line_ids': [[0, 0, {
                'attribute_id': self.env.ref('product.product_attribute_1').id,
                'value_ids': [
                    (4, self.env.ref('product.product_attribute_value_1').id),
                    (4, self.env.ref('product.product_attribute_value_2').id),
                ],
            }]]
        })

    def test_attachment_in_template_and_variants(self):
        variant1 = self.product_template.product_variant_ids[0]
        variant2 = self.product_template.product_variant_ids[1]
        self.assertFalse(self.product_template.message_attachment_count)
        self.assertFalse(variant1.message_attachment_count)
        self.assertFalse(variant2.message_attachment_count)
        attachment = self.env['ir.attachment'].create({
            'name': 'Test Attachment',
            'type': 'binary',
            'datas_fname': 'Test Attachment.txt',
            'res_model': 'product.template',
            'res_id': self.product_template.id,
            'mimetype': 'application/txt',
        })
        self.product_template.refresh()
        self.assertEqual(self.product_template.message_attachment_count, 1)
        self.assertEqual(variant1.message_attachment_count, 1)
        self.assertEqual(variant2.message_attachment_count, 1)
        self.env['ir.attachment'].create({
            'name': 'Test Attachment in variant',
            'type': 'binary',
            'datas_fname': 'Test Attachment.txt',
            'res_model': 'product.product',
            'res_id': variant1.id,
            'mimetype': 'application/txt',
        })
        self.product_template.refresh()
        self.assertEqual(self.product_template.message_attachment_count, 1)
        self.assertEqual(variant1.message_attachment_count, 2)
        self.assertEqual(variant2.message_attachment_count, 1)
        attachment.unlink()
        self.assertFalse(self.product_template.message_attachment_count)
        self.assertEqual(variant1.message_attachment_count, 1)
        self.assertFalse(variant2.message_attachment_count)
