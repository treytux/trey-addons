###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ContractContract(models.Model):
    _inherit = 'contract.contract'

    @api.model
    def _finalize_and_create_invoices(self, invoices_values):
        invoices = super()._finalize_and_create_invoices(invoices_values)
        invoices.mapped('invoice_line_ids').onchange_multiple_discount()
        return invoices
