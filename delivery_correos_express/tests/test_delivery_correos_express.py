###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests import common


class TestDeliveryCorreosExpress(common.TransactionCase):

    def setUp(self):
        super().setUp()
        product_shipping_cost = self.env['product.product'].create({
            'type': 'service',
            'name': 'Shipping costs',
            'standard_price': 10,
            'list_price': 100,
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Correos Express',
            'delivery_type': 'correos_express',
            'product_id': product_shipping_cost.id,
            'price_method': 'fixed',
            #
            # For tests, please fill next information
            #
            # 'correos_express_username': '',
            # 'correos_express_password': '',
            # 'correos_express_user_code': '',
            # 'correos_express_label_format': '',
            # 'correos_express_product_type': '',
            # 'correos_express_payment': '',
        })

    def test_api_connection(self):
        user = self.carrier.correos_express_username
        password = self.carrier.correos_express_password
        if not user or not password:
            self.skipTest('Without Correos Express credentials')
        response = self.carrier.correos_express_test_connection()
        self.assertTrue(response)

    def test_delivery_carrier_correos_express_price(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'delivery_price_method')])
        if module.state != 'installed':
            self.skipTest(
                'delivery_price_method not installed, ignore price test')
        product = self.env.ref('product.product_delivery_01')
        partner = self.env.ref('base.res_partner_12')
        pricelist = self.env['product.pricelist'].create({
            'name': 'Test pricelist',
            'item_ids': [(0, 0, {
                'applied_on': '1_product',
                'compute_price': 'fixed',
                'fixed_price': 100.00,
                'product_tmpl_id': product.id,
            })],
        })
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'carrier_id': self.carrier.id,
            'pricelist_id': pricelist.id,
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

    def test_delivery_carrier_correos_express_normal(self):
        user = self.carrier.correos_express_username
        password = self.carrier.correos_express_password
        if not user or not password:
            self.skipTest('Without Correos Express credentials')
        company = self.env.user.company_id
        company.country_id = self.env.ref('base.es').id
        company.partner_id.city = 'Madrid'
        company.partner_id.zip = '28001'
        product = self.env.ref('product.product_delivery_01')
        partner = self.env.ref('base.res_partner_12')
        partner.city = company.partner_id.city
        partner.zip = company.partner_id.zip
        partner.country_id = self.env.ref('base.es').id
        partner.name = 'Partner test [ñáéíóú]'
        partner.phone = 616666666
        self.carrier.correos_express_delivery_type = 'normal'
        self.carrier.correos_express_label_format = '2'
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
        picking.number_of_packages = 1
        picking.shipping_weight = 10
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
        if not self.carrier.correos_express_username:
            self.skipTest('Without Correos Express WS credentials')
        picking.tracking_state_update()
        self.assertEquals(
            picking.tracking_state_history,
            'ERROR EN BBDD - NO SE HAN ENCONTRADO DATOS')

    def test_delivery_carrier_correos_express_office(self):
        user = self.carrier.correos_express_username
        password = self.carrier.correos_express_password
        if not user or not password:
            self.skipTest('Without Correos Express credentials')
        company = self.env.user.company_id
        company.country_id = self.env.ref('base.es').id
        company.partner_id.city = 'Madrid'
        company.partner_id.zip = '28001'
        product = self.env.ref('product.product_delivery_01')
        partner = self.env.ref('base.res_partner_12')
        partner.city = company.partner_id.city
        partner.zip = company.partner_id.zip
        partner.country_id = self.env.ref('base.es').id
        partner.name = 'Partner test [ñáéíóú]'
        partner.phone = 616666666
        self.carrier.correos_express_delivery_type = 'office'
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
        picking.number_of_packages = 1
        picking.shipping_weight = 10
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
        if not self.carrier.correos_express_username:
            self.skipTest('Without Correos Express WS credentials')
        picking.tracking_state_update()
        self.assertEquals(
            picking.tracking_state_history,
            'ERROR EN BBDD - NO SE HAN ENCONTRADO DATOS')

    def test_delivery_carrier_correos_express_informed_date(self):
        user = self.carrier.correos_express_username
        password = self.carrier.correos_express_password
        if not user or not password:
            self.skipTest('Without Correos Express credentials')
        company = self.env.user.company_id
        company.country_id = self.env.ref('base.es').id
        company.partner_id.city = 'Madrid'
        company.partner_id.zip = '28001'
        product = self.env.ref('product.product_delivery_01')
        partner = self.env.ref('base.res_partner_12')
        partner.city = company.partner_id.city
        partner.zip = company.partner_id.zip
        partner.country_id = self.env.ref('base.es').id
        partner.name = 'Partner test [ñáéíóú]'
        partner.phone = 616666666
        self.carrier.correos_express_delivery_type = 'informed_date'
        self.carrier.correos_express_collection_date = fields.Date.today()
        self.carrier.correos_express_from_time = '16:00'
        self.carrier.correos_express_to_time = '18:00'
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
        picking.number_of_packages = 1
        picking.shipping_weight = 10
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
        if not self.carrier.correos_express_username:
            self.skipTest('Without Correos Express WS credentials')
        picking.tracking_state_update()
        self.assertEquals(
            picking.tracking_state_history,
            'ERROR EN BBDD - NO SE HAN ENCONTRADO DATOS')

    def test_delivery_carrier_correos_express_not_informed_date(self):
        user = self.carrier.correos_express_username
        password = self.carrier.correos_express_password
        if not user or not password:
            self.skipTest('Without Correos Express credentials')
        company = self.env.user.company_id
        company.country_id = self.env.ref('base.es').id
        company.partner_id.city = 'Madrid'
        company.partner_id.zip = '28001'
        product = self.env.ref('product.product_delivery_01')
        partner = self.env.ref('base.res_partner_12')
        partner.city = company.partner_id.city
        partner.zip = company.partner_id.zip
        partner.country_id = self.env.ref('base.es').id
        partner.name = 'Partner test [ñáéíóú]'
        partner.phone = 616666666
        self.carrier.correos_express_delivery_type = 'not_informed_date'
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
        picking.number_of_packages = 1
        picking.shipping_weight = 10
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
        if not self.carrier.correos_express_username:
            self.skipTest('Without Correos Express WS credentials')
        picking.tracking_state_update()
        self.assertEquals(
            picking.tracking_state_history,
            'ERROR EN BBDD - NO SE HAN ENCONTRADO DATOS')

    def test_delivery_carrier_correos_express_unpaid(self):
        user = self.carrier.correos_express_username
        password = self.carrier.correos_express_password
        if not user or not password:
            self.skipTest('Without Correos Express credentials')
        company = self.env.user.company_id
        company.country_id = self.env.ref('base.es').id
        company.partner_id.city = 'Madrid'
        company.partner_id.zip = '28001'
        product = self.env.ref('product.product_delivery_01')
        partner = self.env.ref('base.res_partner_12')
        partner.city = company.partner_id.city
        partner.zip = company.partner_id.zip
        partner.country_id = self.env.ref('base.es').id
        partner.name = 'Partner test [ñáéíóú]'
        partner.phone = 616666666
        self.carrier.correos_express_delivery_type = 'normal'
        self.carrier.correos_express_payment = 'D'
        self.carrier.correos_express_customer_code = '555559999'
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
        picking.number_of_packages = 1
        picking.shipping_weight = 10
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
        if not self.carrier.correos_express_username:
            self.skipTest('Without Correos Express WS credentials')
        picking.tracking_state_update()
        self.assertEquals(
            picking.tracking_state_history,
            'ERROR EN BBDD - NO SE HAN ENCONTRADO DATOS')

    def test_correos_express_check_same_number_packages_and_labels(self):
        user = self.carrier.correos_express_username
        password = self.carrier.correos_express_password
        if not user or not password:
            self.skipTest('Without Correos Express credentials')
        company = self.env.user.company_id
        company.country_id = self.env.ref('base.es').id
        company.partner_id.city = 'Madrid'
        company.partner_id.zip = '28001'
        product = self.env.ref('product.product_delivery_01')
        partner = self.env.ref('base.res_partner_12')
        partner.city = company.partner_id.city
        partner.zip = company.partner_id.zip
        partner.country_id = self.env.ref('base.es').id
        partner.phone = 616666666
        self.carrier.correos_express_delivery_type = 'normal'
        self.carrier.correos_express_label_format = '2'
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'carrier_id': self.carrier.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 4,
            })]
        })
        sale.get_delivery_price()
        sale.set_delivery_line()
        self.assertEquals(len(sale.order_line), 2)
        sale.action_confirm()
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.carrier_id, self.carrier)
        picking.number_of_packages = 4
        picking.shipping_weight = 8
        picking.action_confirm()
        picking.action_assign()
        picking.send_to_shipper()
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', picking.id),
            ('res_model', '=', picking._name),
        ])
        self.assertEquals(len(attachments), 4)
        self.assertTrue(picking.carrier_tracking_ref)
        self.assertFalse(picking.tracking_state_history)
        if not self.carrier.correos_express_username:
            self.skipTest('Without Correos Express WS credentials')
        picking.tracking_state_update()
        self.assertEquals(
            picking.tracking_state_history,
            'ERROR EN BBDD - NO SE HAN ENCONTRADO DATOS')
