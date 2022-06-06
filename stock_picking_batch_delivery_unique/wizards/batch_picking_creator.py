###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockPickingBatchCreator(models.TransientModel):
    _inherit = 'stock.picking.batch.creator'

    def _prepare_stock_batch_picking(self):
        res = super()._prepare_stock_batch_picking()
        carrier_ids = []
        pickings = self.env['stock.picking'].browse(
            self.env.context.get('active_ids', []))
        for picking in pickings:
            carrier_ids.append(picking.carrier_id.id)
        if len(list(set(carrier_ids))) == 1:
            res.update({
                'carrier_id': carrier_ids[0],
            })
        return res
