###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    invoices_related_ids = fields.One2many(
        comodel_name='account.invoice',
        string='Invoices related',
        compute='_compute_invoices_related_ids',
    )

    @api.multi
    def _compute_invoices_related_ids(self):
        account_invoice_obj = self.env['account.invoice']
        for invoice in self.filtered(
                lambda a: a.type in ['out_refund', 'in_refund']):
            invoices = account_invoice_obj.search([
                ('refund_invoice_ids', 'in', invoice.id),
            ])
            invoice.invoices_related_ids = [(6, 0, invoices.ids)]
