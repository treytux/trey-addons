###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_done(self):
        for picking in self:
            if not picking.is_return:
                continue
            for line in picking.move_line_ids.filtered(lambda ln: ln.lot_id):
                if not line.move_id.move_orig_ids:
                    continue
                move_lines = line.move_id.move_orig_ids.mapped(
                    'move_line_ids').filtered(
                        lambda ln: ln.lot_id == line.lot_id)
                return_moves = line.move_id.move_orig_ids.mapped(
                    'returned_move_ids').filtered(
                        lambda m: m.id != line.move_id.id)
                qty_returned = sum(
                    return_moves.mapped('move_line_ids').filtered(
                        lambda ln: ln.lot_id == line.lot_id).mapped('qty_done'))
                qty_total = sum(move_lines.mapped('qty_done'))
                qty_res = qty_total - qty_returned
                if line.qty_done > qty_res:
                    raise ValidationError(_(
                        'You cannot return %s units of lot %s when %s '
                        'have been delivered') % (
                        line.qty_done, line.lot_id.name, qty_res))
        return super().action_done()
