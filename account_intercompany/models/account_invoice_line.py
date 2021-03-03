###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.multi
    def intercompany_check_company(self):
        self.ensure_one()
        self.intercompany_check_company_account()
        self.intercompany_check_company_tax()

    @api.multi
    def intercompany_check_company_tax(self):
        self.ensure_one()
        if not self.invoice_line_tax_ids:
            return
        tax_ids = []
        company = self.invoice_id.company_id
        for tax in self.invoice_line_tax_ids:
            if company == tax.company_id:
                tax_ids.append(tax.id)
                continue
            if not self.product_id:
                tax_ids.append(
                    self.invoice_id.intercompany_get_id(tax, company))
                continue
            if self.invoice_id.type in ('out_invoice', 'out_refund'):
                taxes = (
                    self.product_id.taxes_id.filtered(
                        lambda t: t.company_id == company)
                    or self.account_id.tax_ids
                    or self.invoice_id.company_id.account_sale_tax_id)
            else:
                taxes = (
                    self.product_id.supplier_taxes_id.filtered(
                        lambda t: t.company_id == company)
                    or self.account_id.tax_ids
                    or self.invoice_id.company_id.account_purchase_tax_id)
            tax_ids += self.invoice_id.fiscal_position_id.map_tax(
                taxes, self.product_id, self.invoice_id.partner_id).ids
        self = self.with_context(ignore_intercompany=True)
        self.invoice_line_tax_ids = [(6, 0, tax_ids)]

    @api.multi
    def intercompany_check_company_account(self):
        self.ensure_one()
        if not self.account_id:
            return
        if self.invoice_id.company_id == self.account_id.company_id:
            return
        company = self.invoice_id.company_id
        self = self.with_context(
            ignore_intercompany=True, force_company=company.id)
        if not self.product_id:
            self.account_id = self.invoice_id.intercompany_get_id(
                self.account_id, company)
            return
        account = self.get_invoice_line_account(
            self.invoice_id.type, self.product_id,
            self.invoice_id.fiscal_position_id, company)
        self.account_id = account.id

    @api.model
    def create(self, vals):
        line = super().create(vals)
        line.intercompany_check_company()
        return line

    @api.multi
    def write(self, vals):
        if self._context.get('ignore_intercompany'):
            return super().write(vals)
        res = super().write(vals)
        for line in self:
            line.intercompany_check_company()
        return res
