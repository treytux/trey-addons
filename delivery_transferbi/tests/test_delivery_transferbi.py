# Copyright 2020 Trey, Kilobytes de Soluciones
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class TestDeliveryTransferbi(TransactionCase):

    def setUp(self):
        super().setUp()
        product_shipping_cost = self.env['product.product'].create({
            'type': 'service',
            'name': 'Shipping costs',
            'standard_price': 10,
            'list_price': 100,
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Transferbi',
            'delivery_type': 'transferbi',
            'product_id': product_shipping_cost.id,
            'price_method': 'fixed',
            #
            # For tests, please fill next information
            #
            'transferbi_username': '',
            'transferbi_password': '',
        })

    def test_soap_connection(self):
        if not self.carrier.transferbi_password:
            self.skipTest('Without Transferbi credentials')
        response = self.carrier.transferbi_test_connection()
        self.assertTrue(response)

    def test_delivery_carrier_transferbi_price(self):
        product = self.env.ref('product.product_delivery_01')
        partner = self.env.ref('base.res_partner_12')
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'carrier_id': self.carrier.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 1})]
        })
        self.carrier.write({
            'price_method': 'fixed',
            'fixed_price': 99.99,
        })
        sale.get_delivery_price()
        self.assertEquals(sale.delivery_price, 99.99)
        self.carrier.write({
            'price_method': 'fixed',
            'fixed_price': 5,
        })
        sale.get_delivery_price()
        self.assertEquals(sale.delivery_price, 5)
        self.carrier.write({
            'price_method': 'base_on_rule',
            'fixed_price': 99.99,
            'price_rule_ids': [(0, 0, {
                'variable': 'quantity',
                'operator': '==',
                'max_value': 1,
                'list_base_price': 11.11})]
        })
        sale.get_delivery_price()
        self.assertEquals(sale.delivery_price, 11.11)

    def test_delivery_carrier_transferbi_integration(self):
        if not self.carrier.transferbi_username:
            self.skipTest('Without transferbi credentials')
        company = self.env.user.company_id
        company.country_id = self.env.ref('base.es').id
        company.partner_id.city = 'Madrid'
        company.partner_id.zip = '28001'
        product = self.env.ref('product.product_delivery_01')
        partner = self.env.ref('base.res_partner_12')
        partner.city = company.partner_id.city
        partner.zip = company.partner_id.zip
        partner.country_id = self.env.ref('base.es').id
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'carrier_id': self.carrier.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 10})]
        })
        sale.get_delivery_price()
        sale.set_delivery_line()
        self.assertEquals(len(sale.order_line), 2)
        sale.action_confirm()
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.carrier_id, self.carrier)
        picking.number_of_packages = 3
        picking.name = 'PRUEBA-%s' % picking.name
        picking.action_confirm()
        picking.action_assign()
        picking.send_to_shipper()
        self.assertTrue(picking.carrier_tracking_ref)
        self.assertFalse(picking.tracking_state_history)
        codes = picking.transferbi_barcodes.split(',')
        self.assertEquals(len(codes), 3)
        picking.tracking_state_update()
        self.assertEquals(
            picking.delivery_state, 'shipping_recorded_in_carrier')
        picking.cancel_shipment()
