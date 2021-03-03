###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockPicingDeliveryWizard(models.TransientModel):
    _name = 'stock.picking.delivery_wizard'
    _description = 'Stock picking delivery wizard for select carrier info'

    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Picking',
    )
    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Carrier',
    )
    picking_carrier_id = fields.Many2one(
        related='picking_id.carrier_id',
    )
    number_of_packages = fields.Integer(
        string='Number of packages',
        compute='_compute_values',
        readonly=False,
        store=True,
    )
    weight = fields.Float(
        string='Weight',
        compute='_compute_values',
        readonly=False,
        store=True,
    )

    @api.depends('picking_id')
    def _compute_values(self):
        for wizard in self:
            if not wizard.picking_id:
                continue
            wizard.number_of_packages = wizard.picking_id.number_of_packages
            wizard.weight = wizard.picking_id.shipping_weight

    def _before_send_shippend(self):
        self.ensure_one()
        self.picking_id.write({
            'carrier_id': self.carrier_id.id,
            'number_of_packages': self.number_of_packages,
            'shipping_weight': self.weight,
        })

    def action_update_carrier_info_in_picking(self):
        self.ensure_one()
        if self.picking_id.carrier_id:
            try:
                self.picking_id.cancel_shipment()
            except NotImplementedError:
                pass
        self._before_send_shippend()
        if self._context.get('force_button_validate'):
            return self.picking_id.button_validate()
        if self.carrier_id:
            self.carrier_id.send_shipping(self.picking_id)
