###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _prepare_delivery_wizard(self):
        self.ensure_one()
        return {
            'picking_id': self.id,
            'carrier_id': self.carrier_id.id,
        }

    def action_open_carrier_wizard(self):
        self.ensure_one()
        wizard_vals = self._prepare_delivery_wizard()
        wizard = self.env['stock.picking.delivery_wizard'].create(wizard_vals)
        action = self.env.ref(
            'stock_picking_delivery_wizard.'
            'stock_picking_delivery_wizard_action').read()[0]
        action['res_id'] = wizard.id
        action['context'] = self._context.copy()
        return action

    def is_open_carrier_wizard(self):
        self.ensure_one()
        return self.picking_type_code != 'outgoing'

    def button_validate(self):
        self.ensure_one()
        if not self.is_open_carrier_wizard():
            return super().button_validate()
        if self.carrier_id or self._context.get('force_button_validate'):
            return super().button_validate()
        self = self.with_context(force_button_validate=True)
        return self.action_open_carrier_wizard()
