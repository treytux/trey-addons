###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def send_to_shipper(self):
        if self.carrier_id and self.batch_id:
            return
        res = super().send_to_shipper()
        return res

    @api.one
    def cancel_shipment(self):
        res = super().cancel_shipment()
        pickings = self.env['stock.picking'].search([
            ('id', '!=', self.id),
            ('batch_id', '=', self.batch_id.id),
        ])
        for picking in pickings:
            msg = 'Shipment %s cancelled' % picking.carrier_tracking_ref
            picking.message_post(body=msg)
            picking.write({
                'delivery_state': 'canceled_shipment',
                'date_delivered': False,
                'date_shipped': False,
                'carrier_tracking_ref': False,
            })
        return res
