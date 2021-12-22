###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _action_launch_stock_rule(self):
        return super(
            SaleOrderLine, self.filtered(
                lambda line: line.product_id.pack_ok is False)
        )._action_launch_stock_rule()

    def _get_pack_deliveried(self):
        res = {}
        pack_lines = {
            ln.product_id.id: ln.quantity
            for ln in self.product_id.pack_line_ids
        }
        for move in self.mapped('pack_child_line_ids.move_ids'):
            if move.product_id.id not in pack_lines:
                continue
            if move.product_id.id not in res:
                res[move.product_id.id] = 0
            if move.state != 'done':
                continue
            qty = move.product_uom_qty / pack_lines[move.product_id.id]
            if move.location_dest_id.usage == 'customer':
                is_move_to_refund = (
                    not move.origin_returned_move_id
                    or (move.origin_returned_move_id and move.to_refund))
                if is_move_to_refund:
                    res[move.product_id.id] += qty
            elif move.location_dest_id.usage != 'customer' and move.to_refund:
                res[move.product_id.id] -= qty
        if len(res) != len(pack_lines):
            return 0
        if not res:
            return 0
        return min([v for k, v in res.items()])

    @api.depends(
        'pack_child_line_ids',
        'pack_child_line_ids.move_ids.state',
        'pack_child_line_ids.move_ids.scrapped',
        'pack_child_line_ids.move_ids.product_uom_qty',
        'pack_child_line_ids.move_ids.product_uom'
    )
    def _compute_qty_delivered(self):
        super(SaleOrderLine, self)._compute_qty_delivered()
        for line in self.filtered(lambda ln: ln.pack_child_line_ids):
            qty_delivered_pack = line._get_pack_deliveried()
            line.qty_delivered = qty_delivered_pack

    @api.depends(
        'pack_child_line_ids',
        'pack_child_line_ids.qty_invoiced',
        'pack_child_line_ids.qty_delivered',
        'pack_child_line_ids.product_uom_qty',
        'pack_child_line_ids.order_id.state'
    )
    def _get_to_invoice_qty(self):
        super(SaleOrderLine, self)._get_to_invoice_qty()
