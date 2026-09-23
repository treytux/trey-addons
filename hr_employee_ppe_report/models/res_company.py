###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    employee_ppe_notes = fields.Text(
        string='PPE Notes',
        translate=True,
    )
