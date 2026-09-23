###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import calendar
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartnerInvoiceDay(models.Model):
    _name = 'res.partner.invoice_day'
    _description = 'Partner invoice day'
    _order = 'name'

    name = fields.Char(
        string='Name',
        translate=True,
        required=True,
    )
    days = fields.Char(
        string='Days',
        help='Comma-separated list of days of the month (1-31) on which '
             'this invoicing day is triggered. Use 31 to represent the '
             'last day of the month, since months have a different '
             'number of days.',
    )

    @api.constrains('days')
    def _check_days(self):
        for record in self:
            for value in record._get_days_list():
                if not 1 <= value <= 31:
                    raise ValidationError(_(
                        'Days must be numbers between 1 and 31.'))

    def _get_days_list(self):
        self.ensure_one()
        if not self.days:
            return []
        values = []
        for value in self.days.split(','):
            value = value.strip()
            if not value:
                continue
            if not value.isdigit():
                raise ValidationError(_(
                    'Days must be a comma-separated list of numbers '
                    'between 1 and 31, got: %s') % value)
            values.append(int(value))
        return values

    def _is_invoicing_day(self, today):
        self.ensure_one()
        day_prev = today - timedelta(days=1)
        last_day_of_month = calendar.monthrange(
            day_prev.year, day_prev.month)[1]
        for nominal_day in self._get_days_list():
            if nominal_day >= last_day_of_month:
                if day_prev.day == last_day_of_month:
                    return True
            elif day_prev.day == nominal_day:
                return True
        return False
