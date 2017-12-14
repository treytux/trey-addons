# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_done(self):
        if 'pos_order_lots' not in self.env.context:
            return super(StockPicking, self).action_done()

        def get_product_lot(move):
            for lot in self.env.context['pos_order_lots']:
                equals = all([
                    move.name == lot['name'],
                    move.product_id.id == lot['product_id'],
                    move.product_uom.id == lot['product_uom'],
                    move.product_uom_qty == lot['product_uom_qty']])
                if equals:
                    return lot['lot_id']
            return None

        transfer = self.env['stock.transfer_details'].create({
            'picking_id': self.id})
        for move in self.move_lines:
            self.env['stock.transfer_details_items'].create({
                'sourceloc_id': move.location_id.id,
                'destinationloc_id': move.location_dest_id.id,
                'product_id': move.product_id.id,
                'owner_id': move.partner_id.id,
                'transfer_id': transfer.id,
                'quantity': move.product_uom_qty,
                'product_uom_id': move.product_uom.id,
                'lot_id': get_product_lot(move)})
        transfer.do_detailed_transfer()
        return super(StockPicking, self).action_done()
