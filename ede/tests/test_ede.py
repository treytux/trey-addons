###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import unittest

from odoo import exceptions
from odoo.tests import TransactionCase


class TestEde(TransactionCase):

    def setUp(self):
        super().setUp()
        #######################################################################
        # IMPORTANTE:
        #
        # - El test funciona contra la wsdl de EDE real por lo que se necesita
        # que tanto el producto como el campo "ede_document_id" del pedido de
        # compra existan en la bd de EDE.
        #
        # - Para lanzar los tests en local varias veces o varios tests a la
        # vez, comentar los "self.env.cr.commit" del código par evitar que
        # guarde los datos en base de datos y de el error de que ya existe el
        # barcode:
        #   Key (barcode)=(4317784094511) already exists.
        # Debido a esto todos los tests excepto uno están comentados.
        #######################################################################
        self.ede_supplier = self.env.ref('ede.res_partner_ede')
        self.customer = self.env['res.partner'].create({
            'name': 'Customer Test',
            'customer': True,
            'supplier': False,
        })
        self.company = self.env.user.company_id
        data = {
            'ede_supplier_id': self.ede_supplier.id,
            'ede_user_id': self.env.user.id,
            'ede_test_wsdl':
                'https://webservices.ede.de:9443/ibis/ws/WS_EXT_ELC?wsdl',
            'ede_test_member': '',  # FILLME
            'ede_test_user': '',  # FILLME
            'ede_test_password': '',  # FILLME
            'ede_test_url_user': '',  # FILLME
            'ede_test_url_password': '',  # FILLME
            'ede_runtime': 'test',
            'ede_picking_type_id': self.env.ref('stock.picking_type_in').id,
            'ede_start_code': '1982',
        }
        self.company.write(data)
        self.route_ede_customer = self.env.ref(
            'stock.route_warehouse0_mto').copy({
                'name': 'Ede Customer',
                'sale_selectable': True,
                'is_ede_customer': True,
            })
        self.route_ede_company = \
            self.route_ede_customer.copy({
                'name': 'Ede Company',
                'sale_selectable': True,
                'is_ede_company': True,
            })
        self.product_01 = self.env['product.product'].create({
            'type': 'product',
            'company_id': self.env.user.company_id.id,
            'name': 'Cortafríos metal 175mm FORMAT',
            'default_code': '198268400175',
            'barcode': '4317784094511',
            'standard_price': 2.92,
            'list_price': 6.08,
            'seller_ids': [(0, 0, {'name': self.ede_supplier.id})],
        })
        self.product_tmpl_obj = self.env['product.template']
        if not all([self.company[val] for val in data.keys()]):
            raise unittest.SkipTest(
                'Necessary EDE configuration not set in company')

    def create_sale_order(self):
        order = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'client_order_ref': 'XXX-YYY-ZZZ',
            'partner_shipping_id': self.customer.id,
        })
        self.env['sale.order.line'].create({
            'product_id': self.product_01.id,
            'product_uom_qty': 1.00,
            'route_id': self.route_ede_customer.id,
            'order_id': order.id,
        })
        return order

    def create_simulation_sale(self, order=None):
        return self.env['simulator.sale'].create({
            'order_id': order.id,
            'lines': [(0, 0, {
                'sale_line_id': order.order_line[0].id,
            })]
        })

    def create_simulation_purchase(self, order=None):
        return self.env['simulator.purchase'].create({
            'order_id': order.id,
            'lines': [(0, 0, {
                'purchase_line_id': order.order_line[0].id,
            })]
        })

    def test_ede_workflow_from_button_ok(self):
        so = self.create_sale_order()
        self.assertEquals(so.state, 'draft')
        self.assertTrue(so.order_line.filtered(
            lambda ln: ln.route_id == self.route_ede_customer))
        so.action_confirm()
        self.assertEquals(so.state, 'sale')
        self.assertTrue(so.name)
        self.assertTrue(so.order_line[0].is_simulator)
        self.assertEquals(so.order_line[0].state, 'sale')
        simu_so = self.create_simulation_sale(so)
        self.assertTrue(simu_so)
        self.assertEquals(simu_so.state, 'step_1')
        simu_so.action_to_step_2()
        self.assertEquals(simu_so.state, 'step_2')
        po = self.env['purchase.order'].search([
            ('sale_order_id', '=', so.id),
        ])
        self.assertTrue(po)
        self.assertEquals(po.state, 'draft')
        self.assertTrue(po.is_ede_order)
        simu_po = self.create_simulation_purchase(po)
        self.assertTrue(simu_po)
        self.assertEquals(simu_po.state, 'step_1')
        simu_po.action_to_step_2()
        self.assertEquals(simu_po.state, 'step_2')
        po.ede_document_id = '5523022986'
        po.ede_state = 'C'
        po.button_confirm()
        self.assertEqual(po.state, 'purchase')
        self.assertEqual(po.picking_count, 1)
        po.action_check_status()
        self.assertEquals(po.ede_state, 'C')
        po_log = self.env['purchase.order.ede.log'].search([])
        self.assertFalse(po_log)

    def test_ede_workflow_from_cron_ok(self):
        so = self.create_sale_order()
        self.assertEquals(so.state, 'draft')
        self.assertTrue(so.order_line.filtered(
            lambda ln: ln.route_id == self.route_ede_customer))
        so.action_confirm()
        self.assertEquals(so.state, 'sale')
        self.assertTrue(so.name)
        self.assertTrue(so.order_line[0].is_simulator)
        self.assertEquals(so.order_line[0].state, 'sale')
        simu_so = self.create_simulation_sale(so)
        self.assertTrue(simu_so)
        self.assertEquals(simu_so.state, 'step_1')
        simu_so.action_to_step_2()
        self.assertEquals(simu_so.state, 'step_2')
        po = self.env['purchase.order'].search([('sale_order_id', '=', so.id)])
        self.assertTrue(po)
        self.assertEquals(po.state, 'draft')
        self.assertTrue(po.is_ede_order, 'Purchase: no purchase ede order')
        simu_po = self.create_simulation_purchase(po)
        self.assertTrue(simu_po)
        self.assertEquals(simu_po.state, 'step_1')
        simu_po.action_to_step_2()
        self.assertEquals(simu_po.state, 'step_2')
        po.ede_document_id = '5523022986'
        po.ede_state = 'C'
        po.button_confirm()
        self.assertEqual(po.state, 'purchase')
        self.assertEqual(po.picking_count, 1)
        # Force to comply with the domain
        po.is_ede_send = True
        po.ede_state = 'A'
        self.env['purchase.order'].search([])._run_ede_check_status()
        # Function set to 'C'
        self.assertEquals(po.ede_state, 'C')
        po_log_lines = self.env['purchase.order.ede.log.line'].search([
            ('supplier_purchase_order_id', '=', po.id),
        ])
        self.assertEquals(len(po_log_lines), 2)
        self.assertEquals(po_log_lines[0].state, 'done')
        self.assertEquals(
            po_log_lines[0].ede_purchase_order_number, '5523022986')
        self.assertIn('Process Confirm Sale', po_log_lines[0].log)
        self.assertEquals(po_log_lines[0].supplier_purchase_order_id, po)
        self.assertEquals(po_log_lines[1].state, 'done')
        self.assertEquals(
            po_log_lines[1].ede_purchase_order_number, '5523022986')
        self.assertIn('Confirmed Picking', po_log_lines[1].log)
        self.assertEquals(po_log_lines[1].supplier_purchase_order_id, po)
        po_log = po_log_lines.mapped('log_id')
        self.assertEquals(len(po_log), 1)
        self.assertEquals(po_log.state, 'done')

    def test_ede_workflow_from_button_error_authorization(self):
        self.company.write({
            'ede_real_password': 'aaaaaa',
        })
        so = self.create_sale_order()
        self.assertEquals(so.state, 'draft')
        self.assertTrue(so.order_line.filtered(
            lambda ln: ln.route_id == self.route_ede_customer))
        so.action_confirm()
        self.assertEquals(so.state, 'sale')
        self.assertTrue(so.name)
        self.assertTrue(so.order_line[0].is_simulator)
        self.assertEquals(so.order_line[0].state, 'sale')
        simu_so = self.create_simulation_sale(so)
        self.assertTrue(simu_so)
        self.assertEquals(simu_so.state, 'step_1')
        with self.assertRaises(exceptions.UserError) as result:
            simu_so.action_to_step_2()
        self.assertEqual(
            result.exception.name, 'EDE not Return Simulation Products')
        po_log = self.env['purchase.order.ede.log'].search([])
        self.assertEqual(len(po_log), 1)
        po_log_lines = self.env['purchase.order.ede.log.line'].search([
            ('ede_purchase_order_number', '=', False),
            ('log_id', '=', po_log.id),
        ])
        self.assertEquals(len(po_log_lines), 1)
        self.assertEquals(po_log_lines.state, 'fail')
        self.assertFalse(po_log_lines.ede_purchase_order_number)
        self.assertIn(
            'EDE Connector Critical Error: Authorization failed!',
            po_log_lines.log)
        self.assertFalse(po_log_lines.supplier_purchase_order_id)

    def test_ede_workflow_from_cron_error_authorization(self):
        self.company.write({
            'ede_real_password': 'aaaaaa',
        })
        so = self.create_sale_order()
        self.assertEquals(so.state, 'draft')
        self.assertTrue(so.order_line.filtered(
            lambda ln: ln.route_id == self.route_ede_customer))
        so.action_confirm()
        self.assertEquals(so.state, 'sale')
        self.assertTrue(so.name)
        self.assertTrue(so.order_line[0].is_simulator)
        self.assertEquals(so.order_line[0].state, 'sale')
        po = self.env['purchase.order'].search([('sale_order_id', '=', so.id)])
        self.assertTrue(po)
        self.assertEquals(po.state, 'draft')
        self.assertTrue(po.is_ede_order, 'Purchase: no purchase ede order')
        po.ede_document_id = '5523022986'
        po.ede_state = 'C'
        po.button_confirm()
        self.assertEqual(po.state, 'purchase')
        self.assertEqual(po.picking_count, 1)
        # Force to comply with the domain
        po.is_ede_send = True
        po.ede_state = 'A'
        self.env['purchase.order'].search([])._run_ede_check_status()
        po_log = self.env['purchase.order.ede.log'].search([])
        self.assertEqual(len(po_log), 1)
        po_log_lines = self.env['purchase.order.ede.log.line'].search([
            ('ede_purchase_order_number', '=', '5523022986'),
            ('log_id', '=', po_log.id),
        ])
        self.assertEquals(len(po_log_lines), 1)
        self.assertEquals(po_log_lines.state, 'fail')
        self.assertEquals(po_log_lines.ede_purchase_order_number, '5523022986')
        self.assertIn(
            'EDE Connector order status no data: 5523022986', po_log_lines.log)
        self.assertIn('Authorization failed!', po_log_lines.log)
        self.assertFalse(po_log_lines.supplier_purchase_order_id)

    ###########################################################################
    # Los tests 'critical_error' sólo funcionan si hay un error crítico en la
    # función 'get_order_status'.
    # Puede simularse, por ejemplo, cambiando el contenido del try por una
    # asignación de una variable que no exista y cambiando:
    #   except RuntimeError as detail:
    # por:
    #   except Exception as detail:
    ###########################################################################
    def test_ede_workflow_from_cron_critical_error(self):
        so = self.create_sale_order()
        self.assertEquals(so.state, 'draft')
        self.assertTrue(so.order_line.filtered(
            lambda ln: ln.route_id == self.route_ede_customer))
        so.action_confirm()
        self.assertEquals(so.state, 'sale')
        self.assertTrue(so.name)
        self.assertTrue(so.order_line[0].is_simulator)
        self.assertEquals(so.order_line[0].state, 'sale')
        po = self.env['purchase.order'].search([
            ('sale_order_id', '=', so.id),
        ])
        self.assertTrue(po)
        self.assertEquals(po.state, 'draft')
        self.assertTrue(po.is_ede_order, 'Purchase: no purchase ede order')
        po.ede_document_id = '5523022986'
        po.ede_state = 'C'
        po.button_confirm()
        self.assertEqual(po.state, 'purchase')
        self.assertEqual(po.picking_count, 1)
        # Force to comply with the domain
        po.is_ede_send = True
        po.ede_state = 'A'
        self.env['purchase.order'].search([])._run_ede_check_status()
        po_log_lines = self.env['purchase.order.ede.log.line'].search([
            ('ede_purchase_order_number', '=', '5523022986'),
        ])
        self.assertEquals(len(po_log_lines), 1)
        self.assertEquals(po_log_lines.state, 'fail')
        self.assertEquals(po_log_lines.ede_purchase_order_number, '5523022986')
        self.assertIn('EDE Connector Critical Error: ', po_log_lines.log)
        self.assertFalse(po_log_lines.supplier_purchase_order_id, po)

    def test_ede_workflow_from_button_critical_error(self):
        so = self.create_sale_order()
        self.assertEquals(so.state, 'draft')
        self.assertTrue(so.order_line.filtered(
            lambda ln: ln.route_id == self.route_ede_customer))
        so.action_confirm()
        self.assertEquals(so.state, 'sale')
        self.assertTrue(so.name)
        self.assertTrue(so.order_line[0].is_simulator)
        self.assertEquals(so.order_line[0].state, 'sale')
        simu_so = self.create_simulation_sale(so)
        self.assertTrue(simu_so)
        self.assertEquals(simu_so.state, 'step_1')
        simu_so.action_to_step_2()
        self.assertEquals(simu_so.state, 'step_2')
        po = self.env['purchase.order'].search([
            ('sale_order_id', '=', so.id),
        ])
        self.assertTrue(po)
        self.assertEquals(po.state, 'draft')
        self.assertTrue(po.is_ede_order)
        simu_po = self.create_simulation_purchase(po)
        self.assertTrue(simu_po)
        self.assertEquals(simu_po.state, 'step_1')
        simu_po.action_to_step_2()
        self.assertEquals(simu_po.state, 'step_2')
        po.ede_document_id = '5523022986'
        po.ede_state = 'C'
        po.button_confirm()
        self.assertEqual(po.state, 'purchase')
        self.assertEqual(po.picking_count, 1)
        po.action_check_status()
        self.assertEquals(po.ede_state, 'C')
        po_log = self.env['purchase.order.ede.log'].search([])
        self.assertEqual(len(po_log), 1)
        po_log_lines = self.env['purchase.order.ede.log.line'].search([
            ('ede_purchase_order_number', '=', '5523022986'),
            ('log_id', '=', po_log.id),
        ])
        self.assertEquals(len(po_log_lines), 1)
        self.assertEquals(po_log_lines.state, 'fail')
        self.assertEquals(po_log_lines.ede_purchase_order_number, '5523022986')
        self.assertIn('EDE Connector Critical Error: ', po_log_lines.log)
        self.assertFalse(po_log_lines.supplier_purchase_order_id)

    def test_cron_ede_update_product_prices(self):
        self.company.write({
            'ede_real_password': 'CHANGE-ME',
        })
        product_02 = self.env['product.product'].create({
            'type': 'product',
            'company_id': self.env.user.company_id.id,
            'name': 'Alicate universal 180mm FORMAT',
            'default_code': '198268400176',
            'barcode': '4003530040009',
            'standard_price': 9999,
            'list_price': 6.55,
            'seller_ids': [(0, 0, {
                'name': self.ede_supplier.id,
                'price': 9999,
            })],
        })
        result = self.product_tmpl_obj.cron_ede_update_product_prices(domain=[
            ('id', '=', product_02.product_tmpl_id.id),
        ])
        self.assertTrue(result)
        self.assertNotEqual(product_02.standard_price, 9999)
        self.assertNotEqual(product_02.seller_ids.price, 9999)

    def test_cron_ede_update_product_prices_without_supplier(self):
        self.company.ede_supplier_id = False
        with self.assertRaises(exceptions.ValidationError) as error:
            self.product_tmpl_obj.cron_ede_update_product_prices()
        self.assertEqual(error.exception.name, 'EDE supplier not configured')

    def test_cron_ede_update_product_prices_without_products(self):
        self.product_01.barcode = False
        with self.assertRaises(exceptions.ValidationError) as error:
            self.product_tmpl_obj.cron_ede_update_product_prices()
        self.assertEqual(
            error.exception.name, 'No products found with EDE supplier')
