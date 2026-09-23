###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import binascii
import logging
from io import BytesIO

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from PIL import Image
from PyPDF2 import PdfFileReader, PdfFileWriter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

_logger = logging.getLogger(__name__)


class DocumentPage(models.Model):
    _inherit = 'document.page'
    _CM_TO_POINTS = 72.0 / 2.54
    _DEFAULT_PAGE_WIDTH_POINTS = 595.28
    _DEFAULT_PAGE_HEIGHT_POINTS = 841.89

    allow_pdf_signature = fields.Boolean(
        string='Allow PDF signature',
        help='Allow employees to sign the single PDF attached to this page.',
    )
    signature_page = fields.Integer(
        string='Signature page',
        default=1,
        help='PDF page number where the signature will be placed.',
    )
    signature_position = fields.Selection(
        selection=[
            ('top_left', 'Top Left'),
            ('top_center', 'Top Center'),
            ('top_right', 'Top Right'),
            ('middle_left', 'Middle Left'),
            ('middle_center', 'Middle Center'),
            ('middle_right', 'Middle Right'),
            ('bottom_left', 'Bottom Left'),
            ('bottom_center', 'Bottom Center'),
            ('bottom_right', 'Bottom Right'),
            ('custom', 'Custom'),
        ],
        string='Signature position',
        default='bottom_right',
        required=True,
        help='Automatic placement of the signature box on the page.',
    )
    signature_x = fields.Float(
        string='Signature X',
        default=2.0,
        help='Horizontal signature position in centimeters from the left.',
    )
    signature_y = fields.Float(
        string='Signature Y',
        default=2.0,
        help='Vertical signature position in centimeters from the bottom.',
    )
    signature_width = fields.Float(
        string='Signature width',
        default=6.0,
        help='Signature box width in centimeters.',
    )
    signature_height = fields.Float(
        string='Signature height',
        default=3.0,
        help='Signature box height in centimeters.',
    )
    pdf_signed = fields.Boolean(
        string='PDF signed',
        copy=False,
        readonly=True,
    )
    pdf_signed_by = fields.Char(
        string='PDF signed by',
        copy=False,
        readonly=True,
    )
    pdf_signed_on = fields.Datetime(
        string='PDF signed on',
        copy=False,
        readonly=True,
    )

    def _can_sign_pdf_from_portal(self):
        self.ensure_one()
        if not self.allow_pdf_signature or self.pdf_signed:
            return False
        attachments = self.attachment_page_ids
        return len(attachments) == 1 and self._is_pdf_attachment(attachments)

    @api.onchange(
        'signature_position', 'signature_page', 'signature_width',
        'signature_height')
    def _onchange_signature_reference_xy(self):
        for page in self:
            if page.signature_position == 'custom':
                continue
            page_width, page_height = page._get_reference_page_size_points()
            signature_width = page._cm_to_points(page.signature_width)
            signature_height = page._cm_to_points(page.signature_height)
            signature_x, signature_y = page._get_signature_xy(
                page_width, page_height, signature_width, signature_height)
            page.signature_x = page._points_to_cm(signature_x)
            page.signature_y = page._points_to_cm(signature_y)

    def _is_pdf_attachment(self, attachment):
        self.ensure_one()
        name = (attachment.name or '').lower()
        return attachment.mimetype == 'application/pdf' or name.endswith('.pdf')

    def _get_pdf_signature_attachment(self):
        self.ensure_one()
        attachments = self.attachment_page_ids
        if len(attachments) != 1:
            raise UserError(_(
                'A signable knowledge page must have exactly one attachment.'))
        attachment = attachments[0]
        if not self._is_pdf_attachment(attachment):
            raise UserError(_('The attachment to sign must be a PDF file.'))
        if not attachment.datas:
            raise UserError(_('The PDF attachment is empty.'))
        return attachment

    def action_sign_pdf_attachment(self, name, signature):
        self.ensure_one()
        if not name:
            raise UserError(_('Signer name is missing.'))
        self._check_pdf_signature_ready()
        attachment = self._get_pdf_signature_attachment()
        pdf_content = base64.b64decode(attachment.datas)
        signature_content = self._decode_signature(signature)
        signed_pdf = self._add_signature_to_pdf(pdf_content, signature_content)
        attachment.write({
            'datas': base64.b64encode(signed_pdf),
            'mimetype': 'application/pdf',
        })
        self.write({
            'pdf_signed': True,
            'pdf_signed_by': name,
            'pdf_signed_on': fields.Datetime.now(),
        })
        return True

    def _check_pdf_signature_ready(self):
        self.ensure_one()
        if not self.allow_pdf_signature:
            raise UserError(_('This knowledge page does not allow signatures.'))
        if self.pdf_signed:
            raise UserError(_('This PDF has already been signed.'))
        if not self.signature_page or self.signature_page < 1:
            raise UserError(_('The signature page must be greater than zero.'))
        if self.signature_width <= 0 or self.signature_height <= 0:
            raise UserError(_('The signature size must be greater than zero.'))
        if self.signature_position == 'custom' and (
                self.signature_x < 0 or self.signature_y < 0):
            raise UserError(_('The signature position cannot be negative.'))

    def _decode_signature(self, signature):
        if not signature:
            raise UserError(_('Signature is missing.'))
        if ',' in signature:
            signature = signature.split(',', 1)[1]
        try:
            content = base64.b64decode(signature)
            image = Image.open(BytesIO(content))
            image.verify()
        except (binascii.Error, OSError, ValueError) as error:
            raise UserError(_('Invalid signature data.')) from error
        return content

    def _add_signature_to_pdf(self, pdf_content, signature_content):
        self.ensure_one()
        try:
            reader = PdfFileReader(BytesIO(pdf_content))
            writer = PdfFileWriter()
        except Exception as error:
            raise UserError(_('Invalid PDF attachment.')) from error
        page_count = self._get_pdf_page_count(reader)
        page_number = self.signature_page
        if page_number > page_count:
            raise UserError(_('The signature page does not exist in the PDF.'))
        for index in range(page_count):
            page = self._get_pdf_page(reader, index)
            if index + 1 == page_number:
                self._validate_signature_box(page)
                overlay = self._build_signature_overlay(
                    page, signature_content)
                self._merge_pdf_page(page, overlay)
            self._add_pdf_page(writer, page)
        pdf_buffer = BytesIO()
        writer.write(pdf_buffer)
        return pdf_buffer.getvalue()

    def _build_signature_overlay(self, page, signature_content):
        page_width, page_height = self._get_pdf_page_size(page)
        signature_width = self._cm_to_points(self.signature_width)
        signature_height = self._cm_to_points(self.signature_height)
        signature_x, signature_y = self._get_signature_xy(
            page_width, page_height, signature_width, signature_height)
        overlay_buffer = BytesIO()
        signature_buffer = BytesIO(signature_content)
        pdf_canvas = canvas.Canvas(
            overlay_buffer, pagesize=(page_width, page_height))
        pdf_canvas.drawImage(
            ImageReader(signature_buffer), signature_x, signature_y,
            width=signature_width, height=signature_height, mask='auto')
        pdf_canvas.save()
        overlay_buffer.seek(0)
        return self._get_pdf_page(PdfFileReader(overlay_buffer), 0)

    def _validate_signature_box(self, page):
        page_width, page_height = self._get_pdf_page_size(page)
        signature_width = self._cm_to_points(self.signature_width)
        signature_height = self._cm_to_points(self.signature_height)
        signature_x, signature_y = self._get_signature_xy(
            page_width, page_height, signature_width, signature_height)
        if signature_x < 0 or signature_y < 0:
            raise UserError(_('The signature position cannot be negative.'))
        if signature_x + signature_width > page_width:
            raise UserError(_('The signature exceeds the PDF page width.'))
        if signature_y + signature_height > page_height:
            raise UserError(_('The signature exceeds the PDF page height.'))

    def _get_pdf_page_count(self, reader):
        if hasattr(reader, 'numPages'):
            return reader.numPages
        return len(reader.pages)

    def _get_pdf_page(self, reader, index):
        if hasattr(reader, 'getPage'):
            return reader.getPage(index)
        return reader.pages[index]

    def _add_pdf_page(self, writer, page):
        if hasattr(writer, 'addPage'):
            writer.addPage(page)
        else:
            writer.add_page(page)

    def _merge_pdf_page(self, page, overlay):
        if hasattr(page, 'mergePage'):
            page.mergePage(overlay)
        else:
            page.merge_page(overlay)

    def _get_pdf_page_size(self, page):
        box = getattr(page, 'mediaBox', None) or page.mediabox
        if hasattr(box, 'getWidth'):
            return float(box.getWidth()), float(box.getHeight())
        return float(box.width), float(box.height)

    def _cm_to_points(self, value):
        return value * self._CM_TO_POINTS

    def _points_to_cm(self, value):
        return value / self._CM_TO_POINTS

    def _get_reference_page_size_points(self):
        self.ensure_one()
        attachment = self.attachment_page_ids.filtered(
            lambda att: self._is_pdf_attachment(att) and att.datas)
        if len(attachment) != 1:
            return (
                self._DEFAULT_PAGE_WIDTH_POINTS,
                self._DEFAULT_PAGE_HEIGHT_POINTS,
            )
        try:
            pdf_content = base64.b64decode(attachment.datas)
            reader = PdfFileReader(BytesIO(pdf_content))
            page_count = self._get_pdf_page_count(reader)
            page_index = max(
                0, min((self.signature_page or 1) - 1, page_count - 1))
            page = self._get_pdf_page(reader, page_index)
            return self._get_pdf_page_size(page)
        except Exception:
            return (
                self._DEFAULT_PAGE_WIDTH_POINTS,
                self._DEFAULT_PAGE_HEIGHT_POINTS)

    def _get_signature_xy(
            self, page_width, page_height, signature_width, signature_height):
        self.ensure_one()
        if self.signature_position == 'custom':
            return (
                self._cm_to_points(self.signature_x),
                self._cm_to_points(self.signature_y),
            )
        horizontal_map = {
            'left': 0.0,
            'center': (page_width - signature_width) / 2.0,
            'right': page_width - signature_width,
        }
        vertical_map = {
            'top': page_height - signature_height,
            'middle': (page_height - signature_height) / 2.0,
            'bottom': 0.0,
        }
        vertical_key, horizontal_key = self.signature_position.split('_')
        return horizontal_map[horizontal_key], vertical_map[vertical_key]

    def action_notify_new_document(self):
        for page in self:
            if not page.parent_id:
                continue
            users = page.env['res.users'].search([
                '|',
                ('knowledge_categories', 'in', [page.parent_id.id]),
                ('knowledge_categories.child_ids', 'in', [page.parent_id.id]),
            ])
            template = page.env.ref(
                'portal_employee.notify_new_document', raise_if_not_found=False
            )
            if not template:
                _logger.info(
                    'Cannot notify new document: template '
                    '"portal_employee.notify_new_document" not exists.')
                continue
            notified_users = []
            for user in users:
                if not user.email:
                    _logger.info(
                        'Cannot notify new document: user %s has no'
                        ' email address.', user.name)
                    continue
                email_values = {
                    'email_to': user.email,
                    'email_cc': False,
                    'auto_delete': True,
                    'scheduled_date': False,
                }
                template.with_context(lang=user.lang).send_mail(
                    page.id,
                    force_send=True,
                    raise_exception=False,
                    email_values=email_values
                )
                notified_users.append(user.name)
            if notified_users:
                body_msg = _(
                    'New document notified to users: %s'
                ) % ', '.join(notified_users)
                page.message_post(
                    body=body_msg,
                    message_type='email',
                    subtype_xmlid='mail.mt_note'
                )
