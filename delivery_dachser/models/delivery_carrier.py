###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, exceptions, fields, models
from suds.client import Client
from suds.sudsobject import asdict
from suds.transport.https import HttpAuthenticated


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(
        selection_add=[('dachser', 'Dachser')],
    )
    dachser_username = fields.Char(
        string='User',
        help='Username for Dachser webservice',
    )
    dachser_password = fields.Char(
        string='Password',
        help='Password for Dachser webservice',
    )
    dachser_customer_code = fields.Char(
        string='User code',
        help='Customer code for Dachser webservice',
    )
    dachser_customer_label = fields.Char(
        string='Customer label',
        help='Customer label for Dachser webservice',
    )
    dachser_delivery_product = fields.Selection(
        selection=[
            ('001', 'FLEX'),
            ('002', 'SPEED'),
            ('013', 'FIX'),
            ('014', '10'),
            ('016', 'ON SITE PLUS'),
            ('017', 'ON SITE'),
        ],
        default='001',
        string='Dachser delivery product',
    )

    def recursive_dict(self, dictionary):
        out = {}
        for k, v in asdict(dictionary).items():
            if hasattr(v, '__keylist__'):
                out[k] = self.recursive_dict(v)
            elif isinstance(v, list):
                out[k] = []
                for item in v:
                    if hasattr(item, '__keylist__'):
                        out[k].append(self.recursive_dict(item))
                    else:
                        out[k].append(item)
            else:
                out[k] = v
        return out

    def _get_dachser_url(self):
        return 'https://eview.dachser.com/AidaWebServicios/services/'

    def _get_dachser_auth(self):
        return {
            'Authorization': (
                'Basic SU5URVJPUEVSQUJJTElEQUQ6SU5URVJPUEVSQUJJTElEQUQ=')
        }

    def dachser_send(self, data, picking):
        client = Client(
            url=self._get_dachser_url() + 'CargarFicheroExpedicionesWS?wsdl',
            location=self._get_dachser_url() + 'CargarFicheroExpedicionesWS',
            transport=HttpAuthenticated(headers=self._get_dachser_auth()))
        info = client.factory.create('ns4:DatosCargarFicheroExpedicionesVO')
        info.usuario = self.dachser_username
        info.password = self.dachser_password
        info.nombreFichero = picking.id
        info.clienteEtiqueta = self.dachser_customer_label
        info.fichero = data.decode('ascii')
        arg0 = client.factory.create('ns3:DatosOperacionVO')
        response = client.service.cargarFicheroExpediciones(arg0, info)
        response = self.recursive_dict(response)
        return response

    def dachser_send_shipping(self, pickings):
        return [self.dachser_create_shipping(p) for p in pickings]

    def _dachser_prepare_create_shipping(self, picking):
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', picking.id),
            ('res_model', '=', picking._name),
            ('mimetype', '=', 'application/csv'),
        ])
        if not attachments:
            raise exceptions.ValidationError(
                _('Dachser: you have to create the Dachser file using '
                  'the button "Create Dachser file"'))
        if len(attachments) > 1:
            raise exceptions.ValidationError(
                _('Dachser: error when adding the file to shipment request'))
        return attachments[0].datas

    def _zebra_label_custom(self, label):
        return label

    def get_dachser_label(self, picking, token):
        client = Client(
            url=self._get_dachser_url() + 'ObtencionResultadosWS?wsdl',
            location=self._get_dachser_url() + 'ObtencionResultadosWS',
            transport=HttpAuthenticated(headers=self._get_dachser_auth()),
        )
        info = client.factory.create('ns5:DatosObtencionIntegracionVO')
        info.usuario = self.dachser_username
        info.password = self.dachser_password
        info.clienteEtiqueta = self.dachser_customer_label
        info.idPeticion = picking.dachser_token
        arg0 = client.factory.create('ns3:DatosOperacionVO')
        picking.write({
            'dachser_last_request': fields.Datetime.now(),
        })
        try:
            res = client.service.consultaIntegracion(arg0, info)
        except Exception:
            picking.not_dachser_delivery_label = True
            return {
                'tracking_number': '',
                'exact_price': 0,
            }
        res = self.recursive_dict(res)
        picking.write({
            'dachser_last_response': fields.Datetime.now(),
        })
        if res['resultadoOperacion']['codigoResultado'] != 0:
            raise exceptions.ValidationError(
                _('Dachser code result: %s,'
                  'Message: %s,'
                  'Total lines processed: %s'
                  'Total lines errors: %s'
                  'Total shipments success: %s'
                  'Total shipments failed: %s') % (
                    res['resultadoOperacion']['codigoResultado'],
                    res['resultadoOperacion']['descripcionResultado'],
                    res['totalLineasProcesadas'],
                    res['totalLineasErroneas'],
                    res['totalExpedicionesCorrectas'],
                    res['totalExpedicionesRechazadas']))
        if 'La petición sigue procesandose' in (
                res['resultadoOperacion']['descripcionResultado']):
            picking.not_dachser_delivery_label = True
            return {
                'tracking_number': '',
                'exact_price': 0,
            }
        picking.carrier_tracking_ref = (
            res['expediciones']['ExpedicionWSVO'][0]['numUnico'])
        picking.dachser_expedition_code = (
            res['expediciones']['ExpedicionWSVO'][0]['numExpedicion'])
        picking.dachser_shipment_date = (
            res['expediciones']['ExpedicionWSVO'][0]['fechaExpedicion'])
        self.env['ir.attachment'].create({
            'name': 'DACHSER_%s' % picking.carrier_tracking_ref,
            'datas': res['etiquetas']['anyType'][0],
            'datas_fname': 'dachser_%s.pdf' % picking.carrier_tracking_ref,
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'mimetype': 'application/pdf',
            'description': picking.name,
        })
        picking.not_dachser_delivery_label = False
        response = {
            'tracking_number': picking.carrier_tracking_ref or '',
            'exact_price': 0,
            'dachser_expedition_code': picking.dachser_expedition_code or '',
            'dachser_shipment_date': picking.dachser_shipment_date or '',
            'dachser_token': token or '',
        }
        return response

    def dachser_create_shipping(self, picking):
        self.ensure_one()
        package_info = self._dachser_prepare_create_shipping(picking)
        picking.write({
            'dachser_last_request': fields.Datetime.now(),
        })
        res = self.dachser_send(package_info, picking)
        picking.write({
            'dachser_last_response': fields.Datetime.now(),
        })
        if res['resultadoOperacion']['codigoResultado'] != 0:
            raise exceptions.ValidationError(
                _('DACHSER result code: %s, Message: %s') % (
                    res['resultadoOperacion']['codigoResultado'],
                    res['resultadoOperacion']['descripcionResultado']))
        picking.dachser_token = res['idPeticion']
        picking.write({
            'dachser_last_request': fields.Datetime.now(),
        })
        res = self.get_dachser_label(picking, picking.dachser_token)
        picking.write({
            'dachser_last_response': fields.Datetime.now(),
        })
        return res

    def dachser_cancel_shipment(self, pickings):
        client = Client(
            url=self._get_dachser_url() + 'EliminarExpedicionWS?wsdl',
            location=self._get_dachser_url() + 'EliminarExpedicionWS',
            transport=HttpAuthenticated(headers=self._get_dachser_auth()),
        )
        arg0 = client.factory.create('ns3:DatosOperacionVO')
        for picking in pickings:
            info = client.factory.create('ns4:DatosEliminarExpedicionDTO')
            info.usuario = self.dachser_username
            info.password = self.dachser_password
            info.numUnico = picking.carrier_tracking_ref
            info.clienteEtiqueta = self.dachser_customer_label
            res = client.service.eliminarExpedicion(arg0, info)
            res = self.recursive_dict(res)
            if res['resultadoOperacion']['codigoResultado'] != 0:
                raise exceptions.ValidationError(
                    _('Dachser code result: %s, Message: %s') % (
                        res['resultadoOperacion']['codigoResultado'],
                        res['resultadoOperacion']['descripcionResultado']))
        return True

    def dachser_tracking_state_update(self, picking):
        raise NotImplementedError(_('''
            Dachser API doesn't provide methods to update state,
            so you should relay on another update state method instead or
            override this one in your custom code.
        '''))

    def dachser_get_tracking_link(self, picking):
        raise NotImplementedError(_('''
            Dachser API doesn't provide methods to update state,
            so you should relay on another update state method instead or
            override this one in your custom code.
        '''))

    def dachser_rate_shipment(self, order):
        raise NotImplementedError(_('''
            Dachser API doesn't provide methods to compute delivery
            rates, so you should relay on another price method instead or
            override this one in your custom code.
        '''))
