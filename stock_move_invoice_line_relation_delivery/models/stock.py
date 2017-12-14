# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _invoice_create_line(self, moves, journal_id, inv_type='out_invoice'):
        invoice_ids = super(StockPicking, self)._invoice_create_line(
            moves, journal_id, inv_type=inv_type)
        for move in moves:
            for invoice in move.picking_id.sale_id.invoice_ids:
                if invoice.id in invoice_ids:
                    invoice['stock_move_id'] = move.id
        return invoice_ids
