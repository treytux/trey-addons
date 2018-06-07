# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    procure_method = fields.Selection(
        selection_add=[('mts_mto', 'MTS + MTO')])

    @api.multi
    def action_confirm(self):
        moves_mts_mtos = self.browse(
            [m.id for m in self if m.procure_method == 'mts_mto'])
        super(StockMove, moves_mts_mtos).action_confirm()
        for move in moves_mts_mtos:
            super(StockMove, move).action_assign()
            if move.reserved_availability == move.product_uom_qty:
                move.procure_method = 'make_to_stock'
            else:
                move.procure_method = 'make_to_order'
        return super(StockMove, self).action_confirm()
