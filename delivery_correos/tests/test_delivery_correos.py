###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from odoo.tests import common


class TestDeliveryCorreos(common.TransactionCase):
    def setUp(self):
        super().setUp()
        product_shipping_cost = self.env['product.product'].create({
            'type': 'service',
            'name': 'Shipping costs',
            'standard_price': 10,
            'list_price': 100,
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Correos',
            'delivery_type': 'correos',
            'product_id': product_shipping_cost.id,
            'price_method': 'fixed',
            'correos_labeller_code': 'XXX1',
            'prod_environment': False,
            #
            # For tests, please fill next information
            #
            # 'correos_username': ,
            # 'correos_username_test': ,
            # 'correos_password': ,
            # 'correos_password_test': ,
        })
        self.product = self.env.ref('product.product_delivery_01')
        self.partner = self.env.ref('base.res_partner_12')
        self.partner.write({
            'name': 'Partner test',
            'country_id': self.env.ref('base.es').id,
            'city': 'Madrid',
            'zip': '28001',
            'phone': 616666666,
        })

    def check_credentials(self):
        if not self.carrier.correos_username_test or (
                not self.carrier.correos_password_test):
            self.skipTest('Without Correos credentials for test')
        return True

    def test_api_connection(self):
        self.check_credentials()
        line_1 = '<soapenv:Envelope '
        line_2 = 'xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"'
        line_3 = 'xmlns="http://www.correos.es/iris6/services/'
        line_4 = 'preregistroetiquetas">'
        data = """%s %s
            <soapenv:Header/>
            <soapenv:Body>
                <PreregistroEnvio>
                    <FechaOperacion>29-12-2022</FechaOperacion>
                    <CodEtiquetador>XXX1</CodEtiquetador>
                    <Care>000000</Care>
                    <ModDevEtiqueta>2</ModDevEtiqueta>
                    <Remitente>
                        <Identificacion>
                        <Nombre>Partner test</Nombre>
                        <Nif>.</Nif>
                        </Identificacion>
                        <DatosDireccion>
                        <Direccion>Partner street</Direccion>
                        <Numero>1</Numero>
                        <Localidad>City</Localidad>
                        <Provincia>City</Provincia>
                        </DatosDireccion>
                        <CP>18008</CP>
                        <Telefonocontacto>999887766</Telefonocontacto>
                        <Email>test@test.com</Email>
                    </Remitente>
                    <Destinatario>
                        <Identificacion>
                        <Nombre>Customer test</Nombre>
                        </Identificacion>
                        <DatosDireccion>
                        <Direccion>Customer street 1</Direccion>
                        <Localidad>Customer city</Localidad>
                        </DatosDireccion>
                        <CP></CP>
                        <Telefonocontacto>111223344</Telefonocontacto>
                        <Email>customer@test.com</Email>
                    </Destinatario>
                    <Envio>
                        <CodProducto>SOTEST</CodProducto>
                        <ReferenciaCliente>1234</ReferenciaCliente>
                        <TipoFranqueo>FP</TipoFranqueo>
                        <ModalidadEntrega>ST</ModalidadEntrega>
                        <Pesos>
                        <Peso>
                            <TipoPeso>R</TipoPeso>
                            <Valor>3</Valor>
                        </Peso>
                        </Pesos>
                        <Largo>100</Largo>
                        <Alto>10</Alto>
                        <Ancho>10</Ancho>
                    </Envio>
                </PreregistroEnvio>
            </soapenv:Body>
            </soapenv:Envelope>""" % (line_1 + line_2, line_3 + line_4)
        response = self.carrier.correos_send(data)
        self.assertEquals(response.status_code, 200)

    def test_correos_send_shipment(self):
        self.check_credentials()
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'carrier_id': self.carrier.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.assertEquals(len(sale.order_line), 1)
        sale.action_confirm()
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.carrier_id, self.carrier)
        picking.number_of_packages = 1
        picking.shipping_weight = 3
        picking.action_confirm()
        picking.action_assign()
        picking.send_to_shipper()
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', picking.id),
            ('res_model', '=', picking._name),
        ])
        self.assertEquals(len(attachments), 1)
        self.assertTrue(picking.carrier_tracking_ref)
        self.assertFalse(picking.tracking_state_history)

    def test_correos_update_shipment_check_last_response_request(self):
        self.check_credentials()
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'carrier_id': self.carrier.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.assertEquals(len(sale.order_line), 1)
        sale.action_confirm()
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.carrier_id, self.carrier)
        picking.number_of_packages = 1
        picking.shipping_weight = 3
        picking.action_confirm()
        picking.action_assign()
        picking.send_to_shipper()
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', picking.id),
            ('res_model', '=', picking._name),
        ])
        self.assertEquals(len(attachments), 1)
        self.assertTrue(picking.carrier_tracking_ref)
        self.assertFalse(picking.tracking_state_history)
        picking.tracking_state_update()
        response_time = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M')
        self.assertIn(response_time, picking.correos_last_response)

    def test_correos_update_shipment_check_last_response_request_02(self):
        self.json_response = [{
            'codEnvio': 'PQ43B404AA015110128001N',
            'numReferencia1': 'ENVIOSOB_2',
            'numReferencia2': '',
            'numReferencia3': '',
            'refCliente': 'ENVIOSOB_2',
            'codProducto': 'QD',
            'cod_tipomodif': '',
            'remit_telef': '',
            'remit_email': '',
            'remit_nombre': '',
            'remit_nom_via': '',
            'remit_cod_postal': '',
            'remit_nom_localidad': '',
            'remit_nom_provincia': '',
            'desti_telef': '',
            'desti_email': '',
            'desti_nombre': '',
            'desti_nom_via': '',
            'desti_cod_postal': '',
            'desti_nom_localidad': '',
            'desti_nom_provincia': '',
            'fec_entrega': '',
            'horas_entrega': '',
            'eur_reembolso': '',
            'eur_asegurado': '',
            'ind_avisorecibo': '',
            'num_giro': '',
            'eur_importetotal': '',
            'eur_importegirado': '',
            'ind_entregadest': '',
            'imp_declarado': '',
            'ind_ent_recogida': '',
            'indemnizacion': '',
            'eventos': [
                {
                    'fecEvento': '21/11/2018',
                    'horEvento': '14:25:44',
                    'codEvento': 'A090000V',
                    'fase': '1',
                    'color': 'V',
                    'desTextoResumen': 'Prerregistrado',
                    'desTextoAmpliado': 'Envío prerregistrado en el sistema',
                    'accionWeb': '',
                    'paramAccionWeb': '',
                    'codired': '',
                    'unidad': 'NO_OFI',
                },
            ],
            'enviosAsociados': [{
                'codEnvio': 'DQ43B404AA015110128042M',
                'fecEvento': '27/11/2018',
                'horEvento': '13:29:21',
                'codEvento': 'I010000V',
                'desResumen': 'Entregado',
                'desAmpliada': 'Envío entregado al destinatario o autorizado'
            }],
            'error': {
                'codError': '0',
                'desError': '',
            },
            'largo': '13',
            'alto': '30',
            'ancho': '24',
            'peso': '2820',
            'fec_entregasum': '',
            'fec_caducidad': '28/11/2018 00:00',
            'fec_calculada': '26/11/2018 00:00',
            'fec_a_mostrar': '',
            'telefono_D_notif': '',
            'email_D_notif': '',
            'telefono_R_notif': '',
            'email_R_notif': '',
            'cod_oficinaorigen': '',
            'cod_oficinadestino': '',
            'cod_categoria': '',
            'cod_despacho': '',
            'fec_despacho': '',
            'num_lista': '',
            'num_orden': '',
        }]
        tracking_state = self.carrier.update_state(self.json_response)
        self.assertEquals(tracking_state, '%s-%s-%s-%s' % (
            self.json_response[0]['eventos'][0]['fecEvento'],
            self.json_response[0]['eventos'][0]['horEvento'],
            self.json_response[0]['eventos'][0]['desTextoResumen'],
            self.json_response[0]['eventos'][0]['desTextoAmpliado']))
        self.json_response[0].update({
            'eventos': [],
            'enviosAsociados': [],
            'error': {
                'codError': '401',
                'desError': 'Bad request',
            }
        })
        tracking_state = self.carrier.update_state(self.json_response)
        self.assertEquals(tracking_state, 'Error code: %s, Error: %s' % (
            self.json_response[0]['error']['codError'],
            self.json_response[0]['error']['desError']))
