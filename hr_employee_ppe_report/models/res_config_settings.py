###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    employee_ppe_notes = fields.Text(
        string='PPE Notes',
        related='company_id.employee_ppe_notes',
        readonly=False,
        translate=True,
    )
