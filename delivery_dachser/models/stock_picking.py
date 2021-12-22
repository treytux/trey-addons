###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _prepare_dachser_wizard(self):
        self.ensure_one()
        return {
            'picking_id': self.id,
        }

    def action_open_dachser_wizard(self):
        self.ensure_one()
        wizard_vals = self._prepare_dachser_wizard()
        wizard = self.env['delivery.dachser'].create(wizard_vals)
        action = self.env.ref(
            'delivery_dachser.delivery_dachser_wizard_action').read()[0]
        action['res_id'] = wizard.id
        action['context'] = self._context.copy()
        return action
