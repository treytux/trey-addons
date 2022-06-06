###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import email
import re

from odoo import api, models


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def message_process(self, model, message, custom_values=None,
                        save_original=False, strip_attachments=False,
                        thread_id=None):
        if thread_id:
            return super().message_process(
                model, message, custom_values=custom_values,
                save_original=save_original,
                strip_attachments=strip_attachments, thread_id=thread_id)
        extract = getattr(
            email, 'message_from_bytes', email.message_from_string)
        msg_txt = extract(message)
        msg = self.message_parse(msg_txt, save_original=save_original)
        partners_to = msg.get('to')
        mails = partners_to and re.findall(
            r'[\w.+-]+@[\w-]+\.[\w.-]+', partners_to) or []
        mail_server = self.env['ir.mail_server'].search([])
        for mail in mails:
            pos = mail.find('@')
            if pos == -1:
                continue
            alias = self.env['mail.alias'].search([
                ('alias_name', '=', mail[:pos]),
                ('alias_model_id.model', '=', model),
            ], limit=1)
            if alias and alias.external_email:
                mail = self.env['mail.mail'].create({
                    'subject': msg.get('subject'),
                    'email_from': mail_server.smtp_user,
                    'email_to': alias.external_email,
                    'body_html': msg.get('body'),
                })
                mail.send()
        return super().message_process(
            model, message, custom_values=custom_values,
            save_original=save_original, strip_attachments=strip_attachments,
            thread_id=thread_id)
