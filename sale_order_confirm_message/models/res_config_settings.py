###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_confirm_message_active = fields.Boolean(
        related='company_id.sale_confirm_message_active',
        readonly=False,
    )
    sale_confirm_message_require_check = fields.Boolean(
        related='company_id.sale_confirm_message_require_check',
        readonly=False,
    )
    sale_confirm_message_body = fields.Text(
        related='company_id.sale_confirm_message_body',
        readonly=False,
    )
