###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_return = fields.Boolean(
        string='Is Return',
        compute='_compute_is_return')

    @api.one
    @api.depends('amount_total')
    def _compute_is_return(self):
        self.is_return = self.amount_total < 0

    @api.multi
    def _add_supplier_to_product(self):
        if self.is_return:
            return
        return super()._add_supplier_to_product()

    @api.multi
    def action_view_invoice(self):
        self.ensure_one()
        if self.env.context.get('create_bill', None):
            invoices = self.create_invoices()
            return self.show_invoices(invoices)
        return super().action_view_invoice()

    @api.multi
    def create_invoice(self):
        def get_invoice():
            invoices = self.invoice_ids.filtered(lambda i: i.state != 'cancel')
            if invoices:
                return invoices[0]
            return self.env['account.invoice'].create({
                'partner_id': self.partner_id.id,
                'purchase_id': self.id,
                'type': 'in_invoice'})

        def update_invoice_type(invoice):
            total = sum([
                li.purchase_line_id.price_total
                for li in invoice.invoice_line_ids])
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

    @api.multi
    def show_invoices(self, invoices):
        form_view = self.env.ref('account.invoice_supplier_form')
        tree_view = self.env.ref('account.invoice_supplier_tree')
        search_view = self.env.ref('account.view_account_invoice_filter')
        return {
            'name': _('Purchase invoices'),
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree,form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', invoices.ids)],
        }
