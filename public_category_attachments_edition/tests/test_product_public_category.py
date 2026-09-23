###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo.tests.common import TransactionCase


class TestProductPublicCategoryAttachments(TransactionCase):

    def test_create_attachment_from_public_category(self):
        category = self.env['product.public.category'].create({
            'name': 'Test public category',
        })
        category.write({
            'attachment_public_cat_ids': [(0, 0, {
                'name': 'test.txt',
                'datas': base64.b64encode(b'Test attachment'),
            })],
        })
        attachment = category.attachment_public_cat_ids
        self.assertEqual(len(attachment), 1)
        self.assertEqual(attachment.name, 'test.txt')
        self.assertEqual(attachment.res_model, 'product.public.category')
        self.assertEqual(attachment.res_id, category.id)

    def test_public_category_attachment_domain(self):
        category = self.env['product.public.category'].create({
            'name': 'Test public category',
        })
        partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })
        attachment = self.env['ir.attachment'].create({
            'name': 'partner.txt',
            'datas': base64.b64encode(b'Partner attachment'),
            'res_model': 'res.partner',
            'res_id': partner.id,
        })
        self.assertNotIn(attachment, category.attachment_public_cat_ids)
