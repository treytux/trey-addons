###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_cancel(self):
        for move in self:
            for move_dest in move.move_dest_ids:
                allow = all(move_dest.route_ids.mapped(
                    'allow_cancel_picking_relationed'))
                if allow and move_dest.state == 'waiting':
                    move_dest.write({
                        'move_orig_ids': [(3, move.id)],
                        'state': 'draft',
                        'procure_method': 'make_to_stock',
                    })
                    move_dest._action_confirm()
        return super()._action_cancel()
