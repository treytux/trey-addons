###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    period_min_qty = fields.Selection(
        related='company_id.period_min_qty',
        string='Period min qty',
        readonly=False,
        help='Period for calculation in orderpoints.',
    )
