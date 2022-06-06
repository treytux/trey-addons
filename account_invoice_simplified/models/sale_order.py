###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        if self.partner_id.vat:
            return res
        journal = self.env['account.journal'].browse(res.get('journal_id', []))
        if journal.journal_simplified_id:
            res['journal_id'] = journal.journal_simplified_id
        return res
