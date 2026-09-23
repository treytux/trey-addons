###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _apply_price_unit_diff(self, price_unit_diff):
        relation_obj = self.env['stock.move.line.relation']
        move_line_relations = relation_obj.search([
            ('move_line_id', 'in', self.ids),
        ])
        update_move_lines = self
        update_move_lines |= self.search([
            ('move_line_relation_ids', 'in', move_line_relations.ids),
        ], order='date')
        for move_line in update_move_lines:
            move = move_line.move_id
            relations = move.move_line_ids.mapped('move_line_relation_ids')
            if relations:
                value = sum([r.quantity * r.price_unit for r in relations])
            else:
                price_unit = abs(move.price_unit) + price_unit_diff
                update_relations = relation_obj.search([
                    ('move_line_id', 'in', move_line.ids),
                ])
                update_relations.write({
                    'price_unit': price_unit,
                })
                value = price_unit * move.product_uom_qty
            value *= -1 if move._is_out() else 1
            price_unit = value / move.product_uom_qty
            move.write({
                'price_unit': price_unit,
                'value': value,
                'remaining_value': price_unit * move.remaining_qty
            })
        return update_move_lines
