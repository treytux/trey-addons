###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amount_tax_signed = fields.Monetary(
        store=True,
    )
    amount_untaxed_invoice_signed = fields.Monetary(
        store=True,
    )

    @api.depends('amount_tax', 'amount_untaxed')
    def _compute_sign_taxes(self):
        super()._compute_sign_taxes()
