# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_number(self):
        res = super(AccountInvoice, self).action_number()
        for invoice in self:
            invoice.write({'name': invoice.number})
        return res
