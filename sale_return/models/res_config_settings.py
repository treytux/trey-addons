###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    return_days = fields.Integer(
        related='company_id.default_return_days',
        readonly=False,
        required=True,
    )
