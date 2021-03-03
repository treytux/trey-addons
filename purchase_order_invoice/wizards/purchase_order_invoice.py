###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class PurchaseOrderInvoice(models.TransientModel):
    _name = 'purchase.order.invoice'
    _description = 'Wizard for invoice purchase order'

    method = fields.Selection(
        selection=[
            ('received', 'Invoice received not invoiced'),
            ('all-not-invoiced', 'Invoice all lines not invoiced'),
            ('all', 'Invoice all lines'),
        ],
        string='Invoice method',
        default='received',
    )

    def purchase_get(self):
        assert self._context.get('active_ids'), 'Missing active_ids'
        purchases = self.env['purchase.order'].browse(
            self._context['active_ids'])
        assert len(purchases) == 1, 'Only can invoice one purchase order'
        return purchases[0]

    def action_view_invoice(self):
        purchase = self.purchase_get()
        return purchase.with_context(create_bill=False).action_view_invoice()

    def create_refund_invoice(self, invoice):
        for line in invoice.invoice_line_ids:
            line.quantity *= -1
        refund = invoice._prepare_refund(invoice)
        invoice.invoice_line_ids = [(6, 0, [])]
        del refund['refund_invoice_id']
        invoice.update(refund)

    def action_invoice(self):
        purchase = self.purchase_get()
        invoice_obj = self.env['account.invoice']
        invoice = invoice_obj.new({
            'origin': purchase.name,
            'purchase_id': purchase.id,
            'type': 'in_invoice',
            'currency_id': purchase.currency_id.id,
            'company_id': purchase.company_id.id
        })
        invoice.purchase_order_change()
        invoice._onchange_partner_id()
        if self.method == 'all':
            for line in invoice.invoice_line_ids:
                line.quantity = line.purchase_line_id.product_qty
        elif self.method == 'all-not-invoiced':
            for line in invoice.invoice_line_ids:
                line.quantity = (
                    line.purchase_line_id.product_qty
                    - line.purchase_line_id.qty_invoiced)
        lines_to_delete = invoice.invoice_line_ids.filtered(
            lambda ln: ln.quantity == 0)
        invoice.invoice_line_ids = invoice.invoice_line_ids - lines_to_delete
        if invoice.invoice_line_ids:
            if invoice.amount_total < 0:
                self.create_refund_invoice(invoice)
            data = invoice_obj._convert_to_write(invoice._cache)
            invoice = invoice_obj.create(data)
            invoice.compute_taxes()
        return purchase.with_context(create_bill=False).action_view_invoice()
