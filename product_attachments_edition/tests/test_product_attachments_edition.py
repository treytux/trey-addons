###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo import Command
from odoo.tests.common import TransactionCase


class TestProductAttachmentsEdition(TransactionCase):

    def setUp(self):
        super().setUp()
        self.category = self.env['product.category'].create({
            'name': 'Attachment test category',
        })
        self.product_template = self.env['product.template'].create({
            'name': 'Attachment test product',
            'categ_id': self.category.id,
        })
        self.product_variant = self.product_template.product_variant_id
        self.file_data = base64.b64encode(b'test attachment')

    def _attachment_values(self, name):
        return {
            'name': name,
            'datas': self.file_data,
            'type': 'binary',
        }

    def test_template_attachment_is_linked_to_template(self):
        self.product_template.write({
            'attachment_template_ids': [Command.create(
                self._attachment_values('template.txt'))],
        })
        attachment = self.product_template.attachment_template_ids
        self.assertEqual(len(attachment), 1)
        self.assertEqual(attachment.res_model, 'product.template')
        self.assertEqual(attachment.res_id, self.product_template.id)

    def test_variant_attachment_is_linked_to_variant(self):
        self.product_variant.write({
            'attachment_product_ids': [Command.create(
                self._attachment_values('variant.txt'))],
        })
        attachment = self.product_variant.attachment_product_ids
        self.assertEqual(len(attachment), 1)
        self.assertEqual(attachment.res_model, 'product.product')
        self.assertEqual(attachment.res_id, self.product_variant.id)

    def test_category_attachment_is_linked_to_category(self):
        self.category.write({
            'attachment_category_ids': [Command.create(
                self._attachment_values('category.txt'))],
        })
        attachment = self.category.attachment_category_ids
        self.assertEqual(len(attachment), 1)
        self.assertEqual(attachment.res_model, 'product.category')
        self.assertEqual(attachment.res_id, self.category.id)

    def test_attachments_are_isolated_by_model_and_record(self):
        other_category = self.env['product.category'].create({
            'name': 'Other attachment test category',
        })
        self.category.write({
            'attachment_category_ids': [Command.create(
                self._attachment_values('category.txt'))],
        })
        self.assertTrue(self.category.attachment_category_ids)
        self.assertFalse(other_category.attachment_category_ids)
        self.assertFalse(self.product_template.attachment_template_ids)
        self.assertFalse(self.product_variant.attachment_product_ids)

    def test_attachment_can_be_removed(self):
        self.category.write({
            'attachment_category_ids': [Command.create(
                self._attachment_values('category.txt'))],
        })
        attachment = self.category.attachment_category_ids
        self.category.write({
            'attachment_category_ids': [Command.unlink(attachment.id)],
        })
        self.assertFalse(self.category.attachment_category_ids)
        self.assertTrue(attachment.exists())
        self.assertFalse(attachment.res_id)

    def test_category_form_contains_attachment_field(self):
        view = self.category.get_view(
            view_id=self.env.ref(
                'product_attachments_edition.product_category_form_view').id,
            view_type='form')
        self.assertIn('attachment_category_ids', view['arch'])
