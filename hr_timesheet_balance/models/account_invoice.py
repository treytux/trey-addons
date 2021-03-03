###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def action_move_create(self):
        self = self.with_context(reset_balance=True)
        return super(AccountInvoice, self).action_move_create()
