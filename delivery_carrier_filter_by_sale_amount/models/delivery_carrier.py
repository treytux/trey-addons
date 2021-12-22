###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    not_available_from = fields.Boolean(
        string='Not available if order amount is above',
    )
    limit_amount = fields.Float(
        string='Limit amount',
        help='Limit amount so that no shipping method can be selected',
    )
