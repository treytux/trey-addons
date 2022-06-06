###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import fields, models

_log = logging.getLogger(__name__)


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
    join_purchases = fields.Boolean(
        string='Join purchases same supplier',
        default=True,
    )

    def purchases_get(self):
        assert self._context.get('active_ids'), 'Missing active_ids'
        purchases = self.env['purchase.order'].browse(
            self._context['active_ids'])
        return purchases

    def action_view_invoice(self):
        purchases = self.purchases_get()
        if len(purchases) == 1:
            return purchases.with_context(
                create_bill=False).action_view_invoice()
        self.action_invoice()
        action = self.env.ref('account.action_vendor_bill_template').read()[0]
        action['domain'] = '[("id", "in", %s)]' % str(
            purchases.mapped('invoice_ids.id'))
        action['view_type'] = 'tree'
        return action

    def create_refund_invoice(self, invoice):
        for line in invoice.invoice_line_ids:
            line.quantity *= -1
        refund = invoice._prepare_refund(invoice)
        invoice.invoice_line_ids = [(6, 0, [])]
        del refund['refund_invoice_id']
        del refund['origin']
        # For compatibilty with 'account_invoice_refund_link' addon.
        for _op, _code, vals in refund['invoice_line_ids']:
            if 'origin_line_ids' in vals:
                vals['origin_line_ids'] = False
        invoice.update(refund)
        invoice.compute_taxes()

    def action_invoice(self):
        def join_invoices(new_invoice, invoices):
            invoice = invoices.filtered(
                lambda inv: inv.partner_id == new_invoice.partner_id)
            if not invoice:
                return new_invoice
            invoice.origin = '%s,%s' % (invoice.origin, purchase.name)
            invoice.purchase_id = False
            for line in new_invoice.invoice_line_ids:
                data = line._convert_to_write(line._cache)
                data['invoice_id'] = invoice.id
                line.create(data)
            invoice.compute_taxes()
            return invoice

        invoices = self.env['account.invoice']
        purchases = self.purchases_get()
        for index, purchase in enumerate(purchases):
            _log.info('[%s/%s] Invoice purchase %s' % (
                index + 1, len(purchases), purchase.name))
            invoice = invoices.new({
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
            invoice.invoice_line_ids = (
                invoice.invoice_line_ids - lines_to_delete)
            if not invoice.invoice_line_ids:
                continue
            if self.join_purchases:
                invoice = join_invoices(invoice, invoices)
            if invoice.id not in invoices.ids:
                data = invoices._convert_to_write(invoice._cache)
                data['invoice_line_ids'].pop(0)
                invoice = invoices.create(data)
                invoice.compute_taxes()
                invoices |= invoice
        for invoice in invoices:
            if invoice.amount_total < 0:
                self.create_refund_invoice(invoice)
        if len(invoices) > 1:
            return True
        return purchase.with_context(create_bill=False).action_view_invoice()
