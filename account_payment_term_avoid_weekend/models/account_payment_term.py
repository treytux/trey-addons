###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import datetime

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    avoid_payment_weekend = fields.Boolean(
        string='Avoid payment on weekend',
    )

    def check_date_weekend(self, date):
        return date.weekday() in [5, 6]

    def delay_payment_day(self, date):
        if date.weekday() == 5:
            return date + relativedelta(days=2)
        elif date.weekday() == 6:
            return date + relativedelta(days=1)

    @api.one
    def compute(self, value, date_ref=False):
        res = super().compute(value=value, date_ref=date_ref)[0]
        if not self.avoid_payment_weekend:
            return res
        module = self.env['ir.module.module'].sudo().search([
            ('name', '=', 'account_payment_term_extension'),
            ('state', '=', 'installed'),
        ])
        result = []
        for line in res:
            date = datetime.datetime.strptime(line[0], '%Y-%m-%d').date()
            if not self.check_date_weekend(date):
                result.append((date, line[1]))
                continue
            date = self.delay_payment_day(date)
            if not module:
                result.append((date.strftime('%Y-%m-%d'), line[1]))
                continue
            holiday = self.holiday_ids.filtered(lambda ln: ln.holiday == date)
            if holiday:
                result.append(
                    (holiday.date_postponed.strftime('%Y-%m-%d'), line[1]))
                continue
            result.append((date.strftime('%Y-%m-%d'), line[1]))
        return result
