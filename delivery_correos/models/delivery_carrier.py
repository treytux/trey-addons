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
    correos_product_code = fields.Char(
        string='Product code',
    )

    def correos_send(self, data, soap_action):
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
            'SOAPAction': soap_action,
        }
        res = requests.post(url, headers=headers, data=data)
        return res

    def correos_send_shipping(self, pickings):
        return [self.correos_create_shipping(p) for p in pickings]

    def correos_normalize_text(self, text):
        text = text.replace('&', '&amp;')
        return text and normalize(
            "NFKD", text).encode("ascii", "ignore").decode("ascii") or None

    def correos_get_sender_address(self, picking):
        warehouse = picking.location_id.get_warehouse()
        if not warehouse:
            return picking.company_id.partner_id
        return warehouse.partner_id if warehouse.partner_id else (
            picking.company_id.partner_id)

    def convert_to_cm(self, product_id):
        uom_cm = self.env.ref('uom.product_uom_cm')
        length = product_id.product_length
        height = product_id.product_height
        width = product_id.product_width
        dimensional_uom_id = product_id.dimensional_uom_id
        if dimensional_uom_id != uom_cm:
            length = dimensional_uom_id._compute_quantity(
                qty=length, to_unit=uom_cm, round=False)
            height = dimensional_uom_id._compute_quantity(
                qty=height, to_unit=uom_cm, round=False)
            width = dimensional_uom_id._compute_quantity(
                qty=width, to_unit=uom_cm, round=False)
        return length, height, width

    def correos_prepare_multiple_packages_shipping(self, picking):
        def fix_dimension(dims, value_min, count):
            dims_ok = [d for d in dims if d >= value_min]
            if len(dims_ok) >= count:
                return
            count -= len(dims_ok)
            for dim in [d for d in dims if d < value_min]:
                if dim <= value_min:
                    dims[dims.index(dim)] = value_min
                    count -= 1
                if count == 0:
                    break
            return

        picking_lines = len(picking.move_lines)
        dimension_list = []
        for line in picking.move_lines:
            dims = list(self.convert_to_cm(line.product_id))
            fix_dimension(dims, 15, 1)
            fix_dimension(dims, 10, 2)
            dimension_list.append(dims)
        phone = picking.partner_id.phone if picking.partner_id.phone else (
            picking.partner_id.mobile if picking.partner_id.mobile else '000')
        if phone.startswith('+'):
            phone = phone[3:]
        phone = ''.join([c for c in phone if c in '0123456789'])
        sender_address = self.correos_get_sender_address(picking)
        shipping_weight = (
            picking.shipping_weight
            and picking.weight_uom_id._compute_quantity(
                picking.shipping_weight, self.env.ref('uom.product_uom_gram'))
            or 200)
        street2 = picking.partner_id.street2 if (
            picking.partner_id.street2) else ''
        picking_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        line_1 = '<soap:Envelope '
        line_2 = 'xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
        line_3 = 'xmlns="http://www.correos.es/iris6/services/'
        line_4 = 'preregistroetiquetas"'
        partner_address = ' '.join([
            s for s in [picking.partner_id.street, picking.partner_id.street2]
            if s
        ])
        packages = []
        product_code = '<CodProducto>%s</CodProducto>' % (
            self.correos_product_code) if (
                picking.number_of_packages == 1) else ''
        postage_type = '<TipoFranqueo>FP</TipoFranqueo>' if (
            picking.number_of_packages == 1) else ''
        delivery_type = '<ModalidadEntrega>ST</ModalidadEntrega>' if (
            picking.number_of_packages == 1) else ''
        total_packages = picking.number_of_packages
        for package in range(picking.number_of_packages):
            dim = (
                dimension_list[package]
                if package < picking_lines else dimension_list[0])
            packages.append(f"""<Envio>
                {product_code}
                {postage_type}
                {delivery_type}
                <NumBulto>{package + 1}</NumBulto>
                <ReferenciaCliente>{picking.name}</ReferenciaCliente>
                <Pesos>
                    <Peso>
                        <TipoPeso>R</TipoPeso>
                        <Valor>{int(shipping_weight / total_packages)}</Valor>
                    </Peso>
                </Pesos>
                <Largo>{int(dim[0])}</Largo>
                <Alto>{int(dim[1])}</Alto>
                <Ancho>{int(dim[2])}</Ancho>
            </Envio>""")
        label = 'PreregistroEnvioMultibulto' if (
            picking.number_of_packages > 1) else 'PreregistroEnvio'
        xml = """%s
            <soap:Body>
                <%s %s%s>
                    <FechaOperacion>%s</FechaOperacion>
                    <CodEtiquetador>%s</CodEtiquetador>
                    <Care>000000</Care>
                    <TotalBultos>%s</TotalBultos>
                    <ModDevEtiqueta>2</ModDevEtiqueta>
                    %s
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
                    %s%s%s
                    %s
                    %s
                    %s
                </%s>
            </soap:Body>
            </soap:Envelope>""" % (
            line_1 + line_2,
            label,
            line_3,
            line_4,
            picking_date,
            self.correos_labeller_code,
            picking.number_of_packages,
            '<NotificacionBulto>N</NotificacionBulto>' if (
                picking.number_of_packages > 1) else '',
            sender_address.display_name,
            sender_address.street,
            street2,
            sender_address.city,
            sender_address.city,
            sender_address.zip,
            sender_address.phone,
            sender_address.email,
            picking.partner_id.name,
            partner_address,
            picking.partner_id.city,
            picking.partner_id.zip,
            phone,
            picking.partner_id.email,
            '<Envios>\n' if picking.number_of_packages > 1 else '',
            '\n'.join(packages),
            '</Envios>' if picking.number_of_packages > 1 else '',
            '<CodProducto>%s</CodProducto>' % self.correos_product_code if (
                picking.number_of_packages > 1) else '',
            '<TipoFranqueo>FP</TipoFranqueo>' if (
                picking.number_of_packages > 1) else '',
            '<ModalidadEntrega>ST</ModalidadEntrega>' if (
                picking.number_of_packages > 1) else '',
            label,
        )
        return self.correos_normalize_text(xml)

    def _correos_prepare_create_shipping(self, picking):
        self.ensure_one()
        return self.correos_prepare_multiple_packages_shipping(picking)

    def _zebra_label_custom(self, label):
        return label

    def correos_create_shipping(self, picking):
        self.ensure_one()
        package_info = self._correos_prepare_create_shipping(picking)
        picking.write({
            'correos_last_request': fields.Datetime.now(),
        })
        if picking.number_of_packages > 1:
            soap_action = 'PreRegistroMultibulto'
        else:
            soap_action = 'PreRegistro'
        response = self.correos_send(package_info, soap_action)
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
        picking.correos_last_response = fields.Datetime.now()
        if picking.number_of_packages > 1:
            picking.carrier_tracking_ref = root.find('.//CodExpedicion').text
            count = 1
            for label in root.findall('.//Fichero'):
                self.env['ir.attachment'].create({
                    'name': 'Correos %s %s' % (
                        picking.carrier_tracking_ref, count),
                    'datas': label.text,
                    'datas_fname': 'correos_%s' % picking.carrier_tracking_ref,
                    'res_model': 'stock.picking',
                    'res_id': picking.id,
                    'mimetype': 'application/pdf',
                })
                count += 1
        else:
            picking.carrier_tracking_ref = root.find('.//CodEnvio').text
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

    def correos_cancel_shipment(self, pickings):
        line_1 = '<soapenv:Envelope '
        line_2 = 'xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
        line_3 = 'xmlns:prer="http://www.correos.es/iris6/services/'
        line_4 = 'preregistroetiquetas">'
        line_5 = 'xmlns="http://www.correos.es/iris6/services/'
        line_6 = 'preregistroetiquetas"'
        for picking in pickings:
            xml = """%s
                <soapenv:Header/>
                <soapenv:Body>
                    <PeticionAnular %s>
                        <IdiomaErrores>EN</IdiomaErrores>
                        <codCertificado>%s</codCertificado>
                    </PeticionAnular>
                </soapenv:Body>
                </soapenv:Envelope>""" % (
                line_1 + line_2 + line_3 + line_4,
                line_5 + line_6,
                picking.carrier_tracking_ref,
            )
            data = self.correos_normalize_text(xml)
            response = self.correos_send(data, 'AnularOp')
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
        return True

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
