# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api
import base64
import logging
_log = logging.getLogger(__name__)


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create_message_post(self, model, res_id, body, params=None):
        if params is None:
            params = {}
        if not model or not res_id or not body:
            return False
        obj = self.env[model].browse(res_id)
        if not obj.exists():
            return False
        subject = params['subject'] if 'subject' in params else False
        msg_type = params['msg_type'] if 'msg_type' in params else 'email'
        attachments = []
        if 'attachments' in params:
            for a in params['attachments']:
                attachments.append(
                    (a['datas_fname'], base64.decodestring(a['datas'])))
        try:
            obj.with_context(mail_post_autofollow=False).message_post(
                body=body, subject=subject, type=msg_type,
                attachments=attachments)
            return True
        except Exception:
            return False
