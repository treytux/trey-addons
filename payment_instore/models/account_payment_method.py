###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import requests
from odoo import _, api, models
from odoo.exceptions import ValidationError
from requests.exceptions import ConnectTimeout, ReadTimeout


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res['instore'] = {
            'mode': _('multi'),
            'domain': [
                ('type', '=', 'bank'),
            ],
        }
        return res

    def get_instore_error_dict(self, error_code):
        error_mapping = self.env['instore.error.mapping'].search([
            ('code', '=', error_code),
        ])
        if len(error_mapping) != 1:
            return _('Unknown error: %s') % error_code
        return '%s: %s' % (error_code, error_mapping.description)

    def _write_instore_values(self, invoice, payment, instore_data):
        vals_list = {
            'transactionId': 'last_instore_txn_id',
            'transactionNumber': 'last_instore_tx_number',
            'status': 'instore_device_tx_status',
            'deviceId': 'instore_device_id',
        }
        for val in vals_list:
            if val in instore_data:
                invoice[vals_list[val]] = instore_data[val]
                payment[vals_list[val]] = instore_data[val]

    def generate_instore_tpv_transaction(self, app_key, instore_url_base):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'x-apikey': app_key,
        }
        generate_transaction_url = f'{instore_url_base}/createTransaction'
        try:
            response = requests.get(
                generate_transaction_url, headers=headers, verify=False,
                timeout=10)
        except ConnectTimeout as timeout_error:
            raise ValidationError(_(
                'Timeout error, check devices connection:\n %s') % (
                    timeout_error))
        if response.status_code == 200 and response.json().get('transactionId'):
            return response.json()
        else:
            raise ValidationError(_(
                'Error generating transaction:', response.status_code,
                response.text))

    def get_instore_tpv_transaction(self, app_key, instore_url, payment_tx_id):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'x-apikey': app_key,
        }
        generate_transaction_url = f'{instore_url}/getTransaction'
        try:
            response = requests.get(
                generate_transaction_url, headers=headers, verify=False,
                timeout=10, json={'transactionId': payment_tx_id})
        except ConnectTimeout as timeout_error:
            raise ValidationError(_(
                'Timeout error, check devices connection:\n %s') % (
                    timeout_error))
        if response.status_code == 200 and response.json().get('result'):
            response_json = response.json()
            response_status = response_json.get('status', None)
            if response_status not in [-1001, -1002]:
                return False
            return response_json
        else:
            raise ValidationError(_(
                'Error generating transaction:', response.status_code,
                response.text))

    def get_instore_data_request(
            self, app_key, transaction_id, payment, refund_tx_number=False):
        headers = {
            'Content-Type': 'application/json',
            'x-apikey': app_key,
        }
        body = {
            'transactionId': transaction_id,
            'paymentApp': 'comercia',
            'amount': int(
                payment.amount * 10**payment.currency_id.decimal_places),
            'currencyCode': payment.currency_id.name,
            'otherData': {
                'printReceipt': 0,
                'orderId': payment.ref,
            },
        }
        if refund_tx_number:
            body['transactionNumber'] = refund_tx_number
        return headers, body

    def instore_post_request(
            self, data_request, payment_provider, payment, invoice):
        app_key = payment_provider.instore_appconector_key
        instore_url_base = payment_provider.instore_url_base
        device_response_data = self.generate_instore_tpv_transaction(
            app_key, instore_url_base)
        self._write_instore_values(invoice, payment, device_response_data)
        device_transaction_id = device_response_data.get('transactionId', '')
        reversed_transaction_number = (
            invoice.reversed_entry_id.last_instore_tx_number
        )
        url = data_request['url_request']
        headers, body = self.get_instore_data_request(
            app_key, device_transaction_id, payment,
            reversed_transaction_number)
        try:
            response = requests.post(
                url, headers=headers, json=body, verify=False, timeout=90)
        except ReadTimeout as timeout_error:
            device_response_data = self.get_instore_tpv_transaction(
                app_key, instore_url_base, device_transaction_id)
            if (not device_response_data or device_response_data.get('status')
                    not in [-1001, -1002]):
                raise timeout_error
            self._write_instore_values(invoice, payment, device_response_data)
            return
        device_response_data = response.json()
        if response.status_code == 200:
            response_status = device_response_data.get('status', None)
            if response_status not in [-1001, -1002]:
                raise ValidationError(_('Request error: %s') % (
                    self.get_instore_error_dict(response_status),
                ))
            self._write_instore_values(invoice, payment, device_response_data)
        else:
            response_error_code = device_response_data.get('errCode', None)
            if response_error_code:
                raise ValidationError(_('Request error: %s') % (
                    self.get_instore_error_dict(response_error_code),
                ))
            raise ValidationError(_(
                'Request error:', response.status_code, response.text))

    def pay_instore_tpv(self, payment_provider, payment, invoice):
        data_request = {
            'url_request': f'{payment_provider.instore_url_base}/payment',
        }
        self.instore_post_request(
            data_request, payment_provider, payment, invoice)

    def refund_instore_tpv(self, payment_provider, payment, invoice):
        data_request = {
            'url_request': f'{payment_provider.instore_url_base}/refund',
            'reversed_transaction_number': (
                invoice.reversed_entry_id.last_instore_tx_number),
        }
        self.instore_post_request(
            data_request, payment_provider, payment, invoice)
