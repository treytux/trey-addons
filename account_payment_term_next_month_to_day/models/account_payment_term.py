# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields
from dateutil.relativedelta import relativedelta
import calendar


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    def compute(self, cr, uid, id, value, date_ref=False, context=None):
        result = super(AccountPaymentTerm, self).compute(
            cr, uid, id, value=value, date_ref=date_ref, context=context)
        payment_term = self.browse(cr, uid, id, context=context)
        if not result:
            return result
        for i, line in enumerate(payment_term.line_ids):
            if not line.payment_day:
                continue
            date = fields.Date.from_string(result[i][0])
            next_month = (date + relativedelta(months=+line.payment_month))
            days_in_month = calendar.monthrange(date.year, next_month.month)[1]
            paymentDay = (line.payment_day <= days_in_month and
                          line.payment_day or days_in_month)
            daysToPaymentDay = paymentDay - int(date.day)
            new_date = (date +
                        relativedelta(months=+line.payment_month) +
                        relativedelta(days=+daysToPaymentDay))
            result[i] = (fields.Date.to_string(new_date), result[i][1])
        return result


class AccountPaymentTermLine(models.Model):
    _inherit = 'account.payment.term.line'

    payment_month = fields.Integer(
        string='Payment month(s)',
        help='Input the day of the month for the payment to be made.')
    payment_day = fields.Integer(
        string='Payment day',
        help='Input how many months for the payment to be made.')
