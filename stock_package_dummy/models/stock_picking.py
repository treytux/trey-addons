###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_package_dummy_read(self):
        self.ensure_one()
        wizard = self.env['stock.package_dummy.read'].create({
            'location_id': self.location_dest_id.id,
            'picking_id': self.id,
            'action': 'stock_picking',
        })
        action = self.env.ref(
            'stock_package_dummy.stock_package_dummy_read_action').read()[0]
        action['res_id'] = wizard.id
        return action
