###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def get_purchase_last_price(self):
        if not self:
            return 0.0
        line = self.purchase_line_id
        if not line or not line.product_qty:
            return 0.0
        return line.price_subtotal / line.product_qty

    @api.multi
    def _action_done(self):
        super()._action_done()
        moves_done = self.filtered(
            lambda m: m.state == 'done'
            and m.picking_id
            and m.picking_id.picking_type_code == 'incoming'
        )
        for move in moves_done:
            if not move.product_id or not move.purchase_line_id:
                continue
            move.product_id.purchase_last_price = move.get_purchase_last_price()
            so_lines_with_moves_no_done = self.env['stock.move'].search([
                ('product_id', '=', move.product_id.id),
                ('state', '!=', 'done'),
                ('sale_line_id', '!=', False),
            ]).mapped('sale_line_id')
            for so_line in so_lines_with_moves_no_done:
                so_line.set_purchase_last_price(move.get_purchase_last_price())
