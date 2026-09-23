###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
from io import BytesIO

from odoo import _
from odoo.exceptions import UserError
from odoo.tests import TransactionCase
from PIL import Image, ImageDraw
from PyPDF2 import PdfFileReader
from reportlab.pdfgen import canvas


class TestDocumentPagePdfSignature(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.page_model = cls.env['document.page']
        cls.attachment_model = cls.env['ir.attachment']

    def _create_page(self, **values):
        default_values = {
            'name': 'Signable page',
            'content': '<p>Document content</p>',
            'allow_pdf_signature': True,
            'signature_page': 1,
            'signature_position': 'bottom_right',
            'signature_x': 1.0,
            'signature_y': 1.0,
            'signature_width': 2.0,
            'signature_height': 1.0,
        }
        default_values.update(values)
        return self.page_model.create(default_values)

    def _create_pdf_attachment(self, page, name='document.pdf', content=None):
        content = content or self._create_pdf()
        return self.attachment_model.create({
            'name': name,
            'datas': base64.b64encode(content),
            'mimetype': 'application/pdf',
            'res_id': page.id,
            'res_model': 'document.page',
        })

    def _create_text_attachment(self, page):
        return self.attachment_model.create({
            'name': 'document.txt',
            'datas': base64.b64encode(b'Test content'),
            'mimetype': 'text/plain',
            'res_id': page.id,
            'res_model': 'document.page',
        })

    def _create_pdf(self, pages=1, width=300, height=300):
        buffer = BytesIO()
        pdf_canvas = canvas.Canvas(buffer, pagesize=(width, height))
        for page_number in range(pages):
            pdf_canvas.drawString(
                20, height - 40, 'Page %s' % (page_number + 1))
            pdf_canvas.showPage()
        pdf_canvas.save()
        return buffer.getvalue()

    def _create_signature(self):
        image = Image.new('RGBA', (120, 40), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        draw.line(
            (5, 25, 40, 10, 80, 30, 115, 8), fill=(0, 0, 0, 255), width=3)
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()

    def test_sign_pdf_attachment_replaces_original_pdf(self):
        page = self._create_page()
        attachment = self._create_pdf_attachment(page)
        original_data = attachment.datas
        signature = self._create_signature()
        result = page.action_sign_pdf_attachment('Employee', signature)
        signed_content = base64.b64decode(attachment.datas)
        reader = PdfFileReader(BytesIO(signed_content))
        self.assertTrue(result)
        self.assertTrue(page.pdf_signed)
        self.assertEqual(page.pdf_signed_by, 'Employee')
        self.assertTrue(page.pdf_signed_on)
        self.assertNotEqual(attachment.datas, original_data)
        self.assertEqual(attachment.mimetype, 'application/pdf')
        self.assertEqual(reader.numPages, 1)

    def test_not_signable_page_is_rejected(self):
        page = self._create_page(allow_pdf_signature=False)
        self._create_pdf_attachment(page)
        signature = self._create_signature()
        with self.assertRaises(UserError) as res:
            page.action_sign_pdf_attachment('Employee', signature)
        self.assertIn(
            _('This knowledge page does not allow signatures.'),
            res.exception.args[0])

    def test_already_signed_page_is_rejected(self):
        page = self._create_page(pdf_signed=True)
        self._create_pdf_attachment(page)
        signature = self._create_signature()
        with self.assertRaises(UserError) as res:
            page.action_sign_pdf_attachment('Employee', signature)
        self.assertIn(
            _('This PDF has already been signed.'), res.exception.args[0])

    def test_page_without_attachment_is_rejected(self):
        page = self._create_page()
        signature = self._create_signature()
        with self.assertRaises(UserError) as res:
            page.action_sign_pdf_attachment('Employee', signature)
        self.assertIn(
            _('A signable knowledge page must have exactly one attachment.'),
            res.exception.args[0])

    def test_page_with_multiple_attachments_is_rejected(self):
        page = self._create_page()
        self._create_pdf_attachment(page, name='first.pdf')
        self._create_pdf_attachment(page, name='second.pdf')
        signature = self._create_signature()
        with self.assertRaises(UserError) as res:
            page.action_sign_pdf_attachment('Employee', signature)
        self.assertIn(
            _('A signable knowledge page must have exactly one attachment.'),
            res.exception.args[0])

    def test_non_pdf_attachment_is_rejected(self):
        page = self._create_page()
        self._create_text_attachment(page)
        signature = self._create_signature()
        with self.assertRaises(UserError) as res:
            page.action_sign_pdf_attachment('Employee', signature)
        self.assertIn(
            _('The attachment to sign must be a PDF file.'),
            res.exception.args[0])

    def test_signature_outside_page_width_is_rejected(self):
        page = self._create_page(
            signature_position='custom',
            signature_x=9.0,
            signature_width=3.0)
        self._create_pdf_attachment(page)
        signature = self._create_signature()
        with self.assertRaises(UserError) as res:
            page.action_sign_pdf_attachment('Employee', signature)
        self.assertIn(
            _('The signature exceeds the PDF page width.'),
            res.exception.args[0])

    def test_signature_outside_page_height_is_rejected(self):
        page = self._create_page(
            signature_position='custom',
            signature_y=9.0,
            signature_height=3.0)
        self._create_pdf_attachment(page)
        signature = self._create_signature()
        with self.assertRaises(UserError) as res:
            page.action_sign_pdf_attachment('Employee', signature)
        self.assertIn(
            _('The signature exceeds the PDF page height.'),
            res.exception.args[0])

    def test_missing_pdf_page_is_rejected(self):
        page = self._create_page(signature_page=2)
        self._create_pdf_attachment(page)
        signature = self._create_signature()
        with self.assertRaises(UserError) as res:
            page.action_sign_pdf_attachment('Employee', signature)
        self.assertIn(
            _('The signature page does not exist in the PDF.'),
            res.exception.args[0])

    def test_automatic_position_ignores_custom_xy_values(self):
        page = self._create_page(
            signature_position='bottom_right', signature_x=50.0,
            signature_y=50.0, signature_width=2.0, signature_height=1.0)
        attachment = self._create_pdf_attachment(page)
        signature = self._create_signature()
        page.action_sign_pdf_attachment('Employee', signature)
        self.assertTrue(page.pdf_signed)
        self.assertEqual(attachment.mimetype, 'application/pdf')

    def test_onchange_updates_reference_xy_for_automatic_position(self):
        page = self._create_page(
            signature_position='bottom_right', signature_width=2.0,
            signature_height=1.0, signature_x=50.0, signature_y=50.0)
        self._create_pdf_attachment(
            page, content=self._create_pdf(width=300, height=300))
        page._onchange_signature_reference_xy()
        self.assertAlmostEqual(page.signature_x, 8.58, places=2)
        self.assertAlmostEqual(page.signature_y, 0.0, places=2)

    def test_onchange_keeps_manual_xy_for_custom_position(self):
        page = self._create_page(
            signature_position='custom', signature_x=4.0, signature_y=5.0)
        self._create_pdf_attachment(page)
        page._onchange_signature_reference_xy()
        self.assertEqual(page.signature_x, 4.0)
        self.assertEqual(page.signature_y, 5.0)
