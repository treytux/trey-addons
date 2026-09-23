###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models

DAILY_PRODUCTIVE_HOURS = 8


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    daily_productive_hours = fields.Float(
        'Daily productive hours',
        default=DAILY_PRODUCTIVE_HOURS,
        help='Estimate daily employee\'s productivity in hours.')
