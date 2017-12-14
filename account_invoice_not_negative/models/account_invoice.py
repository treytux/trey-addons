# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, exceptions, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_validate(self):
        allow_negative = self.journal_id.allow_invoice_negative
        if self.amount_total < 0 and not allow_negative:
            raise exceptions.Warning(
                _('You can not validate the invoice, the total is negative'))
        super(AccountInvoice, self).invoice_validate()
