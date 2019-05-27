###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    auto_shipping_cost = fields.Boolean(
        string='Auto add shipping cost in sale order')
