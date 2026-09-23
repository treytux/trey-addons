###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.team_id and self.team_id.invoice_journal_id:
            invoice_vals['journal_id'] = self.team_id.invoice_journal_id.id
        return invoice_vals
