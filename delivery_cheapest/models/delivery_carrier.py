###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    include_cheapest_carrier = fields.Boolean(
        string='Include to calculate the cheapest delivery carrier',
    )
