###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ContractContract(models.Model):
    _inherit = 'contract.contract'

    @api.model
    def _finalize_invoice_creation(self, invoices):
        def get_account(invoice, account):
            acc = account.search([
                ('code', '=', account.code),
                ('company_id', '=', invoice.company_id.id)])
            return acc.id if acc else False

        for invoice in invoices:
            if invoice.company_id != invoice.account_id.company_id:
                invoice.account_id = get_account(invoice, invoice.account_id)
            for line in invoice.invoice_line_ids:
                if invoice.company_id != line.account_id.company_id:
                    line.account_id = get_account(invoice, line.account_id)
        return super()._finalize_invoice_creation(invoices)
