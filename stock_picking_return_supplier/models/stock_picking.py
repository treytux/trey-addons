###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    purchase_count = fields.Integer(
        string='Number of purchase',
        compute='_compute_purchase_count',
    )
    picking_count = fields.Integer(
        string='Number of picking',
        compute='_compute_picking_count',
    )

    def get_purchase_order_ids(self):
        purchase_line_ids = self.move_lines.mapped('purchase_line_id')
        purchase_ids = list(set(purchase_line_ids.mapped('order_id').ids))
        purchases = self.env['purchase.order'].browse(purchase_ids)
        return purchases.ids

    def get_picking_ids(self):
        origin_move_ids = self.move_lines.mapped('origin_returned_move_id').ids
        moves = self.env['stock.move'].browse(origin_move_ids)
        origin_picking_ids = moves.mapped('picking_id').ids
        return list(set(origin_picking_ids))

    @api.multi
    def _compute_purchase_count(self):
        for picking in self:
            picking.purchase_count = len(picking.get_purchase_order_ids())

    @api.multi
    def _compute_picking_count(self):
        for picking in self:
            picking.picking_count = len(picking.get_picking_ids())

    def action_view_picking_purchase_link(self):
        purchase_order_ids = self.get_purchase_order_ids()
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
            'domain': [('id', 'in', purchase_order_ids)],
        }
        if len(purchase_order_ids) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': purchase_order_ids[0],
            })
        return action_vals

    def action_view_picking_origin_move_link(self):
        picking_order_ids = self.get_picking_ids()
        form_view = self.env.ref('stock.view_picking_form')
        tree_view = self.env.ref('stock.vpicktree')
        search_view = self.env.ref('stock.view_picking_internal_search')
        action_vals = {
            'name': _('Stock pickings'),
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree, form',
            'search_view_id': search_view.id,
            'view_type': 'form',
            'domain': [('id', 'in', picking_order_ids)],
        }
        if len(picking_order_ids) == 1:
            del action_vals['views']
            action_vals.update({
                'view_mode': 'form',
                'res_id': picking_order_ids[0],
            })
        return action_vals
