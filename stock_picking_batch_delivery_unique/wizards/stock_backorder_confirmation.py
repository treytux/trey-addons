###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    batch_id = fields.Many2one(
        comodel_name='stock.picking.batch',
        string='Batch',
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        batch = self.env.context.get('batch')
        if 'batch_id' not in res and batch:
            res['batch_id'] = batch.id
        return res

    def _process(self, cancel_backorder=False):
        if not self.batch_id:
            return super()._process(cancel_backorder=cancel_backorder)
        picking_ids = self.batch_id.get_pickings_to_validate()
        res = super()._process(cancel_backorder=cancel_backorder)
        simulate_picking = self.batch_id.create_simulate_stock_picking(
            picking_ids)
        info = simulate_picking.carrier_id.send_shipping(simulate_picking)
        self.batch_id.create_attachments(
            self.batch_id.get_picking_attachments(simulate_picking))
        self.batch_id.add_shipping_info(self.batch_id.picking_ids.filtered(
            lambda p: p.state == 'done' and p.id in picking_ids), info)
        simulate_picking.unlink()
        return res
