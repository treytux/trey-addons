###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _is_sii_simplified_invoice(self):
        res = super()._is_sii_simplified_invoice()
        partner = self.partner_id.commercial_partner_id
        if partner.sii_simplified_invoice:
            return res
        journal_id = self.env.user.company_id.simplified_journal_id
        if partner.vat or not journal_id:
            return res
        else:
            return True
