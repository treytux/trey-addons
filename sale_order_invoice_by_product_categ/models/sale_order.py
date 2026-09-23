###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _create_invoices_with_hook(self, invoice_ids):
        def recompute_origin(invoice):
            sale_names = list({
                s.order_id.name
                for i in invoice.invoice_line_ids
                for s in i.sale_line_ids})
            invoice.origin = ', '.join(sale_names)

        if not invoice_ids:
            return invoice_ids
        invoices = self.env['account.invoice'].browse(invoice_ids)
        invoice_lines = invoices.mapped('invoice_line_ids')
        categories_lines = invoice_lines.mapped('product_id.categ_id')
        if len(categories_lines) == 1:
            return invoice_ids
        categories_partner = invoices.mapped(
            'partner_id.invoice_by_product_categ_ids')
        if len(categories_partner) == 0:
            return invoice_ids
        dict_categ_lines = {}
        product_categ_obj = self.env['product.category']
        for categ in categories_partner:
            all_childs = product_categ_obj.search([
                ('id', 'child_of', [categ.id]),
            ])
            categ_childs = categories_partner.filtered(
                lambda c: c.id not in [categ.id] and c.id in all_childs.ids)
            dict_categ_lines[categ.id] = invoice_lines.filtered(
                lambda ln: ln.product_id.categ_id.id in all_childs.ids and (
                    ln.product_id.categ_id.id not in categ_childs.ids))
        if len(categories_partner) == 1 \
                and dict_categ_lines[categories_partner[0].id] == invoice_lines:
            return invoice_ids
        for categ in dict_categ_lines:
            if dict_categ_lines[categ] == invoices.mapped('invoice_line_ids'):
                break
            new_invoice = invoices[0].copy({
                'invoice_line_ids': [(6, 0, dict_categ_lines[categ].ids)],
            })
            recompute_origin(new_invoice)
            new_invoice.compute_taxes()
            invoice_ids.append(new_invoice.id)
        for invoice in invoices:
            if invoice.invoice_line_ids:
                recompute_origin(invoice)
                invoice.compute_taxes()
                continue
            invoice_ids.remove(invoice.id)
            invoice.unlink()

    def action_invoice_create(self, grouped=False, final=False):
        invoice_ids = super().action_invoice_create(grouped, final)
        for invoice_id in invoice_ids:
            self._create_invoices_with_hook([invoice_id])
        return invoice_ids

    def _modify_invoices(self, invoices):
        invoices_dict = super()._modify_invoices(invoices)
        invoice_ids = [inv.id for inv in invoices_dict.values()]
        for invoice_id in invoice_ids:
            self._create_invoices_with_hook([invoice_id])
        return invoices_dict
