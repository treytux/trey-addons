###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def remove_empty_followers(self, model):
        self.env['mail.followers'].search([
            ('res_model', '=', model),
            ('partner_id.email', '=', False),
        ]).unlink()
