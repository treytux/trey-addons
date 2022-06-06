###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class AccountInvoiceLineAgent(models.Model):
    _inherit = "account.invoice.line.agent"

    def _compute_amount(self):
        res = super()._compute_amount()
        for line in self:
            if line.invoice.type.startswith('in_'):
                line.amount = -line.amount
        return res
