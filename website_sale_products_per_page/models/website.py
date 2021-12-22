###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    ppg_values = fields.Char(
        string='Products per page',
        default='20,40,60,100',
        help='Values must be separated by commas, for example: 20,40,60',
    )
