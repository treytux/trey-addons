###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class DeliveryCarrierManifest(models.Model):
    _inherit = 'delivery.carrier.manifest'

    signature = fields.Binary(
        string='Signature',
    )
    signature_date = fields.Date(
        string='Signature date',
    )
    is_signed = fields.Boolean(
        string='Is signed',
    )

    def action_sign_manifest(self):
        self.ensure_one()
        action = self.env.ref(
            'delivery_carrier_manifest_signature.manifest_signature_action')
        action = action.read()[0]
        return action
