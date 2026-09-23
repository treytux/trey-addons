###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    calendar_color = fields.Char(
        string='Calendar color',
    )

    @api.constrains('calendar_color')
    def _check_calendar_color(self):
        pattern = re.compile(r'^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$')
        for account in self:
            if account.calendar_color and not pattern.match(
                    account.calendar_color):
                raise ValidationError(
                    _('Calendar color must be a valid hex color code.'))
