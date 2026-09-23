###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    purchase_count = fields.Integer(
        string='Purchase order count',
        compute='_compute_purchase_count',
    )
    purchase_order_count_technical = fields.Integer(
        string='Number of purchase order generated (technical)',
        compute='_compute_purchase_order_count_technical',
        help='Technical field that does the same thing as the '
             '"purchase_order_count" field of the "sale_purchase" module but '
             'without including the "groups" which restricts its visibility '
             'and use to users who do not belong to the "Purchases/User" '
             'group.',
    )

    @api.depends('order_line.purchase_line_ids.order_id')
    def _compute_purchase_order_count_technical(self):
        for sale in self:
            sale.purchase_order_count_technical = len(
                sale._get_purchase_orders())

    def get_purchase_order_ids(self, sale_order):
        if not sale_order.id:
            return []
        purchase_order_ids = []
        purchase_order_line = self.env['purchase.order.line']
        move_ids = self.env['stock.move'].search([
            ('sale_line_id.id', 'in', sale_order.order_line.ids),
        ]).ids
        if move_ids:
            purchase_lines = purchase_order_line.search([
                ('move_dest_ids', 'in', move_ids),
            ])
            purchase_order_ids += purchase_lines.mapped('order_id').ids
        purchase_lines = purchase_order_line.search([
            '|',
            ('sale_line_id.id', 'in', sale_order.order_line.ids),
            ('sale_order_id.id', '=', sale_order.id),
        ])
        purchase_order_ids += purchase_lines.mapped('order_id').ids
        purchase_orders = self.env['purchase.order'].search([
            ('origin', 'ilike', sale_order.name),
        ])
        purchase_order_ids += purchase_orders.ids
        return list(set(purchase_order_ids))

    @api.depends('state')
    def _compute_purchase_count(self):
        for order in self:
            order.purchase_count = len(self.get_purchase_order_ids(order))

    def action_view_sale_purchase_link(self):
        purchase_order_ids = self.get_purchase_order_ids(self)
        form_view = self.env.ref('purchase.purchase_order_form')
        tree_view = self.env.ref('purchase.purchase_order_tree')
        search_view = self.env.ref('purchase.view_purchase_order_filter')
        if len(purchase_order_ids) > 1 or not purchase_order_ids:
            return {
                'name': _('Purchase orders'),
                'res_model': 'purchase.order',
                'type': 'ir.actions.act_window',
                'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
                'view_mode': 'tree, form',
                'search_view_id': search_view.id,
                'view_type': 'form',
                'domain': [('id', 'in', purchase_order_ids)],
            }
        if len(purchase_order_ids) == 1:
            return {
                'name': _('Purchase orders'),
                'res_model': 'purchase.order',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'search_view_id': search_view.id,
                'view_type': 'form',
                'res_id': purchase_order_ids[0],
            }
