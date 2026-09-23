##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo import models


class IrMailServer(models.Model):
    _inherit = 'ir.mail_server'

    def _prepare_email_message(self, message, smtp_session):
        origin_from = message.get('From')
        smtp_from, smtp_to_list, message = super()._prepare_email_message(
            message, smtp_session)
        if origin_from:
            message.replace_header('From', origin_from)
        return smtp_from, smtp_to_list, message
