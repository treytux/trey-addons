###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    tax_fee_amount = fields.Float(
        string='Tax fee amount',
        compute='_compute_tax_fee_amount',
    )

    def _compute_tax_fee_amount(self):
        for invoice in self:
            invoice.tax_fee_amount = sum(
                invoice.mapped('invoice_line_ids.tax_fee_ids').filtered(
                    lambda tax_ln: tax_ln.tax_fee_id.show_on_invoice
                    in ['value', 'always'] and tax_ln.tax_fee_amount).mapped(
                    'tax_fee_amount'))
