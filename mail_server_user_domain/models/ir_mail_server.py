###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class IrMailServer(models.Model):
    _inherit = 'ir.mail_server'

    def connect(self, host=None, port=None, user=None, password=None,
                encryption=None, smtp_debug=False, mail_server_id=None):
        mail_server_id = mail_server_id or self.env.context.get(
            'force_server_id', None)
        return super().connect(
            host=host, port=port, user=user, password=password,
            encryption=encryption, smtp_debug=smtp_debug,
            mail_server_id=mail_server_id)
