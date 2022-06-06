###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json
from datetime import datetime, timedelta

import requests
from odoo import _, exceptions, fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(
        selection_add=[('dhl', 'DHL')],
    )
    dhl_user_code = fields.Char(
        string='User code',
        help='User code for DHL webservice',
    )
    dhl_username = fields.Char(
        string='User',
        help='Username for DHL webservice',
    )
    dhl_password = fields.Char(
        string='Password',
        help='Password for DHL webservice',
    )
    dhl_token = fields.Char(
        string='Access token',
        help='Access token. Valid for 30 minutes',
    )
    dhl_token_expiration = fields.Datetime(
        string='Access Token Validity',
        default=fields.Datetime.now,
    )
    dhl_payment = fields.Selection(
        selection=[
            ('CPT', 'Paid'),
            ('EXW', 'Unpaid'),
        ],
        default='CPT',
        string='Payment type',
    )
    dhl_label_format = fields.Selection(
        selection=[
            ('PDF', 'PDF'),
            ('ZPL', 'ZPL'),
            ('EPL', 'EPL'),
        ],
        default='PDF',
        string='Label',
    )

    def dhl_authenticate(self):
        if self.dhl_token_expiration > datetime.now():
            return
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
        }
        url = 'https://external.dhl.es/cimapi/api/v1/customer/authenticate'
        data = {
            'Username': self.dhl_username,
            'Password': self.dhl_password,
        }
        data = json.dumps(data)
        res = requests.post(url, headers=headers, data=data)
        if res.status_code != 200:
            raise exceptions.UserError(
                _('DHL exception: %s, %s') % res.status_code, res.reason)
        self.dhl_token = res.text.replace('"', '')
        self.dhl_token_expiration = datetime.now() + timedelta(minutes=25)

    def dhl_send(self, data):
        self.dhl_authenticate()
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer {}'.format(self.dhl_token),
        }
        url = 'https://external.dhl.es/cimapi/api/v1/customer/shipment'
        data = json.dumps(data)
        res = requests.post(url, headers=headers, data=data)
        return res

    def dhl_send_shipping(self, pickings):
        return [self.dhl_create_shipping(p) for p in pickings]

    def _dhl_prepare_create_shipping(self, picking):
        self.ensure_one()
        partner = picking.partner_id
        phone = (partner.phone and partner.phone.replace(' ', '') or '')
        shipping_weight = (
            picking.shipping_weight
            and round(picking.weight_uom_id._compute_quantity(
                picking.shipping_weight, self.env.ref('uom.product_uom_kgm')))
            or 1)
        return {
            'Customer': self.dhl_user_code,
            'Receiver': {
                'Name': partner.name,
                'Address': partner.street,
                'City': partner.city,
                'PostalCode': partner.zip,
                'Country': partner.country_id.code,
                'Phone': phone,
                'Email': partner.email,
            },
            'Sender': {
                'Name': picking.company_id.name,
                'Address': picking.company_id.street,
                'City': picking.company_id.city,
                'PostalCode': picking.company_id.zip,
                'Country': picking.company_id.country_id.code,
                'Phone': picking.company_id.phone,
                'Email': picking.company_id.email,
            },
            'Reference': picking.name,
            'Quantity': picking.number_of_packages,
            'Weight': shipping_weight,
            'WeightVolume': '',
            'CODAmount': '',
            'CODExpenses': 'P',
            'CODCurrency': 'EUR',
            'InsuranceAmount': '',
            'InsuranceExpenses': 'P',
            'DeliveryNote': '',
            'Remarks1': '',
            'Remarks2': '',
            'Incoterms': self.dhl_payment,
            'ContactName': '',
            'GoodsDescription': '',
            'CustomsValue': '',
            'CustomsCurrency': '',
            'PayerAccount': '',
            'Features': '',
            'Format': self.dhl_label_format,
        }

    def _zebra_label_custom(self, label):
        return label

    def dhl_create_shipping(self, picking):
        self.ensure_one()
        package_info = self._dhl_prepare_create_shipping(picking)
        picking.write({
            'dhl_last_request': fields.Datetime.now(),
        })
        res = self.dhl_send(package_info)
        picking.write({
            'dhl_last_response': fields.Datetime.now(),
        })
        response = json.loads(res.content)
        if res.status_code != 200:
            raise exceptions.UserError(
                _('DHL exception: %s') % response['Message'])
        picking.carrier_tracking_ref = response['Tracking']
        picking.dhl_year = response['Year']
        if self.dhl_label_format == 'PDF':
            self.env['ir.attachment'].create({
                'name': 'DHL_%s' % picking.carrier_tracking_ref,
                'datas': response['Label'],
                'datas_fname': 'dhl_%s.pdf' % picking.carrier_tracking_ref,
                'res_model': 'stock.picking',
                'res_id': picking.id,
                'mimetype': 'application/pdf',
            })
        else:
            self.env['ir.attachment'].create({
                'name': 'DHL_%s' % picking.carrier_tracking_ref,
                'datas': response['Label'].encode('utf-8'),
                'datas_fname': 'dhl_%s.txt' % picking.carrier_tracking_ref,
                'res_model': 'stock.picking',
                'res_id': picking.id,
                'mimetype': 'application/txt',
            })
        response['tracking_number'] = picking.carrier_tracking_ref
        response['exact_price'] = 0
        return response

    def dhl_cancel_shipment(self, pickings):
        self.dhl_authenticate()
        for picking in pickings:
            headers = {
                'Accept': 'application/json',
                'Authorization': 'Bearer {}'.format(self.dhl_token),
            }
            url = (
                'https://external.dhl.es/cimapi/api/v1/customer/shipment'
                '?Year=%s&Tracking=%s&Action=DELETE' % (
                    picking.dhl_year, picking.carrier_tracking_ref)
            )
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                continue
            elif res.status_code == 400:
                response = json.loads(res.content)
                raise exceptions.UserError(
                    _('DHL exception: %s') % response['Message'])
            else:
                raise exceptions.UserError(
                    _('DHL exception error code: %s') % res.status_code)
        return True

    def dhl_tracking_state_update(self, picking):
        self.ensure_one()
        if not self.dhl_username:
            picking.tracking_state_history = _(
                'Status cannot be checked, enter webservice carrier '
                'credentials')
            return
        url = (
            'https://external.dhl.es/cimapi/api/v1/customer/track?id=%s' % (
                picking.carrier_tracking_ref)
        )
        picking.write({
            'dhl_last_request': fields.Datetime.now(),
        })
        self.dhl_authenticate()
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer {}'.format(self.dhl_token),
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 400:
            res = json.loads(response.content)
            raise exceptions.UserError(
                _('DHL exception: %s') % res['Message'])
        if response.status_code != 200:
            raise exceptions.UserError(
                _('DHL exception error code: %s') % response.status_code)
        res = json.loads(response.content)
        picking.write({
            'dhl_last_response': fields.Datetime.now(),
        })
        picking.tracking_state_history = '%s %s | %s' % (
            res[0]['Status'], res[0]['Ubication'], res[0]['DateTime'])
        state = res[0]['Code']
        static_states = {
            'T': 'in_transit',
            'A': 'in_transit',
            'AI': 'in_transit',
            'R': 'customer_delivered',
        }
        picking.delivery_state = static_states.get(state, 'incidence')

    def dhl_get_tracking_link(self, picking):
        return (
            'https://clientesparcel.dhl.es/LiveTracking/ModificarEnvio/'
            'es?codigo=%s&amp;app=TRACKING' % picking.carrier_tracking_ref
        )

    def dhl_rate_shipment(self, order):
        raise NotImplementedError(_('''
            DHL API doesn't provide methods to compute delivery
            rates, so you should relay on another price method instead or
            override this one in your custom code.
        '''))
