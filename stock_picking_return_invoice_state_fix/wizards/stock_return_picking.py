# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.multi
    def _create_returns(self):
        data = self.browse(self.ids[0])
        new_picking, picking_type_id = super(
            StockReturnPicking, self)._create_returns()
        moves = self.env['stock.picking'].browse(new_picking).move_lines
        moves.write({'invoice_state': data.invoice_state})
        return new_picking, picking_type_id
