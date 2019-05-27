###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    user_inactive_days = fields.Integer(
        required=True,
        related='website_id.user_inactive_days')
