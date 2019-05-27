###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api
from odoo.tools.float_utils import float_compare


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def action_create_invoice(self):
        self.ensure_one()
        self.create_invoices()
        return self.action_view_invoice()

    @api.multi
    def create_invoice(self):
        def get_invoice():
            if self.env.context.get('merge_draft_invoice', False):
                invoices = self.env['account.invoice'].search([
                    ('partner_id', '=', self.partner_id.id),
                    ('state', '=', 'draft'),
                    ('type', 'in', ['in_invoice', 'in_refund'])])
                if len(invoices) == 1:
                    invoice = invoices[0]
                    invoice.purchase_id = self.id
                    return invoice
            return self.env['account.invoice'].create({
                'partner_id': self.partner_id.id,
                'purchase_id': self.id,
                'type': 'in_invoice'})

        def update_invoice_type(invoice):
            total = sum([
                l.purchase_line_id.price_total
                for l in invoice.invoice_line_ids])
            invoice.type = total < 0 and 'in_refund' or 'in_invoice'
            functions = {
                (False, 'in_invoice'): max, (False, 'in_refund'): min,
                (True, 'in_invoice'): min, (True, 'in_refund'): max}
            for line in invoice.invoice_line_ids:
                is_return = line.purchase_line_id.product_qty < 0
                line.quantity = functions[(is_return, invoice.type)](
                    line.quantity * -1, line.quantity)

        self.ensure_one()
        invoice = get_invoice()
        invoice._onchange_partner_id()
        invoice.purchase_order_change()
        update_invoice_type(invoice)
        invoice.compute_taxes()
        return invoice

    @api.multi
    def create_invoices(self):
        invoices = self.env['account.invoice']
        for purchase in self:
            invoices |= purchase.create_invoice()
        return invoices

    @api.depends(
        'state', 'order_line.qty_invoiced', 'order_line.qty_received',
        'order_line.product_qty')
    def _get_invoiced(self):
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')

        def get_status(line):
            qty = (
                line.product_id.purchase_method == 'purchase' and
                line.product_qty or line.qty_received)
            if qty == 0:
                return 'no'
            qty_invoiced = line.qty_invoiced
            if qty < 0:
                qty *= -1
                qty_invoiced *= -1
            comp = float_compare(qty, qty_invoiced, precision_digits=precision)
            results = dict({-1: 'no', 0: 'invoiced', 1: 'to invoice'})
            return results[comp]

        super()._get_invoiced()
        for order in self:
            if order.invoice_status != 'no':
                continue
            status = list(set([get_status(l) for l in order.order_line]))
            order.invoice_status = len(status) == 1 and status[0] or 'no'
