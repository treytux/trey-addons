###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        self.ensure_one()
        if self.carrier_id or self._context.get('force_button_validate'):
            return super().button_validate()
        picking_type_repair_out = self.env.ref(
            'purchase_order_repair.stock_picking_type_out_repair')
        if self.picking_type_id == picking_type_repair_out:
            self = self.with_context(force_button_validate=True)
            return self.action_open_carrier_wizard()
        return super().button_validate()
