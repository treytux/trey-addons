###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def create(self, vals):
        invoice = super().create(vals)
        if self._context.get('journal_id'):
            invoice.journal_id = self._context.get('journal_id')
        return invoice
