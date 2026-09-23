###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    shipping_weight = fields.Float(
        readonly=True,
    )
    shipping_weight_validate = fields.Float(
        string='Shipping weight validate',
        help='Avoid shipping weight recompute to print picking report',
    )

    def send_to_shipper(self):
        if 'weight' in self.env.context:
            self.shipping_weight_validate = self.env.context['weight']
            self.shipping_weight = self.env.context['weight']
        return super().send_to_shipper()
