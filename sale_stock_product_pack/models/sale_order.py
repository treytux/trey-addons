###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _split_invoice_line(self, invoice_line, qty):
        new_invoice_line = invoice_line.copy({
            'discount': 0,
        })
        invoice_line.quantity = invoice_line.quantity - qty
        new_invoice_line.write({
            'quantity': qty,
            'sale_line_ids': [(6, 0, invoice_line.sale_line_ids.ids)],
        })
        new_invoice_line._onchange_product_id()

    def _process_invoice_line(
            self, invoice_line, sale, sale_product_components,
            sale_line_components):
        qty_sale_line = sale_line_components.filtered(
            lambda ln: ln.product_id == invoice_line.product_id
            and ln in invoice_line.sale_line_ids).mapped('product_uom_qty')
        qty_sale_line = qty_sale_line[0]
        pickings_delivered = sale.picking_ids.filtered(
            lambda p: p.state == 'done')
        moves_delivered = pickings_delivered.mapped('move_lines')
        qty_delivered = (
            sum(moves_delivered.filtered(
                lambda m: m.product_id == invoice_line.product_id
                and m.sale_line_id in invoice_line.sale_line_ids).mapped(
                'product_uom_qty')))
        qty_to_split = qty_delivered - qty_sale_line
        to_split = (
            qty_to_split > 0
            and invoice_line.quantity > qty_to_split)
        if to_split:
            sale._split_invoice_line(invoice_line, qty_to_split)

    def _process_invoices(self, sale, invoice_ids):
        sale_line_components = sale.order_line.filtered(
            lambda p: p.pack_parent_line_id)
        sale_product_components = sale_line_components.mapped('product_id')
        for invoice in self.env['account.invoice'].browse(invoice_ids):
            if invoice not in sale.invoice_ids:
                continue
            for invoice_line in invoice.invoice_line_ids:
                if invoice_line.product_id.pack_ok:
                    continue
                if invoice_line.product_id not in sale_product_components:
                    continue
                self._process_invoice_line(
                    invoice_line, sale, sale_product_components,
                    sale_line_components)

    def action_invoice_create(self, grouped=False, final=False):
        invoice_ids = super().action_invoice_create(grouped, final)
        for sale in self:
            self._process_invoices(sale, invoice_ids)
        return invoice_ids

    # This function will only be called if the database has the
    # "sale_order_action_invoice_create_hook" module installed.
    def _modify_invoices(self, invoices):
        invoices_dict = super()._modify_invoices(invoices)
        invoice_ids = [inv.id for inv in invoices_dict.values()]
        for sale in self:
            self._process_invoices(sale, invoice_ids)
        return invoices_dict
