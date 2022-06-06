###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
from datetime import timedelta

from odoo import fields
from odoo.tests import common


class TestDeliveryDachser(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
            'street': 'Street Test 1',
            'city': 'City test',
            'zip': '28001',
            'phone': 616666666,
            'email': 'partner@test.com',
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Tets product',
            'standard_price': 3,
            'list_price': 20,
        })
        self.location = self.env.ref('stock.stock_location_stock')
        self.inventory = self.env['stock.inventory'].create({
            'name': 'Add products for tests',
            'filter': 'partial',
            'location_id': self.location.id,
            'exhausted': True,
        })
        self.inventory.action_start()
        self.inventory.line_ids.create({
            'inventory_id': self.inventory.id,
            'product_id': self.product.id,
            'product_qty': 10,
            'location_id': self.location.id,
        })
        self.inventory._action_done()
        self.country = self.env.ref('base.es')
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 8,
                }),
            ],
        })
        self.product_shipping_cost = self.env['product.product'].create({
            'type': 'service',
            'name': 'Product shipping costs',
            'standard_price': 10,
            'list_price': 20,
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Dachser',
            'delivery_type': 'dachser',
            'product_id': self.product_shipping_cost.id,
            'price_method': 'fixed',
            #
            # For tests, please fill next information
            #
            # 'dachser_username': ,
            # 'dachser_password': ,
            # 'dachser_customer_code': ,
            # 'dachser_customer_label': ,
        })

    def test_create_dachser_file_picking_default_information(self):
        self.assertEquals(self.sale.state, 'draft')
        self.assertEquals(len(self.sale.order_line), 1)
        self.assertFalse(self.sale.carrier_id)
        self.sale.carrier_id = self.carrier.id
        self.assertEquals(self.sale.carrier_id, self.carrier)
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEquals(len(self.sale.picking_ids), 1)
        self.assertEquals(len(picking.move_lines), 1)
        picking.write({
            'number_of_packages': 1,
            'shipping_weight': 1,
            'volume': 32,
        })
        params = {
            'id': picking.id,
        }
        sender_code = '430529999'
        wizard = self.env['delivery.dachser'].with_context(
            active_ids=picking.ids, params=params).create({
                'picking_id': picking.id,
                'dachser_sender_code': sender_code,
                'dachser_postponed_delivery_date': (
                    fields.Date.today() + timedelta(days=7)),
                'dachser_country_code': self.country.id,
            })
        self.assertEquals(wizard.picking_id, picking)
        self.assertEquals(wizard.dachser_sender_code, sender_code)
        self.assertEquals(
            wizard.dachser_postponed_delivery_date,
            fields.Date.today() + timedelta(days=7))
        self.assertEquals(wizard.dachser_product, '001')
        self.assertFalse(wizard.dachser_arrange_delivery)
        self.assertFalse(wizard.dachser_lifting_platform)
        self.assertEquals(wizard.dachser_country_code.code, 'ES')
        wizard.action_create_dachser_file()
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', picking.id),
            ('res_model', '=', picking._name),
        ])
        self.assertEquals(len(attachments), 1)
        self.assertEquals(attachments[0].name, 'DACHSER_%s' % picking.name)
        self.assertEquals(attachments[0].mimetype, 'application/csv')
        file_content = base64.b64decode(attachments[0].datas)
        file_content = file_content.decode('utf-8')
        self.assertIn('TRS|', file_content)
        self.assertIn(picking.partner_id.street.upper(), file_content)
        self.assertIn(picking.partner_id.city.upper(), file_content)
        self.assertIn(picking.partner_id.zip, file_content)
        self.assertIn(wizard.dachser_sender_code, file_content)
        self.assertIn(wizard.dachser_country_code.code, file_content)
        self.assertIn(str(picking.number_of_packages), file_content)
        self.assertIn(str(picking.shipping_weight), file_content)
        self.assertIn(str(picking.volume), file_content)
        self.assertIn('P|00000.00|P|00000.00|', file_content)
        self.assertIn(wizard.dachser_product, file_content)
        self.assertIn(
            wizard.dachser_postponed_delivery_date.strftime('%Y%m%d'),
            file_content)
        self.assertIn(picking.partner_id.phone, file_content)
        self.assertIn(picking.partner_id.email, file_content)
        self.assertIn('N|N|', file_content)

    def test_create_dachser_file_change_product(self):
        self.assertEquals(self.sale.state, 'draft')
        self.assertEquals(len(self.sale.order_line), 1)
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEquals(len(self.sale.picking_ids), 1)
        self.assertEquals(len(picking.move_lines), 1)
        picking.write({
            'number_of_packages': 1,
            'shipping_weight': 1,
            'volume': 32,
        })
        wizard = self.env['delivery.dachser'].create({
            'picking_id': picking.id,
            'dachser_sender_code': '430529999',
            'dachser_postponed_delivery_date': (
                fields.Date.today() + timedelta(days=7)),
            'dachser_country_code': self.country.id,
            'dachser_product': '002',
        })
        wizard.action_create_dachser_file()
        self.assertEquals(wizard.picking_id, picking)
        self.assertEquals(wizard.dachser_product, '002')
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', picking.id),
            ('res_model', '=', picking._name),
        ])
        self.assertEquals(len(attachments), 1)
        self.assertEquals(attachments[0].name, 'DACHSER_%s' % picking.name)
        self.assertEquals(attachments[0].mimetype, 'application/csv')
        file_content = base64.b64decode(attachments[0].datas)
        file_content = file_content.decode('utf-8')
        self.assertIn('|002|', file_content)

    def test_create_file_activate_arrange_delivery_and_lifting_platform(self):
        self.assertEquals(self.sale.state, 'draft')
        self.assertEquals(len(self.sale.order_line), 1)
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEquals(len(self.sale.picking_ids), 1)
        self.assertEquals(len(picking.move_lines), 1)
        picking.write({
            'number_of_packages': 1,
            'shipping_weight': 1,
            'volume': 32,
        })
        wizard = self.env['delivery.dachser'].create({
            'picking_id': picking.id,
            'dachser_sender_code': '430529999',
            'dachser_postponed_delivery_date': (
                fields.Date.today() + timedelta(days=7)),
            'dachser_country_code': self.country.id,
            'dachser_arrange_delivery': True,
            'dachser_lifting_platform': True,
        })
        wizard.action_create_dachser_file()
        self.assertEquals(wizard.picking_id, picking)
        self.assertTrue(wizard.dachser_arrange_delivery)
        self.assertTrue(wizard.dachser_lifting_platform)
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', picking.id),
            ('res_model', '=', picking._name),
        ])
        self.assertEquals(len(attachments), 1)
        self.assertEquals(attachments[0].name, 'DACHSER_%s' % picking.name)
        self.assertEquals(attachments[0].mimetype, 'application/csv')
        file_content = base64.b64decode(attachments[0].datas)
        file_content = file_content.decode('utf-8')
        self.assertIn('|S|S|', file_content)

    def test_create_file_add_delivery_note_picking(self):
        self.assertEquals(self.sale.state, 'draft')
        self.assertEquals(len(self.sale.order_line), 1)
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEquals(len(self.sale.picking_ids), 1)
        self.assertEquals(len(picking.move_lines), 1)
        picking.write({
            'number_of_packages': 1,
            'shipping_weight': 2,
            'volume': 3,
            'delivery_note': 'Test example delivery note',
        })
        self.assertEquals(picking.delivery_note, 'Test example delivery note')
        wizard = self.env['delivery.dachser'].create({
            'picking_id': picking.id,
            'dachser_sender_code': '430529999',
            'dachser_postponed_delivery_date': (
                fields.Date.today() + timedelta(days=7)),
            'dachser_country_code': self.country.id,
        })
        wizard.action_create_dachser_file()
        self.assertEquals(wizard.picking_id, picking)
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', picking.id),
            ('res_model', '=', picking._name),
        ])
        self.assertEquals(len(attachments), 1)
        self.assertEquals(attachments[0].name, 'DACHSER_%s' % picking.name)
        self.assertEquals(
            attachments[0].datas_fname, 'dachser_%s.csv' % picking.name)
        self.assertEquals(attachments[0].mimetype, 'application/csv')
        file_content = base64.b64decode(attachments[0].datas)
        file_content = file_content.decode('utf-8')
        self.assertIn('Test example delivery note', file_content)

    def check_carrier_credentials(self):
        if not self.carrier.dachser_username or (
                not self.carrier.dachser_password):
            self.skipTest('Without Dachser credentials')

    def test_dachser_send_shipment_and_get_label(self):
        self.check_carrier_credentials()
        self.assertFalse(self.sale.carrier_id)
        self.assertEquals(len(self.sale.order_line), 1)
        self.sale.carrier_id = self.carrier.id
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.carrier_id, self.carrier)
        picking.write({
            'number_of_packages': 1,
            'shipping_weight': 2,
            'volume': 3,
            'delivery_note': 'Test example delivery note',
        })
        self.assertEquals(picking.delivery_note, 'Test example delivery note')
        wizard = self.env['delivery.dachser'].create({
            'picking_id': picking.id,
            'dachser_sender_code': self.carrier.dachser_customer_code,
            'dachser_postponed_delivery_date': (
                fields.Date.today() + timedelta(days=7)),
            'dachser_country_code': self.country.id,
        })
        wizard.action_create_dachser_file()
        self.assertEquals(wizard.picking_id, picking)
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', picking.id),
            ('res_model', '=', picking._name),
        ])
        self.assertEquals(len(attachments), 1)
        self.assertEquals(attachments[0].name, 'DACHSER_%s' % picking.name)
        self.assertEquals(
            attachments[0].datas_fname, 'dachser_%s.csv' % picking.name)
        self.assertEquals(attachments[0].mimetype, 'application/csv')
        picking.action_confirm()
        picking.action_assign()
        picking.send_to_shipper()
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', picking.id),
            ('res_model', '=', picking._name),
        ])
        self.assertEquals(len(attachments), 2)
        self.assertTrue(picking.carrier_tracking_ref)

    def test_dachser_cancel_shipment(self):
        self.check_carrier_credentials()
        self.assertFalse(self.sale.carrier_id)
        self.assertEquals(len(self.sale.order_line), 1)
        self.sale.carrier_id = self.carrier.id
        self.assertEquals(self.sale.carrier_id, self.carrier)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 1)
        picking.write({
            'number_of_packages': 1,
            'shipping_weight': 2,
            'volume': 3,
            'delivery_note': 'Test example delivery note',
        })
        wizard = self.env['delivery.dachser'].create({
            'picking_id': picking.id,
            'dachser_sender_code': self.carrier.dachser_customer_code,
            'dachser_postponed_delivery_date': (
                fields.Date.today() + timedelta(days=7)),
            'dachser_country_code': self.country.id,
        })
        wizard.action_create_dachser()
        self.assertEquals(wizard.picking_id, picking)
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', picking.id),
            ('res_model', '=', picking._name),
        ])
        self.assertEquals(len(attachments), 1)
        self.assertEquals(attachments[0].name, 'DACHSER_%s' % picking.name)
        self.assertEquals(
            attachments[0].datas_fname, 'dachser_%s.csv' % picking.name)
        self.assertEquals(attachments[0].mimetype, 'application/csv')
        picking.action_confirm()
        picking.action_assign()
        picking.send_to_shipper()
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', picking.id),
            ('res_model', '=', picking._name),
        ])
        self.assertEquals(len(attachments), 2)
        self.assertEquals(picking.carrier_tracking_ref)
        self.assertTrue(self.carrier.dachser_cancel_shipment(picking))

    def test_dachser_button_get_label(self):
        self.check_carrier_credentials()
        self.assertFalse(self.sale.carrier_id)
        self.assertEquals(len(self.sale.order_line), 1)
        self.sale.carrier_id = self.carrier.id
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.carrier_id, self.carrier)
        picking.write({
            'number_of_packages': 1,
            'shipping_weight': 2,
            'volume': 3,
            'delivery_note': 'Test example delivery note',
        })
        wizard = self.env['delivery.dachser'].create({
            'picking_id': picking.id,
            'dachser_sender_code': self.carrier.dachser_customer_code,
            'dachser_postponed_delivery_date': (
                fields.Date.today() + timedelta(days=7)),
            'dachser_country_code': self.country.id,
        })
        wizard.action_create_dachser_file()
        self.assertEquals(wizard.picking_id, picking)
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', picking.id),
            ('res_model', '=', picking._name),
        ])
        self.assertEquals(len(attachments), 1)
        self.assertEquals(attachments[0].mimetype, 'application/csv')
        self.assertEquals(attachments[0].name, 'DACHSER_%s' % picking.name)
        self.assertEquals(
            attachments[0].datas_fname, 'dachser_%s.csv' % picking.name)
        picking.action_confirm()
        picking.action_assign()
        picking.send_to_shipper()
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', picking.id),
            ('res_model', '=', picking._name),
        ])
        self.assertEquals(len(attachments), 2)
        self.assertTrue(picking.carrier_tracking_ref)
        picking.action_get_dachser_label()
        self.assertEquals(len(attachments), 3)

    def test_check_autocomplete_dachser_config_parameter(self):
        self.assertEquals(self.sale.state, 'draft')
        self.assertEquals(len(self.sale.order_line), 1)
        self.assertFalse(self.sale.carrier_id)
        self.sale.carrier_id = self.carrier.id
        self.assertEquals(self.sale.carrier_id, self.carrier)
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 1)
        picking.write({
            'number_of_packages': 1,
            'shipping_weight': 1,
            'volume': 32,
        })
        self.assertFalse(self.carrier.dachser_customer_code)
        self.assertFalse(self.carrier.dachser_customer_label)
        self.assertFalse(self.carrier.dachser_username)
        self.assertFalse(self.carrier.dachser_password)
        self.assertEquals(self.carrier.dachser_delivery_product, '001')
        self.carrier.write({
            'dachser_password': 'password',
            'dachser_username': 'user',
            'dachser_customer_code': '430529999',
            'dachser_customer_label': 'Label',
        })
        self.assertTrue(self.carrier.dachser_customer_code)
        self.assertTrue(self.carrier.dachser_customer_label)
        self.assertTrue(self.carrier.dachser_username)
        self.assertTrue(self.carrier.dachser_password)
        params = {
            'id': picking.id,
        }
        wizard = self.env['delivery.dachser'].with_context(
            active_ids=picking.ids, params=params).create({
                'picking_id': picking.id,
                'dachser_postponed_delivery_date': (
                    fields.Date.today() + timedelta(days=7)),
            })
        self.assertEquals(wizard.picking_id, picking)
        self.assertEquals(
            wizard.dachser_sender_code, self.carrier.dachser_customer_code)
        self.assertEquals(
            wizard.dachser_postponed_delivery_date,
            fields.Date.today() + timedelta(days=7))
        self.assertEquals(wizard.dachser_product, '001')
        self.assertFalse(wizard.dachser_arrange_delivery)
        self.assertFalse(wizard.dachser_lifting_platform)
        self.assertEquals(wizard.dachser_country_code.code, 'ES')
        wizard.action_create_dachser_file()
        attachments = self.env['ir.attachment'].search([
            ('res_id', '=', picking.id),
            ('res_model', '=', picking._name),
        ])
        self.assertEquals(len(attachments), 1)
        self.assertEquals(attachments[0].name, 'DACHSER_%s' % picking.name)
