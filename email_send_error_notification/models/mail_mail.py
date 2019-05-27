# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api
from openerp.tools import html2plaintext


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model
    def send_error_notice(self, mail=None):
        context = self.env.context.copy()
        context['sender_message'] = mail
        context['original_body'] = html2plaintext(mail.body_html)
        template = self.env.ref(
            'email_send_error_notification.email_template_error_notice')
        template.with_context(context).send_mail(
            res_id=mail.id, force_send=True)

    @api.model
    def _postprocess_sent_message(self, mail, mail_sent=True):
        if mail.state == 'exception':
            self.send_error_notice(mail)
        return super(MailMail, self)._postprocess_sent_message(mail, mail_sent)
