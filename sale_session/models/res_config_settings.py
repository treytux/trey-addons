###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    show_confirm_current_session_button = fields.Boolean(
        related='company_id.show_confirm_current_session_button',
        readonly=False,
    )
