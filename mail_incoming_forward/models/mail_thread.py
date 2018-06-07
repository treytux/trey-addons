# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, _
import email


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def forward_email(self, message):
        inc_server = self.env['fetchmail.server'].browse(
            self.env.context['fetchmail_server_id'])
        out_server = self.env['ir.mail_server'].search([])
        if not out_server:
            raise Exception('No outgoing email server found.')
        inc_server = inc_server[0]
        if not inc_server.forward_email:
            raise Exception('No forward email defined.')
        out_server = out_server[0]
        msg = email.message_from_string(message)
        if msg.get('to'):
            msg.replace_header('to', inc_server.forward_email)
        elif msg.get('delivered-to'):
            msg.replace_header('delivered-to', inc_server.forward_email)
        subject = _('Forwarded from Odoo: %s') % msg.get('subject')
        msg.replace_header('Subject', subject)
        self.send_email_forwarded(inc_server, out_server, msg.as_string())
        raise Exception('Forwarded email %s' % subject)

    @api.model
    def send_email_forwarded(self, inc_server, out_server, message):
        smtp = out_server.connect(
            out_server.smtp_host, out_server.smtp_port, out_server.smtp_user,
            out_server.smtp_pass, out_server.smtp_encryption,
            out_server.smtp_debug)
        smtp.sendmail(
            out_server.smtp_user, inc_server.forward_email, message)
        smtp.quit()

    @api.model
    def message_process(self, model, message, custom_values=None,
                        save_original=False, strip_attachments=False,
                        thread_id=None):
        try:
            res = super(MailThread, self).message_process(
                model, message, custom_values, save_original,
                strip_attachments, thread_id)
            return res
        except Exception as e:
            self.forward_email(message)
            raise e
