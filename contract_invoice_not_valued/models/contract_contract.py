###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ContractContract(models.Model):
    _inherit = 'contract.contract'

    show_valued_lines = fields.Boolean(
        string='Show Valued Lines',
        default=True,
        help='Indicates whether the invoice generated from this contract will '
        'display valued lines.',
    )

    def _prepare_recurring_invoices_values(self, date_ref=False):
        invoices_values = super()._prepare_recurring_invoices_values(date_ref)
        for invoice_vals in invoices_values:
            invoice_vals['show_valued_lines'] = self.show_valued_lines
        return invoices_values
