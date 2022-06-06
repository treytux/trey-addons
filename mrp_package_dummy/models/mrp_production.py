###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def action_package_dummy_read(self):
        self.ensure_one()
        wizard = self.env['stock.package_dummy.read'].create({
            'production_id': self.id,
            'location_id': self.location_dest_id.id,
            'action': 'mrp_production',
        })
        action = self.env.ref(
            'stock_package_dummy.stock_package_dummy_read_action').read()[0]
        action['res_id'] = wizard.id
        return action
