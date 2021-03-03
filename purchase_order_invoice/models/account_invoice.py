###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_invoice_line_from_po_line(self, line):
        vals = super()._prepare_invoice_line_from_po_line(line)
        if vals['quantity'] != 0:
            return vals
        if line.product_id.purchase_method == 'purchase':
            vals['quantity'] = line.product_qty - line.qty_invoiced
        else:
            vals['quantity'] = line.qty_received - line.qty_invoiced
        return vals
