###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    is_return = fields.Boolean(
        string='Is return',
    )
    is_change = fields.Boolean(
        string='Is return change',
    )

    @api.multi
    def _action_confirm(self, merge=True, merge_into=False):
        for move in self:
            if not move.sale_line_id:
                continue
            sale_line = move.sale_line_id
            to_change = sale_line.qty_changed - sale_line.qty_change
            if not to_change:
                continue
            return_type = self.picking_type_id.return_picking_type_id
            new_move = self.copy({
                'is_return': False,
                'is_change': True,
                'product_uom_qty': self.sale_line_id.qty_change,
                'origin_returned_move_id': move.id,
                'picking_type_id': return_type.id,
                'location_id': return_type.default_location_src_id.id,
                'location_dest_id': self.location_id.id})
            self |= new_move
        return super()._action_confirm(merge, merge_into)
