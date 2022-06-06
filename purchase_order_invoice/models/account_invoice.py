###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    purchase_count = fields.Integer(
        string='Purchase order count',
        compute='_compute_purchase_count',
    )

    def get_purchases(self):
        return self.mapped('invoice_line_ids.purchase_id')

    @api.depends('invoice_line_ids', 'invoice_line_ids.purchase_id')
    def _compute_purchase_count(self):
        for invoice in self:
            invoice.purchase_count = len(invoice.get_purchases())

    def action_view_purchase_order_link(self):
        self.ensure_one()
        purchases = self.get_purchases()
        form_view = self.env.ref('purchase.purchase_order_form')
        tree_view = self.env.ref('purchase.purchase_order_tree')
        search_view = self.env.ref('purchase.view_purchase_order_filter')
        action_vals = {
            'name': _('Purchase orders'),
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', purchases.ids)],
        }
        if len(purchases) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': purchases[0].ids,
            })
        return action_vals

    def _prepare_invoice_line_from_po_line(self, line):
        vals = super()._prepare_invoice_line_from_po_line(line)
        if vals['quantity'] != 0:
            return vals
        if line.product_id.purchase_method == 'purchase':
            vals['quantity'] = line.product_qty - line.qty_invoiced
        else:
            vals['quantity'] = line.qty_received - line.qty_invoiced
        return vals
