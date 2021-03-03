###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, fields, models
from odoo.exceptions import UserError


class PurchaseOrderInvoice(models.TransientModel):
    _inherit = 'purchase.order.invoice'

    method = fields.Selection(
        selection_add=[(
            'divide', 'Invoice received, divided by picking move date')]
    )

    def map_purchase_lines(self, purchase):
        purchase_lines = {}
        for line in purchase.order_line:
            if line.qty_invoiced >= line.qty_received:
                continue
            moves = self.env['stock.move'].search([
                ('id', 'in', line.move_ids.ids),
                ('state', '=', 'done'),
                ('picking_code', '=', 'incoming'),
            ], order='date desc')
            qty_to_invoice = line.qty_received - line.qty_invoiced
            for move in moves:
                if qty_to_invoice <= 0:
                    break
                move_month = move.picking_id.date_done.month
                if move_month not in purchase_lines:
                    purchase_lines.setdefault(move_month, {
                        line: move.quantity_done,
                    })
                else:
                    if line not in purchase_lines[move_month]:
                        purchase_lines[move_month].setdefault(line, 0)
                    purchase_lines[move_month][line] += move.quantity_done
                qty_to_invoice -= move.quantity_done
        return purchase_lines

    def _create_month_invoice(self, invoice_values):
        return self.env['account.invoice'].create(invoice_values)

    def _create_month_invoice_line(self, line_values):
        return self.env['account.invoice.line'].create(line_values)

    def action_invoice(self):
        if self.method != 'divide':
            return super().action_invoice()
        purchase = self.purchase_get()
        mapped_lines = self.map_purchase_lines(purchase)
        if not mapped_lines:
            raise UserError(_('There is no invoices to generate.'))
        for month in mapped_lines:
            invoice_values = {
                'origin': purchase.name,
                'purchase_id': purchase.id,
                'type': 'in_invoice',
                'currency_id': purchase.currency_id.id,
                'company_id': purchase.company_id.id,
                'partner_id': purchase.partner_id.id,
            }
            invoice = self._create_month_invoice(invoice_values)
            invoice._onchange_partner_id()
            for purchase_line in list(mapped_lines[month].keys()):
                line_values = invoice._prepare_invoice_line_from_po_line(
                    purchase_line)
                quantity = mapped_lines[month][purchase_line]
                line_values.update({
                    'quantity': quantity,
                    'invoice_id': invoice.id,
                })
                invoice_line = self._create_month_invoice_line(line_values)
                invoice_line._onchange_product_id()
            if invoice.amount_total < 0:
                self.create_refund_invoice(invoice)
            invoice.compute_taxes()
        return purchase.with_context(create_bill=False).action_view_invoice()
