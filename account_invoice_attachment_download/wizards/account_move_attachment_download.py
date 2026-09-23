###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import io
import zipfile

from odoo import _, exceptions, fields, models


class AccountMoveAttachmentDownload(models.TransientModel):
    _name = 'account.move.attachment_download'
    _description = 'Account Move Attachment Download'

    file_name = fields.Char(
        string='Filename',
        readonly=True,
    )
    file_data = fields.Binary(
        string='Zip file with attachments',
        readonly=True,
    )

    def button_attachment_download(self):
        active_ids = self.env.context.get('active_ids', [])
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'account.move'),
            ('res_id', 'in', active_ids),
        ])
        if not attachments:
            raise exceptions.ValidationError(
                _('No attachments were found for the selected invoices.'))
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as file:
            for attachment in attachments:
                file.writestr(
                    attachment.name, base64.b64decode(attachment.datas))
        zip_buffer.seek(0)
        self.write({
            'file_data': base64.b64encode(zip_buffer.read()).decode(),
            'file_name': _('invoices.zip'),
        })
        zip_buffer.close()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Download Attachments'),
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
