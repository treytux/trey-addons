###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    pending_estimated_time = fields.Float(
        string='Pending estimated time',
    )

    def action_open_origin_record(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.res_model,
            'res_id': self.res_id,
            'view_mode': 'form',
            'target': 'current',
        }
