# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_validate(self):
        pre_followers = self.message_follower_ids
        res = super(AccountInvoice, self).invoice_validate()
        for follower in self.message_follower_ids:
            if follower not in pre_followers:
                self.message_unsubscribe([follower.id])
        return res
