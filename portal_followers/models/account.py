# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api
import logging
_log = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def create(self, vals):
        env = self.env
        account_invoice = super(AccountInvoice, self).create(vals)
        if 'partner_id' in vals:
            root_partner_id = account_invoice.partner_id.root_partner_id
            invoice = env['account.invoice'].browse(account_invoice.id)
            invoice.write(
                {'message_follower_ids': [(6, 0, list(set(
                    account_invoice.message_follower_ids.ids +
                    root_partner_id.message_follower_ids.ids)))]})
        return account_invoice

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        if self.partner_id.is_company and self.partner_id.child_ids and \
           self.partner_id.message_follower_ids:
            self.message_unsubscribe([self.partner_id.id])
        return res
