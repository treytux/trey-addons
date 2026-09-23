###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _notify_by_email_prepare_rendering_context(
            self, message, msg_vals=False, model_description=False,
            force_email_company=False, force_email_lang=False):
        if (self.exists() and self._name == 'hr.leave'
                and not force_email_company):
            force_email_company = self.employee_company_id
        return super()._notify_by_email_prepare_rendering_context(
            message=message, msg_vals=msg_vals,
            model_description=model_description,
            force_email_company=force_email_company,
            force_email_lang=force_email_lang)
