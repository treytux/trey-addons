################################################################################
# For copyright and license notices, see __manifest__.py file in root directory
################################################################################
from datetime import timedelta

from odoo import exceptions
from odoo.tests import common


class TestSaleOrderReserveProducts(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 1',
            'standard_price': 10,
            'default_code': '01-PROD',
            'list_price': 100,
            'tracking': 'lot',
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 2',
            'standard_price': 10,
            'default_code': '02-PROD',
            'list_price': 50,
            'tracking': 'lot',
        })
        self.lot_01 = self.env['stock.production.lot'].create({
            'name': '123456789',
            'product_id': self.product_01.id,
        })
        self.lot_02 = self.env['stock.production.lot'].create({
            'name': '987654321',
            'product_id': self.product_02.id,
        })
        self.internal_location = self.env['stock.location'].create({
            'name': 'Test internal location',
            'usage': 'internal',
        })
        internal_type = self.env.ref('stock.picking_type_internal')
        internal_type.active = True
        self.stock_location = self.env.ref('stock.stock_location_stock')

    def create_inventory(self, product, location, qty, lot_id=False):
        inventory = self.env['stock.inventory'].create({
            'name': 'Add products for test',
            'filter': 'partial',
            'location_id': location.id,
            'exhausted': True,
        })
        inventory.action_start()
        inventory.line_ids.create({
            'inventory_id': inventory.id,
            'product_id': product.id,
            'product_qty': qty,
            'location_id': location.id,
            'prod_lot_id': lot_id,
        })
        inventory._action_done()

    def create_sale(self, partner):
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        return sale

    def test_error_no_lot_assigned_to_wizard_line_01(self):
        self.env.user.company_id.location_reserve_default = (
            self.stock_location.id)
        self.create_inventory(
            self.product_01, self.stock_location, 1, self.lot_01.id)
        self.create_inventory(
            self.product_02, self.stock_location, 1, self.lot_02.id)
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 0)
        wizard = self.env['sale.product.reserve'].with_context(
            active_ids=sale.ids, active_id=sale.ids[0]).create({
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.internal_location.id,
            })
        self.assertEqual(len(wizard.line_ids), 2)
        wizard.line_ids[0].lot_id = self.lot_01.id
        self.assertTrue(wizard.line_ids[0].lot_id)
        self.assertTrue(wizard.line_ids[1].lot_id)

    def test_error_lot_not_belong_to_product(self):
        self.env.user.company_id.location_reserve_default = (
            self.stock_location.id)
        self.create_inventory(
            self.product_01, self.stock_location, 1, self.lot_01.id)
        self.create_inventory(
            self.product_02, self.stock_location, 1, self.lot_02.id)
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 0)
        wizard = self.env['sale.product.reserve'].with_context(
            active_ids=sale.ids, active_id=sale.ids[0]).create({
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.internal_location.id,
            })
        self.assertEqual(len(wizard.line_ids), 2)
        lot_test = self.env['stock.production.lot'].create({
            'name': '85293741',
            'product_id': self.product_01.id,
        })
        wizard.line_ids[0].lot_id = self.lot_01.id
        wizard.line_ids[1].lot_id = lot_test.id
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.button_create_internal_picking_reserve()
        self.assertIn(
            'not belong to product', result.exception.name)

    def test_error_no_stock_lot_reserve(self):
        self.env.user.company_id.location_reserve_default = (
            self.stock_location.id)
        self.create_inventory(
            self.product_01, self.stock_location, 1, self.lot_01.id)
        self.assertEquals(
            self.product_01.with_context(
                location=self.stock_location.id,
                lot_id=self.lot_01.id).qty_available, 1)
        self.assertEquals(
            self.product_02.with_context(
                location=self.stock_location.id,
                lot_id=self.lot_02.id).qty_available, 0)
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 0)
        wizard = self.env['sale.product.reserve'].with_context(
            active_ids=sale.ids, active_id=sale.ids[0]).create({
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.internal_location.id,
            })
        self.assertEqual(len(wizard.line_ids), 2)
        wizard.line_ids[0].lot_id = self.lot_01.id
        wizard.line_ids[1].lot_id = self.lot_02.id
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.button_create_internal_picking_reserve()
        self.assertIn(
            'There is no stock of lot', result.exception.name)

    def test_error_action_cancel_reserve_products(self):
        self.create_inventory(
            self.product_01, self.stock_location, 1, self.lot_01.id)
        self.create_inventory(
            self.product_02, self.stock_location, 1, self.lot_02.id)
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 0)
        with self.assertRaises(exceptions.ValidationError) as result:
            sale.action_cancel_reserve_products()
        self.assertEqual(
            result.exception.name, 'No reservation picking to cancel')

    def test_sale_reserve_products_ok(self):
        self.env.user.company_id.location_reserve_default = (
            self.stock_location.id)
        self.create_inventory(
            self.product_01, self.stock_location, 1, self.lot_01.id)
        self.create_inventory(
            self.product_02, self.stock_location, 1, self.lot_02.id)
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 0)
        wizard = self.env['sale.product.reserve'].with_context(
            active_ids=sale.ids, active_id=sale.ids[0]).create({
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.internal_location.id,
            })
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(
            wizard.line_ids[0].product_id, sale.order_line[0].product_id)
        self.assertEqual(
            wizard.line_ids[1].product_id, sale.order_line[1].product_id)
        wizard.line_ids[0].lot_id = self.lot_01.id
        wizard.line_ids[1].lot_id = self.lot_02.id
        self.assertEqual(wizard.line_ids[0].lot_id, self.lot_01)
        self.assertEqual(wizard.line_ids[1].lot_id, self.lot_02)
        wizard.button_create_internal_picking_reserve()
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 1)
        self.assertTrue(sale.reservation_picking_ids[0].customer_reservation)
        self.assertEqual(sale.reservation_picking_ids[0].state, 'assigned')
        reserved_picking = sale.reservation_picking_ids[0]
        self.assertEqual(reserved_picking.sale_reservation, sale)
        self.assertTrue(reserved_picking.sale_reservation.customer_reservation)

    def test_sale_reserve_and_unreserve_products_ok(self):
        self.env.user.company_id.location_reserve_default = (
            self.stock_location.id)
        self.create_inventory(
            self.product_01, self.stock_location, 1, self.lot_01.id)
        self.create_inventory(
            self.product_02, self.stock_location, 1, self.lot_02.id)
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 0)
        wizard = self.env['sale.product.reserve'].with_context(
            active_ids=sale.ids, active_id=sale.ids[0]).create({
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.internal_location.id,
            })
        self.assertEqual(len(wizard.line_ids), 2)
        wizard.line_ids[0].lot_id = self.lot_01.id
        wizard.line_ids[1].lot_id = self.lot_02.id
        wizard.button_create_internal_picking_reserve()
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 1)
        self.assertTrue(sale.reservation_picking_ids[0].customer_reservation)
        self.assertEqual(sale.reservation_picking_ids[0].state, 'assigned')
        sale.action_cancel_reserve_products()
        self.assertEqual(len(sale.reservation_picking_ids), 1)
        self.assertEqual(sale.reservation_picking_ids[0].state, 'cancel')
        reserved_picking = sale.reservation_picking_ids[0]
        self.assertEqual(reserved_picking.sale_reservation, sale)
        self.assertFalse(reserved_picking.sale_reservation.customer_reservation)

    def test_confirm_sale_reserve(self):
        self.env.user.company_id.location_reserve_default = (
            self.stock_location.id)
        self.create_inventory(
            self.product_01, self.stock_location, 1, self.lot_01.id)
        self.create_inventory(
            self.product_02, self.stock_location, 1, self.lot_02.id)
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 0)
        wizard = self.env['sale.product.reserve'].with_context(
            active_ids=sale.ids, active_id=sale.ids[0]).create({
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.internal_location.id,
            })
        self.assertEqual(len(wizard.line_ids), 2)
        wizard.line_ids[0].lot_id = self.lot_01.id
        wizard.line_ids[1].lot_id = self.lot_02.id
        wizard.button_create_internal_picking_reserve()
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 1)
        self.assertTrue(sale.reservation_picking_ids[0].customer_reservation)
        self.assertEqual(sale.reservation_picking_ids[0].state, 'assigned')
        reserved_picking = sale.reservation_picking_ids[0]
        self.assertEqual(reserved_picking.sale_reservation, sale)
        self.assertTrue(reserved_picking.sale_reservation.customer_reservation)
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(sale.picking_ids[0].state, 'assigned')
        self.assertEqual(len(sale.reservation_picking_ids), 1)
        self.assertEqual(sale.reservation_picking_ids[0].state, 'cancel')
        picking = sale.picking_ids[0]
        self.assertEqual(len(picking.move_lines), 2)
        self.assertEqual(len(picking.move_line_ids), 2)
        self.assertEqual(picking.move_line_ids[0].product_id, self.product_01)
        self.assertEqual(picking.move_line_ids[0].lot_id, self.lot_01)
        self.assertEqual(picking.move_line_ids[1].product_id, self.product_02)
        self.assertEqual(picking.move_line_ids[1].lot_id, self.lot_02)

    def test_cron_date_ok(self):
        self.env.user.company_id.location_reserve_default = (
            self.stock_location.id)
        self.create_inventory(
            self.product_01, self.stock_location, 1, self.lot_01.id)
        self.create_inventory(
            self.product_02, self.stock_location, 1, self.lot_02.id)
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 0)
        wizard = self.env['sale.product.reserve'].with_context(
            active_ids=sale.ids, active_id=sale.ids[0]).create({
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.internal_location.id,
            })
        self.assertEqual(len(wizard.line_ids), 2)
        wizard.line_ids[0].lot_id = self.lot_01.id
        wizard.line_ids[1].lot_id = self.lot_02.id
        wizard.button_create_internal_picking_reserve()
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 1)
        self.assertTrue(sale.reservation_picking_ids[0].customer_reservation)
        days = self.env['ir.config_parameter'].sudo().get_param(
            'sale_order_reserve_products.days_to_unreserve_pickings')
        days_delay = int(days) + 1
        reserved_picking = sale.reservation_picking_ids[0]
        reserved_picking.create_date = reserved_picking.create_date - timedelta(
            days=int(days_delay))
        self.assertEqual(reserved_picking.state, 'assigned')
        self.env['stock.picking'].cron_unreserve_sale_pickings()
        self.assertEqual(reserved_picking.state, 'assigned')
        reserved_picking = sale.reservation_picking_ids[0]
        self.assertEqual(reserved_picking.sale_reservation, sale)
        self.assertTrue(reserved_picking.sale_reservation.customer_reservation)

    def test_cron_date_exceeded(self):
        self.env.user.company_id.location_reserve_default = (
            self.stock_location.id)
        self.create_inventory(
            self.product_01, self.stock_location, 1, self.lot_01.id)
        self.create_inventory(
            self.product_02, self.stock_location, 1, self.lot_02.id)
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 0)
        wizard = self.env['sale.product.reserve'].with_context(
            active_ids=sale.ids, active_id=sale.ids[0]).create({
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.internal_location.id,
            })
        self.assertEqual(len(wizard.line_ids), 2)
        wizard.line_ids[0].lot_id = self.lot_01.id
        wizard.line_ids[1].lot_id = self.lot_02.id
        wizard.button_create_internal_picking_reserve()
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 1)
        self.assertTrue(sale.reservation_picking_ids[0].customer_reservation)
        reserved_picking = sale.reservation_picking_ids[0]
        self.assertEqual(reserved_picking.state, 'assigned')
        self.env['stock.picking'].cron_unreserve_sale_pickings()
        self.assertEqual(reserved_picking.state, 'cancel')
        self.assertIn(
            'Reservation canceled with planned action for exceeding the days',
            reserved_picking.message_ids[0].body)
        self.assertEqual(reserved_picking.sale_reservation, sale)
        self.assertFalse(reserved_picking.sale_reservation.customer_reservation)

    def test_cron_date_today(self):
        self.env.user.company_id.location_reserve_default = (
            self.stock_location.id)
        self.create_inventory(
            self.product_01, self.stock_location, 1, self.lot_01.id)
        self.create_inventory(
            self.product_02, self.stock_location, 1, self.lot_02.id)
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 0)
        wizard = self.env['sale.product.reserve'].with_context(
            active_ids=sale.ids, active_id=sale.ids[0]).create({
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.internal_location.id,
            })
        self.assertEqual(len(wizard.line_ids), 2)
        wizard.line_ids[0].lot_id = self.lot_01.id
        wizard.line_ids[1].lot_id = self.lot_02.id
        wizard.button_create_internal_picking_reserve()
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 1)
        self.assertTrue(sale.reservation_picking_ids[0].customer_reservation)
        reserved_picking = sale.reservation_picking_ids[0]
        days = self.env['ir.config_parameter'].sudo().get_param(
            'sale_order_reserve_products.days_to_unreserve_pickings')
        reserved_picking.create_date = reserved_picking.create_date - timedelta(
            days=int(days))
        self.assertEqual(reserved_picking.state, 'assigned')
        self.env['stock.picking'].cron_unreserve_sale_pickings()
        self.assertEqual(reserved_picking.state, 'cancel')
        self.assertIn(
            'Reservation canceled with planned action for exceeding the days',
            reserved_picking.message_ids[0].body)
        self.assertEqual(reserved_picking.sale_reservation, sale)
        self.assertFalse(reserved_picking.sale_reservation.customer_reservation)

    def test_autocomplete_lots_line_wizard_01(self):
        self.assertFalse(self.env.user.company_id.location_reserve_default)
        self.env.user.company_id.location_reserve_default = (
            self.stock_location.id)
        self.assertTrue(self.env.user.company_id.location_reserve_default)
        self.assertFalse(self.internal_location.reserve_products_location)
        self.internal_location.reserve_products_location = True
        self.assertTrue(self.internal_location.reserve_products_location)
        self.create_inventory(
            self.product_01, self.stock_location, 1, self.lot_01.id)
        self.create_inventory(
            self.product_02, self.stock_location, 1, self.lot_02.id)
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 0)
        lot_test_01 = self.env['stock.production.lot'].create({
            'name': '85293741',
            'product_id': self.product_01.id,
        })
        lot_test_02 = self.env['stock.production.lot'].create({
            'name': '95175365',
            'product_id': self.product_02.id,
        })
        self.create_inventory(
            self.product_01, self.stock_location, 1, lot_test_01.id)
        self.create_inventory(
            self.product_02, self.stock_location, 1, lot_test_02.id)
        wizard = self.env['sale.product.reserve'].with_context(
            active_ids=sale.ids, active_id=sale.ids[0]).create({
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.internal_location.id,
            })
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertTrue(wizard.line_ids[0].lot_id)
        self.assertEqual(wizard.line_ids[0].lot_id, self.lot_01)
        self.assertTrue(wizard.line_ids[0].location_id)
        self.assertEqual(wizard.line_ids[0].location_id, self.stock_location)
        self.assertTrue(wizard.line_ids[1].lot_id)
        self.assertEqual(wizard.line_ids[1].lot_id, self.lot_02)
        self.assertTrue(wizard.line_ids[1].location_id)
        self.assertEqual(wizard.line_ids[1].location_id, self.stock_location)
        self.assertEqual(
            wizard.line_ids[0].lots_selected.ids,
            [self.lot_01.id, lot_test_01.id])
        self.assertEqual(
            wizard.line_ids[1].lots_selected.ids,
            [self.lot_02.id, lot_test_02.id])
        wizard.button_create_internal_picking_reserve()
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 1)
        self.assertTrue(sale.reservation_picking_ids[0].customer_reservation)
        self.assertEqual(sale.reservation_picking_ids[0].state, 'assigned')
        reserved_picking = sale.reservation_picking_ids[0]
        self.assertEqual(reserved_picking.sale_reservation, sale)
        self.assertTrue(reserved_picking.sale_reservation.customer_reservation)
        self.assertEqual(
            reserved_picking.move_line_ids[0].product_id, self.product_01)
        self.assertEqual(
            reserved_picking.move_line_ids[0].lot_id, self.lot_01)
        self.assertEqual(
            reserved_picking.move_line_ids[1].product_id, self.product_02)
        self.assertEqual(
            reserved_picking.move_line_ids[1].lot_id, self.lot_02)
        sale.action_cancel_reserve_products()
        self.assertEqual(len(sale.reservation_picking_ids), 1)
        self.assertEqual(sale.reservation_picking_ids[0].state, 'cancel')
        reserved_picking = sale.reservation_picking_ids[0]
        self.assertEqual(reserved_picking.sale_reservation, sale)
        self.assertFalse(reserved_picking.sale_reservation.customer_reservation)
        wizard = self.env['sale.product.reserve'].with_context(
            active_ids=sale.ids, active_id=sale.ids[0]).create({
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.internal_location.id,
            })
        wizard.button_create_internal_picking_reserve()
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.reservation_picking_ids), 2)
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(sale.picking_ids[0].state, 'assigned')
        self.assertEqual(sale.reservation_picking_ids[0].state, 'cancel')
        self.assertEqual(sale.reservation_picking_ids[1].state, 'cancel')
        picking = sale.picking_ids[0]
        self.assertEqual(len(picking.move_lines), 2)
        self.assertEqual(len(picking.move_line_ids), 2)
        self.assertEqual(picking.move_line_ids[0].product_id, self.product_01)
        self.assertEqual(picking.move_line_ids[0].lot_id, self.lot_01)
        self.assertEqual(picking.move_line_ids[1].product_id, self.product_02)
        self.assertEqual(picking.move_line_ids[1].lot_id, self.lot_02)

    def test_autocomplete_lots_line_wizard_02(self):
        self.assertFalse(self.env.user.company_id.location_reserve_default)
        self.env.user.company_id.location_reserve_default = (
            self.stock_location.id)
        self.assertTrue(self.env.user.company_id.location_reserve_default)
        self.assertFalse(self.internal_location.reserve_products_location)
        self.internal_location.reserve_products_location = True
        self.assertTrue(self.internal_location.reserve_products_location)
        self.create_inventory(
            self.product_01, self.stock_location, 1, self.lot_01.id)
        self.env['stock.production.lot'].create({
            'name': '85293741',
            'product_id': self.product_01.id,
        })
        self.env['stock.production.lot'].create({
            'name': '95175365',
            'product_id': self.product_02.id,
        })
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 0)
        wizard = self.env['sale.product.reserve'].with_context(
            active_ids=sale.ids, active_id=sale.ids[0]).create({
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.internal_location.id,
            })
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertTrue(wizard.line_ids[0].lot_id)
        self.assertEqual(wizard.line_ids[0].product_id, self.product_01)
        self.assertEqual(
            wizard.line_ids[0].lots_selected.ids, [self.lot_01.id])
        self.assertFalse(wizard.line_ids[1].lot_id)
        self.assertEqual(wizard.line_ids[1].product_id, self.product_02)
        self.assertEqual(
            wizard.line_ids[1].lots_selected.ids, [])
        self.assertEqual(len(wizard.msg_line_ids), 1)
        self.assertEqual(
            wizard.msg_line_ids[0].name,
            'Not enough stock of product %s at location %s' % (
                self.product_02.name, self.stock_location.name))

    def test_autocomplete_lots_line_wizard_03(self):
        internal_location_02 = self.env['stock.location'].create({
            'name': 'Test internal location 2',
            'usage': 'internal',
            'location_id': self.stock_location.id,
        })
        self.assertFalse(self.env.user.company_id.location_reserve_default)
        self.env.user.company_id.location_reserve_default = (
            self.stock_location.id)
        self.assertTrue(self.env.user.company_id.location_reserve_default)
        self.assertFalse(self.internal_location.reserve_products_location)
        self.internal_location.reserve_products_location = True
        self.assertTrue(self.internal_location.reserve_products_location)
        self.create_inventory(
            self.product_01, self.stock_location, 1, self.lot_01.id)
        self.create_inventory(
            self.product_02, self.stock_location, 1, self.lot_02.id)
        lot_test_01 = self.env['stock.production.lot'].create({
            'name': '85293741',
            'product_id': self.product_01.id,
        })
        lot_test_02 = self.env['stock.production.lot'].create({
            'name': '95175365',
            'product_id': self.product_02.id,
        })
        self.create_inventory(
            self.product_01, self.stock_location, 1, lot_test_01.id)
        self.create_inventory(
            self.product_02, internal_location_02, 1, lot_test_02.id)
        sale = self.create_sale(self.partner)
        wizard = self.env['sale.product.reserve'].with_context(
            active_ids=sale.ids, active_id=sale.ids[0]).create({
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.internal_location.id,
            })
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertTrue(wizard.line_ids[0].lot_id)
        self.assertEqual(wizard.line_ids[0].lot_id, self.lot_01)
        self.assertTrue(wizard.line_ids[0].location_id)
        self.assertEqual(wizard.line_ids[0].location_id, self.stock_location)
        self.assertTrue(wizard.line_ids[1].lot_id)
        self.assertEqual(wizard.line_ids[1].lot_id, self.lot_02)
        self.assertTrue(wizard.line_ids[1].location_id)
        self.assertEqual(wizard.line_ids[1].location_id, self.stock_location)
        self.assertEqual(
            wizard.line_ids[0].lots_selected.ids,
            [self.lot_01.id, lot_test_01.id])
        self.assertEqual(
            wizard.line_ids[1].lots_selected.ids,
            [self.lot_02.id, lot_test_02.id])
        wizard.line_ids[1].lot_id = lot_test_02.id
        wizard.line_ids[1].onchange_lot_id()
        self.assertEqual(wizard.line_ids[1].lot_id, lot_test_02)
        self.assertEqual(wizard.line_ids[1].location_id, internal_location_02)

    def test_sale_reserve_product_lot_in_multiple_sales(self):
        self.env.user.company_id.location_reserve_default = (
            self.stock_location.id)
        self.create_inventory(
            self.product_01, self.stock_location, 2, self.lot_01.id)
        self.create_inventory(
            self.product_02, self.stock_location, 1, self.lot_02.id)
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 0)
        wizard = self.env['sale.product.reserve'].with_context(
            active_ids=sale.ids, active_id=sale.ids[0]).create({
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.internal_location.id,
            })
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(
            wizard.line_ids[0].product_id, sale.order_line[0].product_id)
        self.assertEqual(
            wizard.line_ids[1].product_id, sale.order_line[1].product_id)
        self.assertEqual(wizard.line_ids[0].lot_id, self.lot_01)
        self.assertEqual(wizard.line_ids[1].lot_id, self.lot_02)
        self.assertEqual(
            wizard.line_ids[0].lots_selected.ids, self.lot_01.ids)
        self.assertEqual(
            wizard.line_ids[1].lots_selected.ids, self.lot_02.ids)
        wizard.button_create_internal_picking_reserve()
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 1)
        self.assertEqual(sale.reservation_picking_ids[0].state, 'assigned')
        reserved_picking = sale.reservation_picking_ids[0]
        self.assertEqual(reserved_picking.sale_reservation, sale)
        self.assertTrue(reserved_picking.sale_reservation.customer_reservation)
        sale_02 = self.create_sale(self.partner)
        self.assertEqual(len(sale_02.reservation_picking_ids), 0)
        wizard_02 = self.env['sale.product.reserve'].with_context(
            active_ids=sale_02.ids, active_id=sale_02.ids[0]).create({
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.internal_location.id,
            })
        self.assertEqual(len(wizard_02.line_ids), 2)
        self.assertEqual(
            wizard_02.line_ids[0].product_id, sale.order_line[0].product_id)
        self.assertEqual(
            wizard_02.line_ids[1].product_id, sale.order_line[1].product_id)
        self.assertEqual(wizard_02.line_ids[0].lot_id, self.lot_01)
        self.assertFalse(wizard_02.line_ids[1].lot_id)
        self.assertEqual(
            wizard_02.line_ids[0].lots_selected.ids, self.lot_01.ids)
        self.assertEqual(
            wizard_02.line_ids[1].lots_selected.ids, [])
        self.assertEqual(len(wizard_02.msg_line_ids), 1)
        self.assertEqual(
            wizard_02.msg_line_ids[0].name,
            'Not enough stock of product %s at location %s' % (
                self.product_02.name, self.stock_location.name))
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.button_create_internal_picking_reserve()
        self.assertEqual(
            result.exception.name,
            'There is no stock of lot %s in location %s.' % (
                self.lot_02.name, self.stock_location.name))

    def test_not_enough_stock_lot_reserve_01(self):
        self.env.user.company_id.location_reserve_default = (
            self.stock_location.id)
        self.create_inventory(
            self.product_01, self.stock_location, 1, self.lot_01.id)
        self.assertEquals(
            self.product_01.with_context(
                location=self.stock_location.id,
                lot_id=self.lot_01.id).qty_available, 1)
        self.assertEquals(
            self.product_02.with_context(
                location=self.stock_location.id,
                lot_id=self.lot_02.id).qty_available, 0)
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 0)
        wizard = self.env['sale.product.reserve'].with_context(
            active_ids=sale.ids, active_id=sale.ids[0]).create({
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.internal_location.id,
            })
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(wizard.line_ids[0].lot_id, self.lot_01)
        self.assertEqual(wizard.line_ids[0].product_id, self.product_01)
        self.assertFalse(wizard.line_ids[1].lot_id)
        self.assertEqual(wizard.line_ids[1].product_id, self.product_02)
        reserved_picking = wizard.button_create_internal_picking_reserve()
        self.assertEqual(reserved_picking.state, 'assigned')
        self.assertEqual(len(reserved_picking.move_lines), 1)
        self.assertEqual(len(reserved_picking.move_line_ids), 1)
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.reservation_picking_ids), 1)
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(sale.reservation_picking_ids[0].state, 'cancel')
        picking = sale.picking_ids[0]
        self.assertEqual(picking.state, 'assigned')
        self.assertTrue(picking.show_check_availability)
        self.assertEqual(len(picking.move_lines), 2)
        self.assertEqual(len(picking.move_line_ids), 1)
        self.assertEqual(picking.move_line_ids[0].product_id, self.product_01)
        picking.action_done()
        self.assertEqual(picking.state, 'assigned')

    def test_not_enough_stock_lot_reserve_02(self):
        self.env.user.company_id.location_reserve_default = (
            self.stock_location.id)
        self.create_inventory(
            self.product_01, self.stock_location, 1, self.lot_01.id)
        self.assertEquals(
            self.product_01.with_context(
                location=self.stock_location.id,
                lot_id=self.lot_01.id).qty_available, 1)
        self.assertEquals(
            self.product_02.with_context(
                location=self.stock_location.id,
                lot_id=self.lot_02.id).qty_available, 0)
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 0)
        wizard = self.env['sale.product.reserve'].with_context(
            active_ids=sale.ids, active_id=sale.ids[0]).create({
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.internal_location.id,
            })
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(wizard.line_ids[0].lot_id, self.lot_01)
        self.assertEqual(wizard.line_ids[0].product_id, self.product_01)
        self.assertFalse(wizard.line_ids[1].lot_id)
        self.assertEqual(wizard.line_ids[1].product_id, self.product_02)
        reserved_picking = wizard.button_create_internal_picking_reserve()
        self.assertEqual(reserved_picking.state, 'assigned')
        self.assertEqual(len(reserved_picking.move_lines), 1)
        self.assertEqual(len(reserved_picking.move_line_ids), 1)
        qty_available = self.env['stock.quant']._get_available_quantity(
            self.product_02, self.stock_location, self.lot_02)
        self.assertTrue(qty_available == 0)
        self.create_inventory(
            self.product_02, self.stock_location, 1, self.lot_02.id)
        qty_available = self.env['stock.quant']._get_available_quantity(
            self.product_02, self.stock_location, self.lot_02)
        self.assertTrue(qty_available == 1)
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.reservation_picking_ids), 1)
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(sale.reservation_picking_ids[0].state, 'cancel')
        picking = sale.picking_ids[0]
        self.assertEqual(picking.state, 'assigned')
        self.assertFalse(picking.show_check_availability)
        self.assertEqual(len(picking.move_lines), 2)
        self.assertEqual(len(picking.move_line_ids), 2)
        self.assertEqual(picking.move_line_ids[0].product_id, self.product_01)
        self.assertEqual(picking.move_line_ids[0].lot_id, self.lot_01)
        self.assertEqual(picking.move_line_ids[1].product_id, self.product_02)
        self.assertEqual(picking.move_line_ids[1].lot_id, self.lot_02)

    def test_not_enough_stock_lot_reserve_03(self):
        self.env.user.company_id.location_reserve_default = (
            self.stock_location.id)
        self.create_inventory(
            self.product_01, self.stock_location, 1, self.lot_01.id)
        self.assertEquals(
            self.product_01.with_context(
                location=self.stock_location.id,
                lot_id=self.lot_01.id).qty_available, 1)
        self.create_inventory(
            self.product_02, self.stock_location, 1, self.lot_02.id)
        self.assertEquals(
            self.product_02.with_context(
                location=self.stock_location.id,
                lot_id=self.lot_02.id).qty_available, 1)
        sale = self.create_sale(self.partner)
        self.assertEqual(sale.order_line[0].product_uom_qty, 1)
        self.assertEqual(sale.order_line[1].product_uom_qty, 1)
        sale.order_line[0].product_uom_qty = 2
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 0)
        wizard = self.env['sale.product.reserve'].with_context(
            active_ids=sale.ids, active_id=sale.ids[0]).create({
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.internal_location.id,
            })
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(wizard.line_ids[0].lot_id, self.lot_01)
        self.assertEqual(wizard.line_ids[0].product_id, self.product_01)
        self.assertFalse(wizard.line_ids[1].lot_id, self.lot_01)
        self.assertEqual(wizard.line_ids[1].product_id, self.product_01)
        self.assertEqual(wizard.line_ids[2].lot_id, self.lot_02)
        self.assertEqual(wizard.line_ids[2].product_id, self.product_02)
        self.assertEqual(len(wizard.msg_line_ids), 1)
        reserved_picking = wizard.button_create_internal_picking_reserve()
        self.assertEqual(reserved_picking.state, 'assigned')
        self.assertEqual(len(reserved_picking.move_lines), 2)
        self.assertEqual(len(reserved_picking.move_line_ids), 2)
        self.assertEqual(
            reserved_picking.move_line_ids[0].product_id, self.product_01)
        self.assertEqual(
            reserved_picking.move_line_ids[0].lot_id, self.lot_01)
        self.assertEqual(
            reserved_picking.move_line_ids[1].product_id, self.product_02)
        self.assertEqual(reserved_picking.move_line_ids[1].lot_id, self.lot_02)
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.reservation_picking_ids), 1)
        self.assertEqual(len(sale.picking_ids), 1)
        self.assertEqual(sale.reservation_picking_ids[0].state, 'cancel')
        picking = sale.picking_ids[0]
        self.assertEqual(picking.state, 'assigned')
        self.assertTrue(picking.show_check_availability)
        self.assertEqual(len(picking.move_lines), 2)
        self.assertEqual(len(picking.move_line_ids), 2)
        self.assertEqual(picking.move_line_ids[0].product_id, self.product_01)
        self.assertEqual(picking.move_line_ids[0].lot_id, self.lot_01)
        self.assertEqual(picking.move_line_ids[1].product_id, self.product_02)
        self.assertEqual(picking.move_line_ids[1].lot_id, self.lot_02)
        picking.action_done()
        self.assertEqual(picking.state, 'assigned')

    def test_cancel_sale_release_picking_reservation(self):
        self.env.user.company_id.location_reserve_default = (
            self.stock_location.id)
        self.create_inventory(
            self.product_01, self.stock_location, 1, self.lot_01.id)
        self.create_inventory(
            self.product_02, self.stock_location, 1, self.lot_02.id)
        sale = self.create_sale(self.partner)
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 0)
        wizard = self.env['sale.product.reserve'].with_context(
            active_ids=sale.ids, active_id=sale.ids[0]).create({
                'location_src_id': self.stock_location.id,
                'location_dest_id': self.internal_location.id,
            })
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(
            wizard.line_ids[0].product_id, sale.order_line[0].product_id)
        self.assertEqual(
            wizard.line_ids[1].product_id, sale.order_line[1].product_id)
        wizard.line_ids[0].lot_id = self.lot_01.id
        wizard.line_ids[1].lot_id = self.lot_02.id
        self.assertEqual(wizard.line_ids[0].lot_id, self.lot_01)
        self.assertEqual(wizard.line_ids[1].lot_id, self.lot_02)
        wizard.button_create_internal_picking_reserve()
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 1)
        self.assertTrue(sale.reservation_picking_ids[0].customer_reservation)
        self.assertEqual(sale.reservation_picking_ids[0].state, 'assigned')
        reserved_picking = sale.reservation_picking_ids[0]
        self.assertEqual(reserved_picking.sale_reservation, sale)
        self.assertTrue(reserved_picking.sale_reservation.customer_reservation)
        self.assertEqual(sale.state, 'draft')
        sale.action_cancel()
        self.assertEqual(sale.state, 'cancel')
        self.assertEqual(len(sale.picking_ids), 0)
        self.assertEqual(len(sale.reservation_picking_ids), 1)
        self.assertEqual(reserved_picking.state, 'cancel')
