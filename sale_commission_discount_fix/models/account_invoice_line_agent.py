# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class AccountInvoiceLineAgent(models.Model):
    _inherit = 'account.invoice.line.agent'

    @api.depends('invoice_line.price_subtotal', 'invoice_line.discount')
    def _compute_amount(self):
        return super(AccountInvoiceLineAgent, self)._compute_amount()
