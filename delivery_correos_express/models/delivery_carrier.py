###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import json

import requests
from odoo import _, exceptions, fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(
        selection_add=[('correos_express', 'Correos Express')],
    )
    correos_express_user_code = fields.Char(
        string='User code',
        help='User code for Correos Express webservice',
    )
    correos_express_username = fields.Char(
        string='User',
        help='Username for Correos Express webservice',
    )
    correos_express_password = fields.Char(
        string='Password',
        help='Password for Correos Express webservice',
    )
    correos_express_delivery_type = fields.Selection(
        selection=[
            ('normal', 'Normal'),
            ('office', 'Office'),
            ('informed_date', 'Informed date'),
            ('not_informed_date', 'Not informed date'),
        ],
        default='normal',
        string='Correos Express delivery type',
    )
    correos_express_product_type = fields.Selection(
        selection=[
            ('61', 'Paq10'),
            ('62', 'Paq14'),
            ('92', 'PaqEmpresa14'),
            ('93', 'ePaq24'),
            ('63', 'Paq24'),
            ('66', 'BalearesExpress'),
            ('67', 'CanariasExpress'),
            ('68', 'CanariasAereo'),
            ('69', 'CanariasMaritimo'),
            ('91', 'InternacionalExpress'),
            ('90', 'InternacionalEstandar'),
            ('54', 'EntregaPlus'),
        ],
        default='63',
        string='Product type',
    )
    correos_express_payment = fields.Selection(
        selection=[
            ('P', 'Paid'),
            ('D', 'Unpaid'),
        ],
        default='P',
        string='Payment type',
    )
    correos_express_label_format = fields.Selection(
        selection=[
            ('1', 'PDF'),
            ('2', 'ZPL'),
        ],
        default='1',
        string='Label',
    )
    correos_express_collection_date = fields.Date(
        string='Collection date',
        help='Fixed date to collect the shipping',
    )
    correos_express_office_code = fields.Char(
        string='Office code',
        help='Correos Express office code',
    )
    correos_express_from_time = fields.Char(
        string='First collection time',
        help='The format has to be HH:MM. Example: 16:30',
    )
    correos_express_to_time = fields.Char(
        string='Last collection time',
        help='The format has to be HH:MM. Example: 16:30',
    )
    correos_express_customer_code = fields.Char(
        string='Customer code',
        help='Customer code. Is obligatory if the delivery type is unpaid',
    )

    def correos_express_send(self, data):
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
        }
        if self.prod_environment:
            url = (
                'https://www.correosexpress.com/wpsc/apiRestGrabacionEnvio/'
                'json/grabacionEnvio')
        else:
            url = (
                'https://test.correosexpress.com/wspsc/apiRestGrabacionEnvio/'
                'json/grabacionEnvio')
        auth = (self.correos_express_username, self.correos_express_password)
        data = json.dumps(data)
        res = requests.post(url, headers=headers, auth=auth, data=data)
        response = json.loads(res.content)
        return response

    def correos_express_get_office_list(self, city, cp):
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
        }
        url = ('https://www.correosexpress.com/wpsc/apiRestOficina/v1/oficinas'
               '/listadoOficinas')
        auth = (self.correos_express_username, self.correos_express_password)
        data = {
            'codigoPostal': cp,
            'poblacion': city,
        }
        data = json.dumps(data)
        res = requests.post(url, headers=headers, auth=auth, data=data)
        response = json.loads(res.content)
        return response

    def correos_express_test_connection(self):
        self.ensure_one()
        data = {
            'solicitante': '1',
            'canalEntrada': '',
            'numEnvio': '',
            'ref': 'GrabEnvioNormal',
            'refCliente': '',
            'fecha': '30062021',
            'codRte': '555559999',
            'nomRte': 'PRUEBA EOF2',
            'nifRte': '',
            'dirRte': 'C/NUEVA,2',
            'pobRte': 'MADRID',
            'codPosNacRte': '28010',
            'paisISORte': '',
            'codPosIntRte': '',
            'contacRte': '',
            'telefRte': '',
            'emailRte': '',
            'codDest': '',
            'nomDest': 'PRUEBAEOF',
            'nifDest': '',
            'dirDest': 'MAYOR,22',
            'pobDest': 'MADRID',
            'codPosNacDest': '28010',
            'paisISODest': '',
            'codPosIntDest': '',
            'contacDest': 'CARMEN PEREZ',
            'telefDest': '616666666',
            'emailDest': '',
            'contacOtrs': '',
            'telefOtrs': '',
            'emailOtrs': '',
            'observac': 'ninguna',
            'numBultos': '1',
            'kilos': '1',
            'volumen': '',
            'alto': '',
            'largo': '',
            'ancho': '',
            'producto': '63',
            'portes': 'P',
            'reembolso': '',
            'entrSabado': '',
            'seguro': '',
            'numEnvioVuelta': '',
            'listaBultos': [
                {
                    'alto': '',
                    'ancho': '',
                    'codBultoCli': '',
                    'codUnico': '',
                    'descripcion': '',
                    'kilos': '',
                    'largo': '',
                    'observaciones': '',
                    'orden': '1',
                    'referencia': '',
                    'volumen': ''
                }
            ],
            'codDirecDestino': '',
            'password': 'string',
            'listaInformacionAdicional': [
                {
                    'tipoEtiqueta': '1',
                    'etiquetaPDF': ''
                }
            ]
        }
        response = self.correos_express_send(data)
        return response

    def correos_express_send_shipping(self, pickings):
        return [self.correos_express_create_shipping(p) for p in pickings]

    def _correos_express_prepare_create_shipping(self, picking):
        self.ensure_one()
        partner = picking.partner_id
        company = picking.company_id
        phone = partner.mobile or partner.phone
        phone = (phone and phone.replace(' ', '') or '')
        package_list = []
        shipping_weight = (
            picking.shipping_weight
            and picking.weight_uom_id._compute_quantity(
                picking.shipping_weight,
                self.env.ref('uom.product_uom_kgm'))
            or 0)
        for index in range(1, picking.number_of_packages + 1):
            package_list.append({
                'alto': '',
                'ancho': '',
                'codBultoCli': '',
                'codUnico': '',
                'descripcion': '',
                'kilos': '',
                'largo': '',
                'observaciones': '',
                'orden': index,
                'referencia': '',
                'volumen': '',
            })
        data = {
            'solicitante': self.correos_express_user_code,
            'canalEntrada': '',
            'numEnvio': '',
            'ref': picking.name,
            'refCliente': '',
            'fecha': fields.Datetime.now().strftime('%d%m%Y'),
            'codRte': self.correos_express_user_code,
            'nomRte': company.name,
            'nifRte': '',
            'dirRte': company.street,
            'pobRte': company.city,
            'codPosNacRte': company.zip,
            'paisISORte': '',
            'codPosIntRte': '',
            'contacRte': '',
            'telefRte': '',
            'emailRte': '',
            'codDest': '',
            'nomDest': partner.name,
            'nifDest': '',
            'dirDest': partner.street,
            'pobDest': partner.city,
            'codPosNacDest': partner.zip,
            'paisISODest': '',
            'codPosIntDest': '',
            'contacDest': partner.name,
            'telefDest': phone,
            'emailDest': '',
            'contacOtrs': '',
            'telefOtrs': '',
            'emailOtrs': '',
            'observac': 'ninguna',
            'numBultos': picking.number_of_packages,
            'kilos': round(shipping_weight, 2),
            'volumen': '',
            'alto': '',
            'largo': '',
            'ancho': '',
            'producto': self.correos_express_product_type,
            'portes': self.correos_express_payment,
            'reembolso': '',
            'entrSabado': '',
            'seguro': '',
            'numEnvioVuelta': '',
            'listaBultos': package_list,
            'codDirecDestino': '',
            'password': '',
            'listaInformacionAdicional': [
                {
                    'tipoEtiqueta': self.correos_express_label_format,
                    'etiquetaPDF': ''
                }
            ]
        }
        if self.correos_express_payment == 'D':
            data.update({
                'codDest': self.correos_express_customer_code,
            })
        if self.correos_express_delivery_type == 'office':
            res = self.correos_express_get_office_list(
                partner.city, partner.zip)
            office = res['oficinas'][0]
            data.update({
                'codDirecDestino': office['codigoOficina'],
            })
        elif self.correos_express_delivery_type == 'informed_date':
            shipping_date = self.correos_express_collection_date.strftime(
                '%d%m%Y')
            data.update({
                'listaInformacionAdicional': [
                    {
                        'tipoEtiqueta': self.correos_express_label_format,
                        'etiquetaPDF': '',
                        'creaRecogida': 'S',
                        'fechaRecogida': shipping_date,
                        'horaDesdeRecogida': self.correos_express_from_time,
                        'horaHastaRecogida': self.correos_express_to_time,
                    }
                ]
            })
        elif self.correos_express_delivery_type == 'not_informed_date':
            data.update({
                'listaInformacionAdicional': [
                    {
                        'tipoEtiqueta': self.correos_express_label_format,
                        'etiquetaPDF': '',
                        'creaRecogida': 'S',
                    }
                ]
            })
        msg = _('The number of packages of picking %s is %s') % (
            picking.name, picking.number_of_packages)
        picking.message_post(body=msg)
        return data

    def _zebra_label_custom(self, label):
        return label

    def correos_express_create_shipping(self, picking):
        self.ensure_one()
        package_info = self._correos_express_prepare_create_shipping(picking)
        picking.write({
            'correos_express_last_request': fields.Datetime.now(),
        })
        res = self.correos_express_send(package_info)
        picking.write({
            'correos_express_last_response': fields.Datetime.now(),
        })
        if res['codigoRetorno'] != 0:
            raise exceptions.UserError(
                _('Correos Express exception: %s') % res['mensajeRetorno'])
        picking.carrier_tracking_ref = res['datosResultado']
        if self.correos_express_label_format == '1':
            for index, label in enumerate(res['etiqueta']):
                label_content = base64.b64decode(label['etiqueta1'])
                self.env['ir.attachment'].create({
                    'name': 'Correos Express %s' % (
                            picking.carrier_tracking_ref),
                    'datas': label_content,
                    'datas_fname': 'correos_express_%s_%s.pdf' % (
                        picking.carrier_tracking_ref,
                        index + 1),
                    'res_model': 'stock.picking',
                    'res_id': picking.id,
                    'mimetype': 'application/pdf',
                })
        else:
            for index, label in enumerate(res['etiqueta']):
                label_content = label['etiqueta2']
                label_content = base64.b64encode(label_content.encode('utf-8'))
                self.env['ir.attachment'].create({
                    'name': 'Correos Express %s' % (
                            picking.carrier_tracking_ref),
                    'datas': label_content,
                    'datas_fname': 'correos_express_%s_%s.txt' % (
                        picking.carrier_tracking_ref, index + 1),
                    'res_model': 'stock.picking',
                    'res_id': picking.id,
                    'mimetype': 'application/txt',
                })
        res['tracking_number'] = picking.carrier_tracking_ref
        res['exact_price'] = 0
        return res

    def correos_express_tracking_state_update(self, picking):
        self.ensure_one()
        if not self.correos_express_username:
            picking.tracking_state_history = _(
                'Status cannot be checked, enter webservice carrier '
                'credentials')
            return
        url = (
            'https://www.cexpr.es/wspsc/apiRestSeguimientoEnviosk8s/json/'
            'seguimientoEnvio')
        data = {
            'codigoCliente': self.correos_express_user_code,
            'dato': picking.carrier_tracking_ref,
        }
        data = json.dumps(data)
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json',
        }
        auth = (self.correos_express_username, self.correos_express_password)
        picking.write({
            'correos_express_last_request': fields.Datetime.now(),
        })
        response = requests.post(url, data=data, auth=auth, headers=headers)
        picking.write({
            'correos_express_last_response': fields.Datetime.now(),
        })
        response = response.json()
        if not response or response['error'] != 0:
            return
        tracking_events = response.get('estadoEnvios', [])
        picking.tracking_state_history = '\n'.join(
            [
                '{} {} - [{}] {}'.format(
                    '{}:{}:{}'.format(
                        t.get('horaEstado')[:2],
                        t.get('horaEstado')[2:-2],
                        t.get('horaEstado')[-2:],
                    ),
                    '{}/{}/{}'.format(
                        t.get('fechaEstado')[:2],
                        t.get('fechaEstado')[2:-4],
                        t.get('fechaEstado')[4:],
                    ),
                    t.get('codEstado'),
                    t.get('descEstado'),
                )
                for t in tracking_events
            ]
        )
        tracking = tracking_events.pop()
        picking.tracking_state = '[{}] {}'.format(
            tracking.get('codEstado'), tracking.get('descEstado')
        )

    def correos_express_cancel_shipment(self, pickings):
        raise NotImplementedError(_('''
            Correos Express API does not provide a method to cancel a shipment
            that has been registered. If you need to change some information,
            create a new shipment with a new label. This does not mean that
            the shipment will be invoiced, this only happens if the package
            is picked up and it enters the shipping stage.
        '''))

    def correos_express_get_tracking_link(self, picking):
        return (
            'https://s.correosexpress.com/search?s=%s&amp;cp=%s' % (
                picking.carrier_tracking_ref, picking.partner_id.zip
            )
        )

    def correos_express_rate_shipment(self):
        raise NotImplementedError(_('''
            Correos Express API doesn't provide methods to compute delivery
            rates, so you should relay on another price method instead or
            override this one in your custom code.
        '''))
