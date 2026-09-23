###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import json

from odoo import http
from odoo.http import request

try:
    from odoo.addons.portal.controllers.mail import PortalChatter
except ImportError:
    PortalChatter = object

attachments_ids = []
attachment_files = []


class ChatterAttachment(PortalChatter):
    @http.route()
    def portal_chatter_post(self, res_model, res_id, message, **kw):
        res = super(ChatterAttachment, self).portal_chatter_post(
            res_model, res_id, message, **kw)
        mail = request.env['mail.message'].sudo().search([
            ['model', 'like', res_model],
            ['message_type', '=', 'comment'],
            ['res_id', '=', res_id]
        ], order='id desc', limit=1)
        partner = request.env['res.partner'].search([
            ('name', '=', request.env.user.name)])
        if not message:
            message = request.env['mail.message'].sudo()
            if attachments_ids:
                message.create({
                    'model': res_model,
                    'email_from': request.env.user.email,
                    'author_id': partner.id,
                    'message_type': 'comment',
                    'res_id': int(res_id),
                    'attachment_ids': [(6, 0, attachments_ids)],
                })
        else:
            mail.sudo().write({
                'attachment_ids': [(6, 0, attachments_ids)],
            })
        attachments_ids.clear()
        return res

    @http.route(
        '/portal/attachment/add', type='http', auth='public', methods=['POST'],
        website=True)
    def attachment_add(
            self, name, file, res_model, res_id, access_token=None, **kwargs):
        attachment = request.env['ir.attachment'].sudo()
        access_token = False
        if not request.env.user.has_group('base.group_user'):
            attachment = attachment.with_context(
                binary_field_real_user=attachment.env.user)
            access_token = attachment.generate_access_token()
        file_read = base64.b64encode(file.read())
        attachment = attachment.create({
            'name': name,
            'datas': file_read,
            'datas_fname': file.filename,
            'res_model': res_model,
            'res_id': int(res_id),
            'access_token': access_token,
        })
        attachment_files.append(file)
        attachments_ids.append(attachment.id)
        return request.make_response(
            data=json.dumps(attachment.read([
                'id', 'name', 'mimetype', 'file_size', 'access_token'])[0]),
            headers=[('Content-Type', 'application/json')]
        )
