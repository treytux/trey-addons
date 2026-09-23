###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import requests
from odoo import _, fields, models
from odoo.exceptions import ValidationError


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[
            ('instore', 'InStore'),
        ],
        ondelete={
            'instore': 'set default',
        }
    )
    instore_appconector_key = fields.Char(
        string='InStore appconector key',
    )
    instore_url_base = fields.Char(
        string='InStore URL base',
    )

    def test_instore_device(self):
        payment_url = f'{self.instore_url_base}/getVersion'
        headers = {
            'Content-Type': 'application/json',
            'x-apikey': self.instore_appconector_key,
        }
        response = requests.get(
            payment_url, headers=headers, data={}, verify=False, timeout=10)
        if response.status_code != 200:
            raise ValidationError(_(
                'Cannot connect with InStore device:', response.status_code,
                response.text))

    def _get_default_payment_method_id(self, code):
        self.ensure_one()
        if self.code != 'instore':
            return super()._get_default_payment_method_id(code)
        return self.env.ref('payment_instore.payment_method_instore').id
