###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64

from odoo.fields import Command
from odoo.tests import common


class TestDocumentPageAttachment(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.document_page_obj = self.env['document.page']
        self.ir_attachment_obj = self.env['ir.attachment']
        self.test_page = self.document_page_obj.create({
            'name': 'Test Page',
            'content': '<p>Test content</p>',
        })
        self.attachment_data = {
            'name': 'test_file.txt',
            'datas': base64.b64encode(b'Test Data').decode(),
            'mimetype': 'text/plain',
        }
        self.one_px_png = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\
            x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
            b'\x00\x00\x00\x0cIDATx\x9cc````\x00\x00\x00\x04\x00\
            x01\xf6\x03\xe0\x00\x00\x00\x00IEND\xaeB`\x82'
        )

    def test_create_attachment_via_one2many_sets_res_model(self):
        self.test_page.write({
            'attachment_page_ids': [Command.create(self.attachment_data)],
        })
        new_attachment = self.ir_attachment_obj.search([
            ('res_model', '=', 'document.page'),
            ('res_id', '=', self.test_page.id),
            ('name', '=', self.attachment_data['name']),
        ], limit=1)
        self.assertTrue(new_attachment)
        self.assertEqual(new_attachment.res_model, 'document.page')
        self.assertEqual(new_attachment.res_id, self.test_page.id)

    def test_attachment_linked_to_correct_page(self):
        second_page = self.document_page_obj.create({
            'name': 'Second Page',
            'content': '<p>Another page</p>',
        })
        self.test_page.write({
            'attachment_page_ids': [Command.create(self.attachment_data)],
        })
        second_page.write({
            'attachment_page_ids': [Command.create({
                'name': 'second_file.txt',
                'datas': base64.b64encode(b'Second file').decode(),
                'mimetype': 'text/plain',
            })],
        })
        test_page_attachments = self.ir_attachment_obj.search([
            ('res_model', '=', 'document.page'),
            ('res_id', '=', self.test_page.id),
        ])
        self.assertEqual(len(test_page_attachments), 1)
        self.assertEqual(
            test_page_attachments[0].name, self.attachment_data['name'])
        second_page_attachments = self.ir_attachment_obj.search([
            ('res_model', '=', 'document.page'),
            ('res_id', '=', second_page.id),
        ])
        self.assertEqual(len(second_page_attachments), 1)
        self.assertNotEqual(
            second_page_attachments[0].name, self.attachment_data['name'])

    def test_normal_write_without_attachment_page_ids(self):
        self.test_page.write({
            'attachment_page_ids': [Command.create(self.attachment_data)]
        })
        original_attachment = self.ir_attachment_obj.search([
            ('res_model', '=', 'document.page'),
            ('res_id', '=', self.test_page.id),
        ], limit=1)
        self.assertTrue(original_attachment)
        self.test_page.write({'name': 'Updated Page Name'})
        self.assertEqual(self.test_page.name, 'Updated Page Name')
        attachment_after = self.ir_attachment_obj.browse(
            original_attachment.id)
        self.assertTrue(attachment_after.exists())
        self.assertEqual(attachment_after.res_model, 'document.page')
        self.assertEqual(attachment_after.res_id, self.test_page.id)
        self.assertEqual(attachment_after.name, self.attachment_data['name'])
        self.test_page.write({})
        self.assertTrue(True)

    def test_multiple_attachments_creation(self):
        attachments_data = [
            {
                'name': 'test.txt',
                'datas': base64.b64encode(b'Test File').decode(),
                'mimetype': 'text/plain',
            },
            {
                'name': 'test_image.png',
                'datas': base64.b64encode(self.one_px_png).decode(),
                'mimetype': 'image/png',
            },
        ]
        commands = [Command.create(data) for data in attachments_data]
        self.test_page.write({'attachment_page_ids': commands})
        attachments = self.ir_attachment_obj.search([
            ('res_model', '=', 'document.page'),
            ('res_id', '=', self.test_page.id),
        ])
        self.assertEqual(len(attachments), 2)
