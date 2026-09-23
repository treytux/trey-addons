from odoo import models


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _notify_thread_by_email(
        self, message, recipients_data, msg_vals=False, mail_auto_delete=True,
        model_description=False, force_email_company=False,
        force_email_lang=False, resend_existing=False, force_send=True,
        send_after_commit=True, subtitles=None, **kwargs
    ):
        if not model_description and self._name == 'sale.order':
            model_description = self.type_name or False
        return super()._notify_thread_by_email(
            message=message, recipients_data=recipients_data,
            msg_vals=msg_vals, mail_auto_delete=mail_auto_delete,
            model_description=model_description,
            force_email_company=force_email_company,
            force_email_lang=force_email_lang, resend_existing=resend_existing,
            force_send=force_send, send_after_commit=send_after_commit,
            subtitles=subtitles, **kwargs)
