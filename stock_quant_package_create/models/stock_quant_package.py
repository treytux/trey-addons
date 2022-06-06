###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    def action_add_products(self):
        self.ensure_one()
        wizard = self.env['stock.quant.package.create'].create({
            'package_id': self.id,
            'name': self.name,
        })
        action = self.env.ref(
            'stock_quant_package_create.stock_quant_package_add_action')
        action = action.read()[0]
        action['res_id'] = wizard.id
        return action
