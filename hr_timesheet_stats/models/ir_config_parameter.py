###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class IrConfigParameter(models.Model):
    _inherit = 'ir.config_parameter'

    hr_timesheet_stats_holidays = fields.Char(
        string='Timesheet stats holidays',
        help='Contains a string with vacation days separated by commas, '
        'for example "2,0,1,2,1,1,0,1,0,1,1,2"',
    )
