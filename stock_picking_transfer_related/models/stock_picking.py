###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_show_pending_transfer(self):
        def find_transfer_pending(move=None, picking_type_code='outgoing'):
            domain = [
                ('product_id', '=', move.product_id.id),
                ('state', 'not in', ['cancel', 'done']),
            ]
            if picking_type_code == 'incoming':
                domain += [
                    ('location_id', '=', move.location_dest_id.id),
                ]
            else:
                domain += [
                    ('location_id', '=', move.location_dest_id.id),
                ]
            moves = self.env['stock.move'].search(
                domain, order='date_expected')
            if not moves:
                return self.env['stock.picking']
            return moves.mapped('picking_id')

        if self.picking_type_code not in ('incoming', 'outgoing'):
            return {}
        picking_list = self.env['stock.picking']
        for move in self.move_lines:
            picking_list |= find_transfer_pending(move, self.picking_type_code)
        if not picking_list:
            return {}
        return {
            'name': _('Transfers Pending'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'res_ids': picking_list.ids,
            'domain': [('id', 'in', picking_list.ids)],
            'type': 'ir.actions.act_window',
        }
