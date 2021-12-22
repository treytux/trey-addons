###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ContractContract(models.Model):
    _inherit = 'contract.contract'

    @api.multi
    def _prepare_invoice(self, date_invoice, journal=None):
        invoice_vals = super()._prepare_invoice(
            date_invoice=date_invoice,
            journal=journal
        )
        if not invoice_vals['date_invoice'] or not invoice_vals['name']:
            return invoice_vals
        invoice_vals['name'] = invoice_vals['name'].replace(
            '#MONTH_INT#',
            invoice_vals['date_invoice'].strftime('%m'),
        )
        invoice_vals['name'] = invoice_vals['name'].replace(
            '#MONTH_STR#',
            invoice_vals['date_invoice'].strftime('%B').capitalize(),
        )
        invoice_vals['name'] = invoice_vals['name'].replace(
            '#YEAR#',
            invoice_vals['date_invoice'].strftime('%Y'),
        )
        return invoice_vals
