###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from io import StringIO
from unicodedata import normalize

import requests
from odoo import _, exceptions, fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(
        selection_add=[('correos', 'Correos')],
    )
    correos_username = fields.Char(
        string='User',
        help='Usernane for Correos webservice',
    )
    correos_password = fields.Char(
        string='Password',
        help='Password for Correos webservice',
    )
    correos_username_test = fields.Char(
        string='Username test',
        help='Username for test environment',
    )
    correos_password_test = fields.Char(
        string='Password test',
        help='Password for test environment',
    )
    correos_labeller_code = fields.Char(
        string='Labeller code',
    )

    def correos_send(self, data):
        if self.prod_environment:
            url = 'https://preregistroenvios.correos.es/preregistroenvios'
            credentials = self.correos_username + ':' + self.correos_password
        else:
            url = ('https://preregistroenviospre.correos.es/preregistroenvios')
            credentials = (
                self.correos_username_test + ':' + self.correos_password_test)
        credentials = credentials.encode()
        credentials_encode = base64.b64encode(credentials)
        headers = {
            'Content-type': 'text/xml;charset=utf-8',
            'Content-Lenght': str(len(data)),
            'Authorization': 'Basic {}'.format(credentials_encode.decode()),
            'SOAPAction': 'PreRegistro',
        }
        res = requests.post(url, headers=headers, data=data)
        return res

    def correos_send_shipping(self, pickings):
        return [self.correos_create_shipping(p) for p in pickings]

    def correos_normalize_text(self, text):
        text = text.replace('&', '&amp;')
        return text and normalize(
            "NFKD", text).encode("ascii", "ignore").decode("ascii") or None

    def _correos_prepare_create_shipping(self, picking):
        self.ensure_one()
        phone = picking.partner_id.phone if picking.partner_id.phone else (
            picking.partner_id.mobile if picking.partner_id.mobile else '000')
        shipping_weight = (
            picking.shipping_weight
            and picking.weight_uom_id._compute_quantity(
                picking.shipping_weight, self.env.ref('uom.product_uom_gram'))
            or 200)
        street2 = picking.partner_id.street2 if (
            picking.partner_id.street2) else ''
        picking_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        line_1 = '<soapenv:Envelope '
        line_2 = 'xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"'
        line_3 = 'xmlns="http://www.correos.es/iris6/services/'
        line_4 = 'preregistroetiquetas">'
        partner_address = ' '.join([
            s for s in [picking.partner_id.street, picking.partner_id.street2]
            if s
        ])
        xml = """%s %s
            <soapenv:Header/>
            <soapenv:Body>
                <PreregistroEnvio>
                    <FechaOperacion>%s</FechaOperacion>
                    <CodEtiquetador>%s</CodEtiquetador>
                    <Care>000000</Care>
                    <ModDevEtiqueta>2</ModDevEtiqueta>
                    <Remitente>
                        <Identificacion>
                        <Nombre>%s</Nombre>
                        <Nif>.</Nif>
                        </Identificacion>
                        <DatosDireccion>
                        <Direccion>%s</Direccion>
                        <Numero>%s</Numero>
                        <Localidad>%s</Localidad>
                        <Provincia>%s</Provincia>
                        </DatosDireccion>
                        <CP>%s</CP>
                        <Telefonocontacto>%s</Telefonocontacto>
                        <Email>%s</Email>
                    </Remitente>
                    <Destinatario>
                        <Identificacion>
                        <Nombre>%s</Nombre>
                        </Identificacion>
                        <DatosDireccion>
                        <Direccion>%s</Direccion>
                        <Localidad>%s</Localidad>
                        </DatosDireccion>
                        <CP>%s</CP>
                        <Telefonocontacto>%s</Telefonocontacto>
                        <Email>%s</Email>
                    </Destinatario>
                    <Envio>
                        <CodProducto>S0132</CodProducto>
                        <ReferenciaCliente>%s</ReferenciaCliente>
                        <TipoFranqueo>FP</TipoFranqueo>
                        <ModalidadEntrega>ST</ModalidadEntrega>
                        <Pesos>
                        <Peso>
                            <TipoPeso>R</TipoPeso>
                            <Valor>%s</Valor>
                        </Peso>
                        </Pesos>
                        <Largo>100</Largo>
                        <Alto>10</Alto>
                        <Ancho>10</Ancho>
                    </Envio>
                </PreregistroEnvio>
            </soapenv:Body>
            </soapenv:Envelope>""" % (
            line_1 + line_2,
            line_3 + line_4,
            picking_date,
            self.correos_labeller_code,
            picking.company_id.display_name,
            picking.company_id.street,
            street2,
            picking.company_id.city,
            picking.company_id.city,
            picking.company_id.zip,
            picking.company_id.phone,
            picking.company_id.email,
            picking.partner_id.name,
            partner_address,
            picking.partner_id.city,
            picking.partner_id.zip,
            phone,
            picking.partner_id.email,
            picking.name,
            int(shipping_weight),
        )
        return self.correos_normalize_text(xml)

    def _zebra_label_custom(self, label):
        return label

    def correos_create_shipping(self, picking):
        self.ensure_one()
        package_info = self._correos_prepare_create_shipping(picking)
        picking.write({
            'correos_last_request': fields.Datetime.now(),
        })
        response = self.correos_send(package_info)
        it = ET.iterparse(StringIO(response.text))
        for _index, el in it:
            prefix, has_namespace, postfix = el.tag.partition('}')
            if has_namespace:
                el.tag = postfix
        root = it.root
        errors = (
            root.findall('.//faultstring')
            or root.findall('.//DescError') or [])
        if errors:
            raise exceptions.UserError(_('Correos error: %s') % (
                ', '.join(error.text for error in errors)))
        picking.write({
            'correos_last_response': fields.Datetime.now(),
            'carrier_tracking_ref': root.find('.//CodEnvio').text,
        })
        self.env['ir.attachment'].create({
            'name': 'Correos %s' % picking.carrier_tracking_ref,
            'datas': root.find('.//Fichero').text,
            'datas_fname': 'correos_%s' % picking.carrier_tracking_ref,
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'mimetype': 'application/pdf',
        })
        return {
            'tracking_number': picking.carrier_tracking_ref,
            'exact_price': 0,
        }

    def update_state(self, data):
        if data[0]['error']['codError'] != '0':
            return _('Error code: %s, Error: %s') % (
                data[0]['error']['codError'], data[0]['error']['desError'])
        return '%s-%s-%s-%s' % (
            data[0]['eventos'][0]['fecEvento'],
            data[0]['eventos'][0]['horEvento'],
            data[0]['eventos'][0]['desTextoResumen'],
            data[0]['eventos'][0]['desTextoAmpliado'])

    def correos_tracking_state_update(self, picking):
        self.ensure_one()
        if not self.correos_username or not self.correos_password:
            picking.tracking_state_history = _(
                'Status cannot be checked, enter webservice carrier '
                'credentiasl')
            return
        credentials = self.correos_username + ':' + self.correos_password
        credentials = credentials.encode()
        credentials_encode = base64.b64encode(credentials)
        headers = {
            'Authorization': 'Basic {}'.format(credentials_encode.decode()),
            'Accept': 'application/json',
        }
        url = (
            'https://localizador.correos.es/canonico/'
            'eventos_envio_servicio_auth/%s?codIdioma=ES&indUltEvento=S' % (
                picking.carrier_tracking_ref))
        res = requests.get(url, headers=headers)
        response = json.loads(res.content)
        tracking_state = self.update_state(response)
        picking.tracking_state_history = tracking_state

    def correos_cancel_shipment(self, picking):
        raise NotImplementedError(_('''
            Correos API doesn't provide methods to cancel shipment'''))

    def correos_get_tracking_link(self, picking):
        return (
            'http://www.correos.es/comun/localizador/track.asp?numero=%s' % (
                picking.carrier_tracking_ref)
        )

    def correos_rate_shipment(self, order):
        raise NotImplementedError(_('''
            Correos API doesn't provide methods to compute delivery
            rates, so you should relay on another price method instead or
            override this one in your custom code.
        '''))
