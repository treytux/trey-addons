# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    @api.multi
    def recompute_voucher_lines(self, partner_id, journal_id, price,
                                currency_id, ttype, date):
        default = super(AccountVoucher, self).recompute_voucher_lines(
            partner_id=partner_id, journal_id=journal_id, price=price,
            currency_id=currency_id, ttype=ttype, date=date)
        for line in default['value']['line_cr_ids']:
            line['amount'] = 0.0
            line['reconcile'] = False
        for line in default['value']['line_dr_ids']:
            line['amount'] = 0.0
            line['reconcile'] = False
        return default
