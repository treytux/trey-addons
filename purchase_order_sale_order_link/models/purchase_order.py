###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sale_count = fields.Integer(
        string='Sale order count',
        compute='_compute_sale_count',
    )

    def get_sale_order_ids(self, purchase_order):
        sale_order_ids = []
        sale_order_obj = self.env['sale.order']
        for line in purchase_order.order_line:
            if line.sale_line_id:
                sale_order_ids += [line.sale_line_id.order_id.id]
            sale_order_ids += [
                move.sale_line_id.order_id.id for move in
                line.move_dest_ids if move.sale_line_id] or []
        if purchase_order.origin:
            for name in purchase_order.origin.split(', '):
                sale_order_ids += sale_order_obj.search([
                    ('name', '=', name),
                ]).ids
        return list(set(sale_order_ids))

    @api.depends('origin', 'order_line')
    def _compute_sale_count(self):
        for order in self:
            order.sale_count = len(self.get_sale_order_ids(order))

    def action_view_purchase_sale_link(self):
        sale_order_ids = self.get_sale_order_ids(self)
        form_view = self.env.ref('sale.view_order_form')
        tree_view = self.env.ref('sale.view_order_tree')
        search_view = self.env.ref('sale.view_sales_order_filter')
        action_vals = {
            'name': _('Sale orders'),
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', sale_order_ids)],
        }
        if len(sale_order_ids) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': sale_order_ids[0],
            })
        return action_vals
