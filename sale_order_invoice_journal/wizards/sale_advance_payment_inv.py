###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        help="Select a journal for the accounting entry. Leave blank to use "
             "the default journal.")

    def create_invoices(self):
        self = self.with_context(journal_id=self.journal_id)
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        return res
