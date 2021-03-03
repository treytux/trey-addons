###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    default_return_days = fields.Integer(
        default=730,
        string='Default max return days',
    )
