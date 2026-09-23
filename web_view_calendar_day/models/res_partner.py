###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sequence = fields.Integer(
        help='Sequence for location partner in calendar view',
    )
    show_in_calendar = fields.Boolean(
        string='Show in calendar',
        default=True,
    )
