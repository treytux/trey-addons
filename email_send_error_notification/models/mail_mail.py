###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api
from odoo.tools import html2plaintext


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model
    def send_error_notice(self):
        context = self.env.context.copy()
        context['sender_message'] = self
        context['original_body'] = html2plaintext(self.body_html)
        template = self.env.ref(
            'email_send_error_notification.mail_template_error_notice')
        template.with_context(context).send_mail(
            res_id=self.id, force_send=True)

    @api.multi
    def _postprocess_sent_message(self, mail_sent=True):
        if self.state == 'exception':
            self.send_error_notice()
        return super(MailMail, self)._postprocess_sent_message(mail_sent)
