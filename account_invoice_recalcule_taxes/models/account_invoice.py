# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def create(self, vals):
        invoice = super(AccountInvoice, self).create(vals)
        if (invoice.env.context.get('no_recompute_taxes') or
                not invoice.journal_id.recalcule_taxes):
            return invoice
        invoice.with_context(no_recompute_taxes=True).button_reset_taxes()
        return invoice

    @api.multi
    def write(self, vals):
        res = super(AccountInvoice, self).write(vals)
        if (self.env.context.get('no_recompute_taxes') or
                not self.journal_id.recalcule_taxes):
            return res
        self.with_context(no_recompute_taxes=True).button_reset_taxes()
        return res
