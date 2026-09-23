###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _tbai_build_invoice(self):
        third_party_invoices = self.sudo().filtered(
            lambda x: x.partner_id.tbai_third_party)
        self -= third_party_invoices
        super(AccountInvoice, self)._tbai_build_invoice()
