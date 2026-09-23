# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.multi
    def _create_returns(self):
        new_picking, picking_type_id = super(
            StockReturnPicking, self)._create_returns()
        moves = self.env['stock.picking'].browse(new_picking).move_lines
        for move in moves:
            original_purchase_line = (
                move.origin_returned_move_id and
                move.origin_returned_move_id.purchase_line_id)
            if original_purchase_line:
                move.purchase_line_id = original_purchase_line.id
        return new_picking, picking_type_id
