###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo import exceptions
from odoo.tests import common


class TestStockPickingValidateCron(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_12')
        self.product = self.env.ref('stock.product_cable_management_box')
        self.product.tracking = 'none'
        self.location = self.env.ref('stock.stock_location_stock')
        self.inventory = self.env['stock.inventory'].create({
            'name': 'Add products for tests',
            'filter': 'partial',
            'location_id': 10,
            'exhausted': True,
        })
        self.inventory.line_ids.create({
            'inventory_id': self.inventory.id,
            'product_id': self.product.id,
            'product_qty': 10,
            'location_id': self.location.id,
        })
        self.inventory.action_start()
        self.inventory._action_done()
        self.sale = self.env['sale.order'].create({
            'name': 'TEST_01',
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 10,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.sale.action_confirm()

    def test_stock_picking_validate_cron_domain_01(self):
        self.assertEqual(self.product.tracking, 'none')
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(len(picking.move_ids_without_package), 1)
        self.assertEqual(
            picking.move_ids_without_package[0].product_id,
            self.product)
        self.assertEqual(
            picking.move_ids_without_package[0].product_uom_qty,
            self.sale.order_line[0].product_uom_qty)
        self.assertEqual(
            picking.move_ids_without_package[0].reserved_availability,
            self.sale.order_line[0].product_uom_qty)
        self.assertEqual(
            picking.move_ids_without_package[0].reserved_availability,
            picking.move_ids_without_package[0].product_uom_qty)
        self.assertTrue(picking.scheduled_date)
        self.assertEqual(picking.picking_type_code, 'outgoing')
        self.assertEqual(picking.state, 'assigned')
        domain = [('picking_type_code', '=', 'outgoing')]
        limit_date = datetime.now() + relativedelta(days=3)
        self.assertTrue(picking.scheduled_date < limit_date)
        self.env['stock.picking'].cron_picking_validate(domain, 3)
        self.assertEqual(picking.state, 'done')

    def test_stock_picking_validate_cron_domain_02(self):
        self.assertEqual(self.product.tracking, 'none')
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(len(picking.move_ids_without_package), 1)
        self.assertEqual(
            picking.move_ids_without_package[0].product_uom_qty,
            self.sale.order_line[0].product_uom_qty)
        self.assertEqual(
            picking.move_ids_without_package[0].reserved_availability,
            picking.move_ids_without_package[0].product_uom_qty)
        self.assertEqual(picking.picking_type_code, 'outgoing')
        self.assertEqual(picking.state, 'assigned')
        domain = [
            ('partner_id', '=', self.partner.id),
            ('picking_type_code', '=', 'outgoing'),
        ]
        limit_date = datetime.now() + relativedelta(days=4)
        self.assertTrue(picking.scheduled_date < limit_date)
        self.env['stock.picking'].cron_picking_validate(domain, 4)
        self.assertEqual(picking.state, 'done')

    def test_stock_picking_validate_cron_domain_03(self):
        partner = self.env.ref('base.res_partner_2')
        sale = self.env['sale.order'].create({
            'name': 'TEST_02',
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 10,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(len(picking.move_ids_without_package), 1)
        self.assertEqual(
            picking.move_ids_without_package[0].reserved_availability,
            picking.move_ids_without_package[0].product_uom_qty)
        domain = [
            ('partner_id', '=', self.partner.id),
            ('picking_type_code', '=', 'outgoing'),
        ]
        limit_date = datetime.now() + relativedelta(days=5)
        self.assertTrue(picking.scheduled_date < limit_date)
        self.env['stock.picking'].cron_picking_validate(domain, 5)
        self.assertEqual(picking.state, 'assigned')

    def test_check_cron_validate_date_not_included(self):
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(len(picking.move_ids_without_package), 1)
        self.assertEqual(
            picking.move_ids_without_package[0].product_uom_qty,
            picking.move_ids_without_package[0].reserved_availability)
        self.assertEqual(picking.picking_type_code, 'outgoing')
        self.assertEqual(picking.state, 'assigned')
        domain = [
            ('partner_id', '=', self.partner.id),
            ('picking_type_code', '=', 'outgoing'),
        ]
        picking.scheduled_date = picking.scheduled_date + relativedelta(days=4)
        limit_date = datetime.now() + relativedelta(days=2)
        self.assertTrue(limit_date < picking.scheduled_date)
        self.env['stock.picking'].cron_picking_validate(domain, 2)
        self.assertEqual(picking.state, 'assigned')

    def test_check_cron_validate_same_date(self):
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(len(picking.move_ids_without_package), 1)
        self.assertEqual(picking.state, 'assigned')
        domain = [
            ('partner_id', '=', self.partner.id),
            ('picking_type_code', '=', 'outgoing'),
        ]
        picking.scheduled_date = picking.scheduled_date + relativedelta(days=1)
        self.env['stock.picking'].cron_picking_validate(domain, 1)
        self.assertEqual(picking.state, 'assigned')

    def test_check_error_not_domain_param(self):
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['stock.picking'].cron_picking_validate(days=2)
        self.assertEqual(
            result.exception.name,
            'Error validating arguments in the function call: '
            'One or both parameters are not in the function call.'
            'Both parameters are required in the function call.')

    def test_check_error_not_days_param(self):
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        domain = [
            ('state', '=', 'assigned'),
            ('picking_type_code', '=', 'outgoing'),
        ]
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['stock.picking'].cron_picking_validate(domain=domain)
        self.assertEqual(
            result.exception.name,
            'Error validating arguments in the function call: '
            'One or both parameters are not in the function call.'
            'Both parameters are required in the function call.')

    def test_check_error_not_params_to_call_function(self):
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['stock.picking'].cron_picking_validate()
        self.assertEqual(
            result.exception.name,
            'Error validating arguments in the function call: '
            'One or both parameters are not in the function call.'
            'Both parameters are required in the function call.')

    def test_check_error_type_params(self):
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        domain = ('state', '=', 'assigned')
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['stock.picking'].cron_picking_validate(domain, 3)
        self.assertEqual(
            result.exception.name,
            'Error validating the domain: The domain has to be a list')

    def test_not_same_qty_reserved_request(self):
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        domain = [
            ('partner_id', '=', self.partner.id),
            ('picking_type_code', '=', 'outgoing'),
        ]
        self.env['stock.picking'].cron_picking_validate(domain, 3)
        self.assertEqual(picking.state, 'confirmed')

    def test_check_error_stock_state_in_domain(self):
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(len(picking.move_ids_without_package), 1)
        self.assertEqual(
            picking.move_ids_without_package[0].product_uom_qty,
            picking.move_ids_without_package[0].reserved_availability)
        self.assertEqual(picking.picking_type_code, 'outgoing')
        self.assertEqual(picking.state, 'assigned')
        domain = [
            ('state', '=', 'assigned'),
            ('partner_id', '=', self.partner.id),
            ('picking_type_code', '=', 'outgoing'),
        ]
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['stock.picking'].cron_picking_validate(domain, 3)
        self.assertEqual(
            result.exception.name,
            'Error validating the domain: State cannot be passed in '
            'the domain')
