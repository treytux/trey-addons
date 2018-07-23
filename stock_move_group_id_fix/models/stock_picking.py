# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def copy(self, default=None):
        new_picking = super(StockPicking, self).copy(default)
        if not new_picking.backorder_id.exists():
            for move in new_picking.move_lines:
                move.group_id = None
        return new_picking
