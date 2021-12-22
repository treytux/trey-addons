###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from odoo.tests import common


class TestDeliveryDHL(common.TransactionCase):
    def setUp(self):
        super().setUp()
        product_shipping_cost = self.env['product.product'].create({
            'type': 'service',
            'name': 'Shipping costs',
            'standard_price': 10,
            'list_price': 100,
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'DHL',
            'delivery_type': 'dhl',
            'product_id': product_shipping_cost.id,
            'price_method': 'fixed',
            #
            # For tests, please fill next information
            #
            # 'dhl_user_code': '',
            # 'dhl_username': '',
            # 'dhl_password': '',
        })
        self.product = self.env.ref('product.product_delivery_01')
        self.partner = self.env.ref('base.res_partner_12')
        self.partner.write({
            'name': 'Partner test [ñáéíóú]',
            'country_id': self.env.ref('base.es').id,
            'city': 'Madrid',
            'zip': '28001',
            'phone': 616666666,
        })

    def check_credentials(self):
        if not self.carrier.dhl_username or not self.carrier.dhl_password:
            self.skipTest('Without DHL credentials')
        return True

    def test_api_connection(self):
        self.check_credentials()
        data = {
            'Customer': self.carrier.dhl_user_code,
            'Receiver': {
                'Name': 'DHL Parcel Madrid',
                'Address': 'Río Almanzora, s/n',
                'City': 'Getafe',
                'PostalCode': '28906',
                'Country': 'ES',
                'Phone': '34914237100',
                'Email': 'test@dhl.com',
            },
            'Sender': {
                'Name': 'Test Company',
                'Address': 'Calle de Núñez de Balboa, 19',
                'City': 'Madrid',
                'PostalCode': '28046',
                'Country': 'ES',
                'Phone': '34914237100',
                'Email': 'test@dhl.com',
            },
            'Reference': 'ALB123456',
            'Quantity': 3,
            'Weight': 5,
            'WeightVolume': '',
            'CODAmount': '',
            'CODExpenses': 'P',
            'CODCurrency': 'EUR',
            'InsuranceAmount': '',
            'InsuranceExpenses': 'P',
            'DeliveryNote': '',
            'Remarks1': '',
            'Remarks2': '',
            'Incoterms': 'CPT',
            'ContactName': '',
            'GoodsDescription': '',
            'CustomsValue': '',
            'CustomsCurrency': '',
            'PayerAccount': '',
            'Features': '',
            'Format': 'PDF',
        }
        response = self.carrier.dhl_send(data)
        self.assertEquals(response.status_code, 200)

    def test_dhl_update_shipment(self):
        self.check_credentials()
        self.carrier.dhl_label_format = 'PDF'
        self.carrier.dhl_payment = 'CPT'
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
        self.assertFalse(picking.tracking_state_history)
        picking.tracking_state_update()
        response_time = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M')
        self.assertIn(response_time, picking.dhl_last_response)

    def test_dhl_cancel_shipment(self):
        self.check_credentials()
        self.carrier.dhl_label_format = 'PDF'
        self.carrier.dhl_payment = 'CPT'
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
        self.assertFalse(picking.tracking_state_history)
        self.assertTrue(self.carrier.dhl_cancel_shipment(picking))

    def test_delivery_carrier_dhl_paid(self):
        self.check_credentials()
        self.carrier.dhl_label_format = 'PDF'
        self.carrier.dhl_payment = 'CPT'
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
        self.assertFalse(picking.tracking_state_history)

    def test_delivery_carrier_dhl_unpaid(self):
        self.check_credentials()
        self.carrier.dhl_label_format = 'PDF'
        self.carrier.dhl_payment = 'EXW'
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
        self.assertFalse(picking.tracking_state_history)

    def test_delivery_carrier_dhl_zpl(self):
        self.check_credentials()
        self.carrier.dhl_label_format = 'ZPL'
        self.carrier.dhl_payment = 'CPT'
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
        self.assertFalse(picking.tracking_state_history)

    def test_delivery_carrier_dhl_epl(self):
        self.check_credentials()
        self.carrier.dhl_label_format = 'EPL'
        self.carrier.dhl_payment = 'CPT'
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
        self.assertFalse(picking.tracking_state_history)
