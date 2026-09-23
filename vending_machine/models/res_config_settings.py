###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    user_for_notification = fields.Many2one(
        comodel_name='res.users',
        string='User',
        help='User for send notifications when there is a new quote from the'
        ' vending machine',
        config_parameter='vending_machine.user_id',
    )
    email_of_user = fields.Char(
        related='user_for_notification.login',
        config_parameter='vending_machine.user_email',
    )

    @api.model
    def get_email_to_notify_replenishment(self):
        param = self.env['ir.config_parameter'].sudo().get_param(
            'vending_machine.user_email')
        return param or ''
