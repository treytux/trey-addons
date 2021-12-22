###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_invoice_create(self, grouped=False, final=False):
        invoice_ids = super().action_invoice_create(
            grouped=grouped, final=final)
        invoices = self.env['account.invoice'].browse(invoice_ids)
        for invoice in invoices:
            for line in invoice.invoice_line_ids:
                if line.quantity == 0:
                    line.unlink()
            pickings = invoice.mapped(
                'invoice_line_ids.move_line_ids.picking_id')
            invoice.picking_ids = [(6, 0, pickings.ids)]
            if sum(invoice.mapped('invoice_line_ids.quantity')) == 0:
                invoice.unlink()
        return invoice_ids
