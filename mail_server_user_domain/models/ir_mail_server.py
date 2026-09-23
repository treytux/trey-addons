###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class IrMailServer(models.Model):
    _inherit = 'ir.mail_server'

    def connect(self, host=None, port=None, user=None, password=None,
                encryption=None, smtp_from=None, ssl_certificate=None,
                ssl_private_key=None, smtp_debug=False, mail_server_id=None,
                allow_archived=False):
        mail_server_id = mail_server_id or self.env.context.get(
            'force_server_id', None)
        return super().connect(
            host=host, port=port, user=user, password=password,
            encryption=encryption, smtp_from=smtp_from,
            ssl_certificate=ssl_certificate, ssl_private_key=ssl_private_key,
            smtp_debug=smtp_debug, mail_server_id=mail_server_id,
            allow_archived=allow_archived
        )
