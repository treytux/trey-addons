###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    period_min_qty = fields.Selection(
        selection=[
            ('annual', 'Annual'),
            ('semester', 'Semester'),
            ('quarterly', 'Quarterly'),
            ('monthly', 'Monthly'),
        ],
        required=True,
        string='Period min quantity',
        default='annual',
        help='Period for calculation in orderpoints.',
    )
