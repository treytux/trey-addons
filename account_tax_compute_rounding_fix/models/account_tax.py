# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models


class AccountTax(models.Model):
    _inherit = "account.tax"

    def _compute(self, cr, uid, taxes, price_unit, quantity, product=None,
                 partner=None, precision=None):
        _precision = self.pool.get('decimal.precision').precision_get(
            cr, uid, 'Account')
        _method = (taxes and
                   taxes[0].company_id.tax_calculation_rounding_method or '')
        if not precision:
            precision = _precision
        elif _method == 'round_globally' and precision == _precision + 5:
            precision += self.pool.get('decimal.precision').precision_get(
                cr, uid, 'Product Price') + 1
        res = self._unit_compute(
            cr, uid, taxes, price_unit, product, partner, quantity)
        total = 0.0
        for r in res:
            if r.get('balance', False):
                r['amount'] = round(
                    r.get('balance', 0.0) * quantity, precision) - total
            else:
                r['amount'] = round(r.get('amount', 0.0) * quantity, precision)
                total += r['amount']
        return res
