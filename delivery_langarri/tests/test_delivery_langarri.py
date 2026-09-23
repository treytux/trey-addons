###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
from types import SimpleNamespace
from unittest.mock import patch

from odoo import fields
from odoo.tests import common


class DummyResponse:

    def __init__(self, text, url):
        self.status_code = 200
        self.text = text
        self.request = SimpleNamespace(url=url, body=None)


class DeliveryLangarriCase(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref('base.main_company')
        cls.partner_dest = cls.env['res.partner'].create({
            'name': 'Destinatario Test',
            'street': 'Calle Falsa 123',
            'zip': '20001',
            'city': 'San Sebastian',
            'phone': '999999999',
            'country_id': cls.env.ref('base.es').id,
        })
        cls.picking = cls.env['stock.picking'].create({
            'partner_id': cls.partner_dest.id,
            'picking_type_id': cls.env.ref('stock.picking_type_out').id,
            'location_id': cls.env.ref('stock.stock_location_stock').id,
            'location_dest_id': cls.env.ref(
                'stock.stock_location_customers').id,
            'company_id': cls.company.id,
            'scheduled_date': fields.Datetime.now(),
        })
        cls.shipping_product = cls.env['product.product'].create({
            'name': 'Langarri Shipping',
            'type': 'service',
            'list_price': 0,
        })
        cls.carrier = cls.env['delivery.carrier'].create({
            'name': 'Langarri Test',
            'delivery_type': 'langarri',
            'product_id': cls.shipping_product.id,
            'integration_level': 'rate_and_ship',
            'prod_environment': False,
            'langarri_customer_code': 'COD',
            'langarri_username': 'USER',
            'langarri_password': 'PASS',
        })
        cls.picking.carrier_id = cls.carrier

    def _mock_requests(self):
        pdf_b64 = base64.b64encode(b'%PDF-1.4 test').decode()
        shipping_xml = (
            '<Albaran><DatosAlbaran>'
            '<Albaran>0001</Albaran>'
            '<CodigoAgenciaOrigen>D30</CodigoAgenciaOrigen>'
            '<CodigoAgenciaDestino>D10</CodigoAgenciaDestino>'
            '<Servicio>MDIA</Servicio>'
            '<CodigoBarras>CODE123</CodigoBarras>'
            '</DatosAlbaran>'
            '<CodigoBarrasBultos>'
            '<CodigoBarrasBulto>CODE123-001</CodigoBarrasBulto>'
            '</CodigoBarrasBultos>'
            '<ControlErrores />'
            '</Albaran>')
        label_xml = (
            '<order><Imagen64>%s</Imagen64><ControlErrores /></order>'
            % pdf_b64)
        responses = [
            DummyResponse(shipping_xml, 'http://test/GrabarEnvio'),
            DummyResponse(label_xml, 'http://test/EtiquetaEnvio'),
        ]

        def mock_request(method, params):
            return method, responses.pop(0)

        return mock_request

    def test_send_shipping_creates_tracking_and_label(self):
        mock_request = self._mock_requests()
        with patch.object(
                type(self.carrier), '_langarri_request',
                side_effect=mock_request):
            result = self.carrier.langarri_send_shipping(self.picking)
        self.assertEqual(result[0]['tracking_number'], 'CODE123')
        self.assertEqual(self.picking.tracking_number, '0001')
        self.assertEqual(self.picking.langarri_barcode, 'CODE123')
        self.assertEqual(
            self.picking.langarri_package_barcodes, 'CODE123-001')
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'stock.picking'),
            ('res_id', '=', self.picking.id),
            ('name', '=', 'langarri_0001.pdf'),
        ], limit=1)
        self.assertTrue(attachment)
        self.assertTrue(attachment.datas)
