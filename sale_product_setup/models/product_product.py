###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_component_view(self):
        if not self.setup_product_ids:
            return {'type': 'ir.actions.act_window_close'}
        action = self.env.ref('product.product_normal_action').read()[0]
        action['domain'] = [('id', 'in', self.setup_product_ids.ids)]
        return action
