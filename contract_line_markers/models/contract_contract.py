###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ContractContract(models.Model):
    _inherit = 'contract.contract'

    def _prepare_invoice(self, date_invoice, journal=None):
        invoice_vals = super()._prepare_invoice(
            date_invoice=date_invoice, journal=journal)
        if not invoice_vals['invoice_date'] or not invoice_vals['ref']:
            return invoice_vals
        invoice_vals['ref'] = invoice_vals['ref'].replace(
            '#MONTH_INT#', invoice_vals['invoice_date'].strftime('%m'))
        invoice_vals['ref'] = invoice_vals['ref'].replace(
            '#MONTH_STR#',
            invoice_vals['invoice_date'].strftime('%B').capitalize())
        invoice_vals['ref'] = invoice_vals['ref'].replace(
            '#YEAR#', invoice_vals['invoice_date'].strftime('%Y'))
        return invoice_vals
