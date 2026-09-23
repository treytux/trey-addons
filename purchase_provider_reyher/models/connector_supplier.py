###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json
import logging
from datetime import timedelta

import requests
from odoo import _, fields, models
from odoo.exceptions import ValidationError

_log = logging.getLogger(__name__)


class ConnectorSupplier(models.Model):
    _inherit = 'connector.supplier'

    supplier_mode = fields.Selection(
        selection_add=[
            ('reyher', 'Reyher'),
        ],
    )
    token_reyher = fields.Char(
        string='Token Reyher',
        help='Token Reyher. Valid for 10 years',
    )
    token_validity_date_reyher = fields.Date(
        string='Token validity date Reyher',
    )
    reyher_batch_size = fields.Integer(
        string='Reyher batch size',
        help='Limit of items by requests.',
        default=100,
        required=True,
    )
    daily_limit_reyher = fields.Integer(
        string='Reyher daily limit',
        help='Limit of daily requests.',
        default=300,
        required=True,
    )
    reyher_delay_between_requests = fields.Integer(
        string='Delay between requests (minutes)',
        help='Delay between request batches for Reyher syncs in minutes',
        default=1,
    )
    reyher_url_base = fields.Char(
        string='Reyher URL Base',
        default='https://rio.reyher.de/rest/reyher_int_de/V1',
        required=True,
    )
    reyher_endpoint_simulate = fields.Char(
        string='Reyher URL Simulate',
        default='/sapordersimulate/mine/getOrdersimulate',
        required=True,
    )

    def reyher_request_authentication_token(self):
        url_authenticate = (
            'https://rio.reyher.de/rest/reyher_int_de/V1/integration/customer'
            'token')
        data = {
            'username': self.username_ws,
            'password': self.password_ws,
        }
        headers = {
            'Content-Type': 'application/json',
        }
        _log.info('Reyher API: Login')
        response = requests.post(
            url=url_authenticate, headers=headers, data=json.dumps(data))
        _log.info('Reyher API: Processing login token')
        if response.status_code != 200:
            raise ValidationError(_(
                'Error when communicating with API: %s') %
                response.content.decode('utf-8'))
        self.token_reyher = response.content.decode('utf-8')
        self.token_validity_date_reyher = (
            fields.Date.today() + timedelta(days=365))

    def reyher_get_order_simulate(self, data):
        self.ensure_one()
        if (not self.token_reyher
                or fields.Date.today() > self.token_validity_date_reyher):
            self.reyher_request_authentication_token()
        url_simulate = self.reyher_url_base + self.reyher_endpoint_simulate
        headers = {
            'Authorization': 'Bearer %s' % self.token_reyher,
            'accept': 'application/json',
            'content-type': 'application/json',
        }
        _log.info('Reyher API: Simulate order')
        if not data:
            raise ValidationError(_('No data to simulate'))
        response = requests.post(
            url=url_simulate, headers=headers, data=json.dumps(data))
        if response.status_code != 200:
            raise ValidationError(_(
                'Error when communicating with API: %s') %
                response.content.decode('utf-8'))
        content = json.loads(response.content)
        if not content:
            raise ValidationError(_('Error: not content found in response'))
        return content
