###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'
    _order = 'sequence'

    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
