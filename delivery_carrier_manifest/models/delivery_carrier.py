###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    manifest_ids = fields.One2many(
        comodel_name='delivery.carrier.manifest',
        inverse_name='carrier_id',
        string='Delivery Manifests',
        readonly=True,
    )
