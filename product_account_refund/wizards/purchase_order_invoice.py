###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class PurchaseOrderInvoice(models.TransientModel):
    _inherit = 'purchase.order.invoice'

    def create_refund_invoice(self, invoice):
        res = super().create_refund_invoice(invoice=invoice)
        invoice_type = invoice.type
        if invoice_type not in ['out_refund', 'in_refund']:
            return res
        for line in invoice.invoice_line_ids:
            product_id = line.product_id
            categ_id = line.product_id.categ_id
            if invoice_type == 'out_refund':
                account = product_id.property_account_sales_refund_id or (
                    categ_id.property_account_sales_refund_id)
            elif invoice_type == 'in_refund':
                account = product_id.property_account_purchase_refund_id or (
                    categ_id.property_account_purchase_refund_id)
            if account:
                line.account_id = account.id
                line._onchange_account_id()
        return res
