###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, exceptions, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def action_invoice_open(self):
        amount_limit = self.journal_id.limit_amount_total
        if self.journal_id.type not in ['sale', 'purchase']:
            return super().action_invoice_open()
        if amount_limit and amount_limit < self.amount_total:
            raise exceptions.UserError(_(
                'This invoice exceeds the limits set in the journal, use '
                'another journal in order to validate this invoice'))
        return super().action_invoice_open()
