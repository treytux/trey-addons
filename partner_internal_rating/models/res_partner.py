###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    evaluation = fields.Selection(
        selection=[
            ('not_set', 'Not set'),
            ('very_low', 'Very low'),
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('very_high', 'Very high'),
        ],
        string='Partner evaluation',
    )
