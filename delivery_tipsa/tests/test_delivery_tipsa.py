###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestDeliveryTipsa(common.TransactionCase):
    def setUp(self):
        super().setUp()
        product_shipping_cost = self.env['product.product'].create({
            'type': 'service',
            'name': 'Shipping costs',
            'standard_price': 10,
            'list_price': 100,
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Tipsa',
            'delivery_type': 'tipsa',
            'product_id': product_shipping_cost.id,
            'price_method': 'fixed',
            #
            # For tests, please fill next information
            #
            # 'tipsa_usercode': ,
            # 'tipsa_password': ,
            # 'tipsa_agency_code': ,
            # 'tipsa_service_code': ,
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
        country = self.env['res.partner'].browse(75)
        self.partner_int = self.env['res.partner'].create({
            'name': 'Partner international',
            'country_id': country.id,
            'street': 'Street international',
            'email': 'email@international.com',
            'city': 'Paris',
            'zip': '75001',
            'phone': 616666666,
        })

    def check_credentials(self):
        if not self.carrier.tipsa_usercode or (
                not self.carrier.tipsa_password):
            self.skipTest('Without Tipsa credentials')
        return True

    def test_api_connection(self):
        self.check_credentials()
        token_id = self.tipsa_authenticate()
        line_1 = '<soap:Envelope '
        line_2 = 'xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"'
        line_3 = 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        line_4 = 'xmlns:xsd="http://www.w3.org/2001/XMLSchema"'
        xml = """<?xml version="1.0" encoding="utf-8"?>
            %s %s
            <soap:Header>
                <ROClientIDHeader>
                <ID>{%s}</ID>
                </ROClientIDHeader>
            </soap:Header>
            <soap:Body>
                <WebServService___GrabaEnvio20>
                <strCodAgeCargo>000000</strCodAgeCargo>
                <strCodAgeOri>000000</strCodAgeOri>
                <dtFecha>2017/11/16</dtFecha>
                <strCodTipoServ>14</strCodTipoServ>
                <strCodCli>33333</strCodCli>
                <strNomOri>nombre ori</strNomOri>
                <strDirOri>calle</strDirOri>
                <strPobOri>origen pob</strPobOri>
                <strCPOri>28850</strCPOri>
                <strTlfOri>34333333</strTlfOri>
                <strNomDes>nombre des</strNomDes>
                <strDirDes>calle falsa</strDirDes>
                <strObs>observaciones</strObs>
                <strCPDes>28850</strCPDes>
                <strPobDes>poblacion destino</strPobDes>
                <strTlfDes>999887766</strTlfDes>
                <intPaq>1</intPaq>
                <strPersContacto>nombre contacto</strPersContacto>
                <boDesSMS>0</boDesSMS>
                <boDesEmail>1</boDesEmail>
                <strDesDirEmails>info@info.com</strDesDirEmails>
                <strCodPais>ES</strCodPais>
                <strContenido>contenido</strContenido>
                <boInsert>1</boInsert>
                </WebServService___GrabaEnvio20>
            </soap:Body>
            </soap:Envelope>""" % (
            line_1 + line_2,
            line_3 + line_4,
            token_id,
        )
        response = self.carrier.dhl_send(xml)
        self.assertEquals(response.status_code, 200)

    def test_tipsa_send_shipment(self):
        self.check_credentials()
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'carrier_id': self.carrier.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 10})]
        })
        self.assertEquals(len(sale.order_line), 1)
        sale.action_confirm()
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.carrier_id, self.carrier)
        picking.number_of_packages = 1
        picking.shipping_weight = 2
        picking.action_confirm()
        picking.action_assign()
        picking.send_to_shipper()
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', picking.id),
            ('res_model', '=', picking._name),
        ])
        self.assertEquals(len(attachments), 1)
        self.assertTrue(picking.carrier_tracking_ref)
