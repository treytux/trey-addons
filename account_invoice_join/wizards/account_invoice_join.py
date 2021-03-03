###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, exceptions, models


class AccountInvoiceJoin(models.TransientModel):
    _name = 'account.invoice.join'
    _description = 'Wizard for join account invoice'

    def check_invoices(self, invoices):
        if len(invoices) <= 1 :
            raise exceptions.UserError(
                _('Select more than one invoice in draft state'))
        draft_invoices = invoices.filtered(lambda i: i.state == 'draft')
        if len(draft_invoices) != len(invoices):
            raise exceptions.UserError(
                _('Not all invoices are in draft state'))
        partner_invoices = invoices.filtered(
            lambda i: i.partner_id == invoices[0].partner_id)
        if len(partner_invoices) != len(invoices):
            raise exceptions.UserError(
                _('All invoices need to be same partner'))
        type_invoices = invoices.filtered(
            lambda i: i.type == invoices[0].type)
        if len(type_invoices) != len(invoices):
            raise exceptions.UserError(
                _('Only can join invoice with same type'))
        return True

    def post_sales(self, invoice, lines):
        if not lines:
            return
        if not hasattr(lines[0], 'sale_line_ids'):
            return
        for sale in lines.mapped('sale_line_ids.order_id'):
            invoice.message_post_with_view(
                'mail.message_origin_link',
                values={'self': invoice, 'origin': sale},
                subtype_id=self.env.ref('mail.mt_note').id)

    def post_purchases(self, invoice, lines):
        if not lines:
            return
        if not hasattr(lines[0], 'purchase_line_id'):
            return
        purchases = lines.mapped('purchase_line_id.order_id')
        html = '<a href=# data-oe-model=purchase.order data-oe-id=%s>%s</a>'
        html_lines = ', '.join(
            [html % (order.id, order.name) for order in purchases])
        body = _('This vendor bill has been created from: %s') % html_lines
        invoice.message_post(body=body)

    def join_invoice(self, master, invoice):
        if invoice.origin:
            if not master.origin:
                master.origin = invoice.origin
            else:
                master.origin += ', %s' % invoice.origin
        if hasattr(invoice, 'picking_ids') and invoice.picking_ids:
            master.picking_ids = [(4, p.id) for p in invoice.picking_ids]

    def action_join(self):
        assert self._context.get('active_ids'), 'Missing active_ids'
        invoices = self.env['account.invoice'].browse(
            self._context['active_ids'])
        self.check_invoices(invoices)
        master = invoices[0]
        for invoice in invoices[1:]:
            self.post_sales(master, invoice.invoice_line_ids)
            self.post_purchases(master, invoice.invoice_line_ids)
            invoice.invoice_line_ids.write({'invoice_id': master.id})
            self.join_invoice(master, invoice)
            invoice.unlink()
        master.compute_taxes()
        return self.action_view_invoice(master)

    def action_view_invoice(self, invoice):
        if invoice.type.startswith('out'):
            action = self.env.ref('account.action_invoice_tree1')
            view = [(self.env.ref('account.invoice_form').id, 'form')]
        else:
            action = self.env.ref('account.action_vendor_bill_template')
            view = [(self.env.ref('account.invoice_supplier_form').id, 'form')]
        res = action.read()[0]
        res.update({
            'res_id': invoice.id,
            'views': view,
            'view_type': 'form',
            'view_mode': 'form',
        })
        return res
