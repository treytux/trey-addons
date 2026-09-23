###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCountry(models.Model):
    _inherit = 'res.country'

    insurance_policy = fields.Text(
        string='Insurance Policy',
        help='Insurance policy for exports',
        translate=True,
    )
