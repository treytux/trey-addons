###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    show_qty_total = fields.Boolean(
        related='company_id.show_qty_total',
        string='Show quantity total',
        readonly=False,
        config_parameter='show_qty_total',
    )
