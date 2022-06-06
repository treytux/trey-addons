###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _finalize_invoices(self, invoices, references):
        res = super()._finalize_invoices(invoices, references)
        for invoice in references:
            if invoice.type != 'out_refund':
                continue
            sales = references[invoice]
            sales_lines = sales.mapped('order_line')
            sales_invoices = sales.mapped('invoice_ids').filtered(
                lambda i: i.type == 'out_invoice')
            if not sales_invoices:
                continue
            related_invoices = self.env['account.invoice.line'].search([
                ('invoice_id', 'in', sales_invoices.ids),
                ('sale_line_ids', 'in', sales_lines.ids),
            ]).mapped('invoice_id')
            invoice.write({
                'tbai_refund_key': 'R1',
                'tbai_refund_type': 'I',
                'refund_invoice_id': (related_invoices
                                      and related_invoices[0]
                                      and related_invoices[0].id or None),
            })
        return res
