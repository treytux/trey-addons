###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    stock_field = fields.Selection(
        related='company_id.stock_field',
        readonly=False,
        help='Field used to determine product availability message',
    )
