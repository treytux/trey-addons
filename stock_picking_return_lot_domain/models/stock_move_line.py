###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    return_lot_ids = fields.Many2many(
        comodel_name='stock.production.lot',
        relation='stock_move_line2stock_production_lot_rel',
        column1='stock_move_line_id',
        column2='lot_id',
        string='Return lots',
        compute='_compute_return_lot_ids',
        store=True,
    )

    @api.depends('product_id', 'move_id.picking_id.move_lines.move_orig_ids')
    def _compute_return_lot_ids(self):
        for line in self:
            if line.product_id.tracking == 'none':
                continue
            line.return_lot_ids = [
                (6, 0, line.move_id.picking_id.move_lines.mapped(
                    'move_orig_ids.move_line_ids.lot_id').ids)
            ]
