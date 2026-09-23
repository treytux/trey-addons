###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import ValidationError


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields=fields)
        if 'product_return_moves' not in res:
            return res
        return_line = self.env['stock.return.picking.line']
        for line_lst in res['product_return_moves']:
            move = self.env['stock.move'].browse(line_lst[2]['move_id'])
            line_lst[2]['quantity'] = return_line.get_limit_return_qty(move)
        return res

    def _create_returns(self):
        for line in self.product_return_moves:
            qty = line.get_limit_return_qty(line.move_id)
            if line.quantity > qty:
                raise ValidationError(
                    _('Is not possible to return more quantity than delivered'))
        return super()._create_returns()


class StockReturnPickingLine(models.TransientModel):
    _inherit = 'stock.return.picking.line'

    def get_limit_return_qty(self, move):
        qty = move.product_qty
        for line in move.move_dest_ids.mapped('move_line_ids'):
            if line.state in ['partially_available', 'assigned']:
                qty -= line.product_qty
            elif line.state == 'done':
                qty -= line.qty_done
        return qty
