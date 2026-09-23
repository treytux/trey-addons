# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _prepare_values_extra_move(
            self, cr, uid, op, product, remaining_qty, context=None):
        res = super(StockPicking, self)._prepare_values_extra_move(
            cr, uid, op, product, remaining_qty, context=context)
        if 'purchase_line_id' in res:
            return res
        purchase_lines = op.linked_move_operation_ids.mapped(
            'move_id.purchase_line_id')
        if purchase_lines:
            res.update({
                'purchase_line_id': purchase_lines[0].id,
            })
        else:
            purchase_lines_rel = op.picking_id.move_lines.filtered(
                lambda m: m.product_id == op.product_id).mapped(
                'purchase_line_id')
            if purchase_lines_rel:
                res.update({
                    'purchase_line_id': purchase_lines_rel[0].id,
                })
        return res
