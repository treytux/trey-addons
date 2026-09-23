###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, exceptions, fields, models


class StockPickingBatchCreator(models.TransientModel):
    _inherit = 'stock.picking.batch.creator'

    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Carrier',
    )

    def _prepare_stock_batch_picking(self):
        res = super()._prepare_stock_batch_picking()
        carrier_ids = []
        pickings = self.env['stock.picking'].browse(
            self.env.context.get('active_ids', []))
        if len(pickings.mapped('partner_id')) > 1:
            raise exceptions.ValidationError(
                _('Shipping address: different address in the same batch.'))
        if 'done' in pickings.mapped('state'):
            raise exceptions.ValidationError(
                _('Validated pickings cannot be included in batch.'))
        for picking in pickings:
            carrier_ids.append(picking.carrier_id.id)
        if len(list(set(carrier_ids))) == 1:
            res.update({
                'carrier_id': carrier_ids[0],
            })
        return res

    def create_simple_batch(self, domain):
        batch = super().create_simple_batch(domain)
        if self.carrier_id:
            batch.carrier_id = self.carrier_id.id
            for picking in batch.picking_ids:
                picking.carrier_id = self.carrier_id.id
        return batch

    def create_multiple_batch(self, domain):
        batchs = super().create_multiple_batch(domain)
        if self.carrier_id:
            for batch in batchs:
                batch.carrier_id = self.carrier_id.id
                for picking in batch.picking_ids:
                    picking.carrier_id = self.carrier_id.id
        return batchs
