###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.multi
    def create_invoices(self):
        sales = self.env['sale.order'].browse(self.env.context['active_ids'])
        invoices = sales.mapped('invoice_ids')
        res = super().create_invoices()
        invoices = sales.mapped('invoice_ids') - invoices
        for invoice in invoices:
            invoice_type = invoice.type
            if invoice_type not in ['out_refund', 'in_refund']:
                continue
            for line in invoice.invoice_line_ids:
                product_id = line.product_id
                categ_id = line.product_id.categ_id
                if invoice_type == 'out_refund':
                    account = product_id.property_account_sales_refund_id or (
                        categ_id.property_account_sales_refund_id)
                elif invoice_type == 'in_refund':
                    account = (
                        product_id.property_account_purchase_refund_id
                        or categ_id.property_account_purchase_refund_id)
                if account:
                    line.account_id = account.id
                    line._onchange_account_id()
        return res
