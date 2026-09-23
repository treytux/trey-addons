###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, exceptions, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_cancel(self):
        allow_sale_cancel = self.env.context.get('allow_sale_cancel', False)
        if not allow_sale_cancel or allow_sale_cancel is False:
            return super()._action_cancel()
        else:
            if any(
                    move.state == 'done'
                    and move.sale_line_id
                    and move.sale_line_id.qty_delivered > 0
                    and not move.scrapped for move in self):
                raise exceptions.UserError(_(
                    'You cannot cancel a stock move that has been set to '
                    '\'Done\' if not all material has been returned. You must '
                    'make the complete return of the move material so that '
                    'the quantity delivered is 0.'))
            elif any(move.state not in ['done', 'cancel'] for move in self):
                moves_to_cancel = self.filtered(
                    lambda m: m.state not in ['cancel', 'done'])
                moves_to_cancel._do_unreserve()
                for move in moves_to_cancel:
                    siblings_states = (move.move_dest_ids.mapped(
                        'move_orig_ids') - move).mapped('state')
                    if move.propagate:
                        if all(state == 'cancel' for state in siblings_states):
                            move.move_dest_ids.filtered(
                                lambda m: m.state != 'done')._action_cancel()
                    else:
                        if all(
                                state in ('done', 'cancel')
                                for state in siblings_states):
                            move.move_dest_ids.write(
                                {'procure_method': 'make_to_stock'})
                            move.move_dest_ids.write(
                                {'move_orig_ids': [(3, move.id, 0)]})
                moves_to_cancel.write({
                    'state': 'cancel',
                    'move_orig_ids': [(5, 0, 0)],
                })
                return True
            return True
