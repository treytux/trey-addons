###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        super()._compute_amount()
        for line in self:
            purchase_last_price = (
                line.price_subtotal / line.product_qty if line.product_qty else 0)
            incoming_moves = line.move_ids.filtered(
                lambda move: move.state == 'done'
                and move.picking_id.picking_type_code == 'incoming'
            )
            if not incoming_moves:
                continue
            date_done_transfer = max(incoming_moves.mapped('date'))
            domain_moves_out = [
                ('product_id', '=', line.product_id.id),
                ('state', '=', 'done'),
                ('picking_id.picking_type_code', '=', 'outgoing'),
                ('sale_line_id', '!=', False),
                ('date', '>=', date_done_transfer),
            ]
            next_done_transfer = self.env['stock.move'].search([
                ('id', 'not in', line.move_ids.ids),
                ('product_id', '=', line.product_id.id),
                ('state', '=', 'done'),
                ('picking_id.picking_type_code', '=', 'incoming'),
                ('date', '>', date_done_transfer),
            ], order='date asc', limit=1)
            if next_done_transfer:
                domain_moves_out.append(
                    ('date', '<', next_done_transfer.date)
                )
            else:
                line.product_id.purchase_last_price = purchase_last_price
            moves_to_update = self.env['stock.move'].search(domain_moves_out)
            sale_lines_to_update = moves_to_update.mapped('sale_line_id')
            sale_lines_to_update.set_purchase_last_price(purchase_last_price)
