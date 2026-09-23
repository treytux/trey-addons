###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    def create(self, vals):
        res = super().create(vals)
        for line in res:
            invoice_type = line.invoice_id.type
            if invoice_type not in ['out_refund', 'in_refund']:
                continue
            categ_id = line.product_id.categ_id
            product_id = line.product_id
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

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super()._onchange_product_id()
        if not self.product_id:
            return res
        invoice_type = self.invoice_id.type
        if invoice_type not in ['out_refund', 'in_refund']:
            return res
        if invoice_type == 'out_refund':
            account = self.product_id.property_account_sales_refund_id or (
                self.product_id.categ_id.property_account_sales_refund_id)
        elif invoice_type == 'in_refund':
            account = self.product_id.property_account_purchase_refund_id or (
                self.product_id.categ_id.property_account_purchase_refund_id)
        if account:
            self.account_id = account.id
            self._onchange_account_id()
        return res
