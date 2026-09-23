###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    holidays_type = fields.Many2many(
        related='company_id.holidays_type',
        readonly=False,
    )
    absences_type = fields.Many2many(
        related='company_id.absences_type',
        readonly=False,
    )
