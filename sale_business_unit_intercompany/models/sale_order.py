###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _split_invoice_by_product_unit_company(self, invoices):
        def _prepare_invoice_by_companies(companies):
            res = self.env['account.invoice']
            for company in companies:
                inv_data = self[0]._prepare_invoice()
                inv_data['company_id'] = company.id
                res |= res.create(inv_data)
            return res

        def _get_lines_by_company(lines, company_id):
            res = self.env['account.invoice.line']
            aux = [
                (li, li.mapped('product_id.unit_id.company_id'))
                for li in lines]
            for i, (line, company) in enumerate(aux):
                if not company:
                    company = [c for ignore, c in aux[i + 1:] if c]
                if company and company[0] == company_id:
                    res |= line
            return res

        companies = self.env['res.company']
        inv_lines = self.env['account.invoice.line']
        for invoice in invoices:
            companies |= invoice.mapped(
                'invoice_line_ids.product_id.unit_id.company_id').filtered(
                    lambda c: c != invoice.company_id)
            inv_lines |= invoice.mapped('invoice_line_ids')
        invoices |= _prepare_invoice_by_companies(companies)
        for invoice in invoices:
            lines = _get_lines_by_company(inv_lines, invoice.company_id)
            if not lines:
                continue
            lines.write(dict(invoice_id=invoice.id))
        res = invoices.filtered(lambda i: len(i.invoice_line_ids) != 0)
        to_unlink = invoices.filtered(lambda i: len(i.invoice_line_ids) == 0)
        to_unlink.unlink()
        return res

    def _finalize_invoices(self, invoices, references):
        new_invoices = {}
        references = {}
        for key, invs in invoices.items():
            for inv in self._split_invoice_by_product_unit_company(invs):
                new_invoices[(key, inv.company_id.id)] = inv
                references[inv] = inv.mapped(
                    'invoice_line_ids.sale_line_ids.order_id')
        super()._finalize_invoices(new_invoices, references)
