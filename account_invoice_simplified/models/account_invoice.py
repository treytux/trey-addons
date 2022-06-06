###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _onchange_journal_id(self):
        res = super()._onchange_journal_id()
        if self.partner_id.vat:
            return res
        if self.journal_id.journal_simplified_id:
            self.journal_id = self.journal_id.journal_simplified_id

    def action_date_assign(self):
        res = super().action_date_assign()
        for inv in self:
            inv._onchange_journal_id()
        return res
