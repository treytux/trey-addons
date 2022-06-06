###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests import common


class TestStockPickingBatchDeliveryUnique(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': False,
        })
        self.free_delivery = self.env.ref('delivery.free_delivery_carrier')
        self.product_01 = self.env['product.product'].create({
            'name': 'Product test 01',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
            'weight': 3,
        })
        self.product_02 = self.env['product.product'].create({
            'name': 'Product test 02',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
            'weight': 2,
        })
        self.product_03 = self.env['product.product'].create({
            'name': 'Product test 03',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
            'weight': 3,
        })
        self.product_04 = self.env['product.product'].create({
            'name': 'Product test 04',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
            'weight': 2,
        })
        self.picking_01 = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': (
                self.env.ref('stock.stock_location_customers').id),
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'carrier_id': self.free_delivery.id,
        })
        self.env['stock.move'].create({
            'name': self.product_01.name,
            'product_id': self.product_01.id,
            'product_uom_qty': 2,
            'product_uom': self.product_01.uom_id.id,
            'picking_id': self.picking_01.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': (
                self.env.ref('stock.stock_location_customers').id),
        })
        self.picking_02 = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': (
                self.env.ref('stock.stock_location_customers').id),
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'carrier_id': self.free_delivery.id,
        })
        self.env['stock.move'].create({
            'name': self.product_02.name,
            'product_id': self.product_02.id,
            'product_uom_qty': 3,
            'product_uom': self.product_02.uom_id.id,
            'picking_id': self.picking_02.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': (
                self.env.ref('stock.stock_location_customers').id),
        })
        self.batch = self.env['stock.picking.batch'].create({
            'name': 'Batch 1',
            'picking_ids': [
                [6, False, [self.picking_01.id, self.picking_02.id]]
            ],
            'carrier_id': False,
        })
        self.picking_03 = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': (
                self.env.ref('stock.stock_location_customers').id),
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'carrier_id': self.free_delivery.id,
        })
        self.move_01 = self.env['stock.move'].create({
            'name': self.product_03.name,
            'product_id': self.product_03.id,
            'product_uom_qty': 4,
            'product_uom': self.product_03.uom_id.id,
            'picking_id': self.picking_03.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': (
                self.env.ref('stock.stock_location_customers').id),
        })
        self.picking_04 = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': (
                self.env.ref('stock.stock_location_customers').id),
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'carrier_id': self.free_delivery.id,
        })
        self.move_02 = self.env['stock.move'].create({
            'name': self.product_04.name,
            'product_id': self.product_04.id,
            'product_uom_qty': 4,
            'product_uom': self.product_04.uom_id.id,
            'picking_id': self.picking_04.id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': (
                self.env.ref('stock.stock_location_customers').id),
        })
        self.product_shipping_costs = self.env['product.product'].create({
            'type': 'service',
            'name': 'Shipping costs',
            'standard_price': 5,
            'list_price': 10,
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Carrier test',
            'delivery_type': 'fixed',
            'product_id': self.product_shipping_costs.id,
            'fixed_price': 3,
        })

    def test_check_cancel_stock_picking_batch(self):
        self.env['stock.quant']._update_available_quantity(
            self.product_01, self.env.ref('stock.stock_location_stock'), 10.0)
        self.env['stock.quant']._update_available_quantity(
            self.product_02, self.env.ref('stock.stock_location_stock'), 10.0)
        self.batch.confirm_picking()
        self.assertEqual(self.picking_01.state, 'assigned')
        self.assertEqual(self.picking_02.state, 'assigned')
        self.picking_01.move_lines.quantity_done = 10
        self.picking_02.move_lines.quantity_done = 10
        picking_type_01 = self.picking_02.picking_type_id or (
            self.picking_02._get_default_picking_type())
        picking_type_01 = self.env['stock.picking.type'].browse(
            picking_type_01.id)
        if picking_type_01:
            sequence_01 = picking_type_01.sequence_id.number_next_actual
        self.batch.done()
        simulate_picking = self.env['stock.picking'].search([
            ('name', '=', self.batch.name),
        ])
        self.assertFalse(simulate_picking)
        picking_type_02 = self.picking_02.picking_type_id or (
            self.picking_02._get_default_picking_type())
        picking_type_02 = self.env['stock.picking.type'].browse(
            picking_type_02.id)
        if picking_type_02:
            sequence_02 = picking_type_02.sequence_id.number_next_actual
        self.assertEqual(sequence_01, sequence_02)
        self.assertEqual(self.picking_01.state, 'done')
        self.assertEqual(self.picking_02.state, 'done')
        quant_01 = self.env['stock.quant']._gather(
            self.product_01, self.env.ref('stock.stock_location_stock'))
        quant_02 = self.env['stock.quant']._gather(
            self.product_02, self.env.ref('stock.stock_location_stock'))
        self.assertFalse(sum(quant_01.mapped('quantity')))
        self.assertFalse(sum(quant_02.mapped('quantity')))
        self.assertFalse(self.picking_01.carrier_tracking_ref)
        self.assertFalse(self.picking_02.carrier_tracking_ref)
        with self.assertRaises(exceptions.UserError):
            self.picking_01.action_cancel()
        with self.assertRaises(exceptions.UserError):
            self.batch.cancel_picking()

    def test_check_stock_move_lines_include(self):
        self.env['stock.quant']._update_available_quantity(
            self.product_01, self.env.ref('stock.stock_location_stock'), 10.0)
        self.env['stock.quant']._update_available_quantity(
            self.product_02, self.env.ref('stock.stock_location_stock'), 10.0)
        self.batch.confirm_picking()
        self.picking_01.action_cancel()
        self.picking_02.move_lines.quantity_done = 10
        self.assertEqual(self.picking_01.state, 'cancel')
        self.batch.done()
        self.assertEqual(self.picking_01.state, 'cancel')
        self.assertEqual(self.picking_02.state, 'done')
        quant_02 = self.env['stock.quant']._gather(
            self.product_02, self.env.ref('stock.stock_location_stock'))
        self.assertFalse(sum(quant_02.mapped('quantity')))
        self.assertFalse(self.picking_01.carrier_tracking_ref)
        self.assertFalse(self.picking_02.carrier_tracking_ref)

    def test_create_stock_picking_batch_and_validate(self):
        self.env['stock.quant']._update_available_quantity(
            self.product_01, self.env.ref('stock.stock_location_stock'), 10.0)
        self.env['stock.quant']._update_available_quantity(
            self.product_02, self.env.ref('stock.stock_location_stock'), 10.0)
        self.batch.confirm_picking()
        self.assertEqual(self.picking_01.state, 'assigned')
        self.assertEqual(self.picking_02.state, 'assigned')
        self.picking_01.move_lines.quantity_done = 10
        self.picking_02.move_lines.quantity_done = 10
        picking_type_01 = self.picking_02.picking_type_id or (
            self.picking_02._get_default_picking_type())
        picking_type_01 = self.env['stock.picking.type'].browse(
            picking_type_01.id)
        if picking_type_01:
            sequence_01 = picking_type_01.sequence_id.number_next_actual
        self.batch.done()
        simulate_picking = self.env['stock.picking'].search([
            ('name', '=', self.batch.name),
        ])
        self.assertFalse(simulate_picking)
        picking_type_02 = self.picking_02.picking_type_id or (
            self.picking_02._get_default_picking_type())
        picking_type_02 = self.env['stock.picking.type'].browse(
            picking_type_02.id)
        if picking_type_02:
            sequence_02 = picking_type_02.sequence_id.number_next_actual
        self.assertEqual(sequence_01, sequence_02)
        self.assertEqual(self.picking_01.state, 'done')
        self.assertEqual(self.picking_02.state, 'done')
        quant_01 = self.env['stock.quant']._gather(
            self.product_01, self.env.ref('stock.stock_location_stock'))
        quant_02 = self.env['stock.quant']._gather(
            self.product_02, self.env.ref('stock.stock_location_stock'))
        self.assertFalse(sum(quant_01.mapped('quantity')))
        self.assertFalse(sum(quant_02.mapped('quantity')))
        self.assertFalse(self.picking_01.carrier_tracking_ref)
        self.assertFalse(self.picking_02.carrier_tracking_ref)

    def test_check_same_partner_stock_picking_batch(self):
        partner = self.env['res.partner'].create({
            'name': 'Partner test 02',
            'is_company': False,
        })
        self.assertEqual(self.picking_02.partner_id, self.partner)
        self.picking_02.partner_id = partner.id
        self.assertNotEqual(self.picking_02.partner_id, self.partner)
        self.assertNotEqual(
            self.picking_01.partner_id, self.picking_02.partner_id)
        self.assertEqual(self.picking_02.partner_id, partner)
        self.env['stock.quant']._update_available_quantity(
            self.product_01, self.env.ref('stock.stock_location_stock'), 10.0)
        self.env['stock.quant']._update_available_quantity(
            self.product_02, self.env.ref('stock.stock_location_stock'), 10.0)
        self.batch.confirm_picking()
        self.assertEqual(self.picking_01.state, 'assigned')
        self.assertEqual(self.picking_02.state, 'assigned')
        self.picking_01.move_lines.quantity_done = 10
        self.picking_02.move_lines.quantity_done = 10
        with self.assertRaises(exceptions.ValidationError) as result:
            self.batch.done()
        self.assertEqual(
            result.exception.name,
            'Delivery: Different partners in the same group')

    def test_check_same_carrier_stock_picking_batch(self):
        normal_delivery = self.env.ref('delivery.normal_delivery_carrier')
        self.assertEqual(self.picking_02.carrier_id, self.free_delivery)
        self.picking_02.carrier_id = normal_delivery.id
        self.assertNotEqual(self.picking_02.carrier_id, self.free_delivery)
        self.assertNotEqual(
            self.picking_01.carrier_id, self.picking_02.carrier_id)
        self.assertEqual(self.picking_02.carrier_id, normal_delivery)
        self.env['stock.quant']._update_available_quantity(
            self.product_01, self.env.ref('stock.stock_location_stock'), 10.0)
        self.env['stock.quant']._update_available_quantity(
            self.product_02, self.env.ref('stock.stock_location_stock'), 10.0)
        self.batch.confirm_picking()
        self.assertEqual(self.picking_01.state, 'assigned')
        self.assertEqual(self.picking_02.state, 'assigned')
        self.picking_01.move_lines.quantity_done = 10
        self.picking_02.move_lines.quantity_done = 10
        with self.assertRaises(exceptions.ValidationError) as result:
            self.batch.done()
        self.assertEqual(
            result.exception.name,
            'Delivery: Different carriers in the same in group')

    def test_check_sequence_stock_picking(self):
        self.env['stock.quant']._update_available_quantity(
            self.product_01, self.env.ref('stock.stock_location_stock'), 10.0)
        self.env['stock.quant']._update_available_quantity(
            self.product_02, self.env.ref('stock.stock_location_stock'), 10.0)
        self.batch.confirm_picking()
        self.assertEqual(self.picking_01.state, 'assigned')
        self.assertEqual(self.picking_02.state, 'assigned')
        self.picking_01.move_lines.quantity_done = 10
        self.picking_02.move_lines.quantity_done = 10
        picking_type_01 = self.picking_02.picking_type_id or (
            self.picking_02._get_default_picking_type())
        picking_type_01 = self.env['stock.picking.type'].browse(
            picking_type_01.id)
        if picking_type_01:
            sequence_01 = picking_type_01.sequence_id.number_next_actual
        self.batch.done()
        simulate_picking = self.env['stock.picking'].search([
            ('name', '=', self.batch.name),
        ])
        self.assertFalse(simulate_picking)
        picking_type_02 = self.picking_02.picking_type_id or (
            self.picking_02._get_default_picking_type())
        picking_type_02 = self.env['stock.picking.type'].browse(
            picking_type_02.id)
        if picking_type_02:
            sequence_02 = picking_type_02.sequence_id.number_next_actual
        self.assertEqual(sequence_01, sequence_02)
        self.assertEqual(self.picking_01.state, 'done')
        self.assertEqual(self.picking_02.state, 'done')
        quant_01 = self.env['stock.quant']._gather(
            self.product_01, self.env.ref('stock.stock_location_stock'))
        quant_02 = self.env['stock.quant']._gather(
            self.product_02, self.env.ref('stock.stock_location_stock'))
        self.assertFalse(sum(quant_01.mapped('quantity')))
        self.assertFalse(sum(quant_02.mapped('quantity')))

    def test_check_weight_volume_and_number_of_packages(self):
        wizard = self.env['stock.picking.batch.creator'].create({
            'name': 'Test wizard',
        })
        wizard.with_context(
            active_ids=[
                self.picking_03.id, self.picking_04.id]).action_create_batch()
        batch = self.env['stock.picking.batch'].search([
            ('name', '=', 'Test wizard'),
        ])
        self.assertEqual(len(batch), 1)
        self.assertFalse(self.product_03.volume)
        self.assertFalse(self.product_04.volume)
        self.product_03.volume = 0.5
        self.product_04.volume = 0.5
        self.assertEqual(self.product_03.volume, 0.5)
        self.assertEqual(self.product_04.volume, 0.5)
        self.assertEqual(self.product_03.weight, 3)
        self.assertEqual(self.product_04.weight, 2)
        batch_volume = batch.total_volume
        batch_weight = batch.total_weight
        self.assertEqual(self.picking_03.weight, 12)
        self.assertEqual(self.picking_04.weight, 8)
        self.assertEqual(self.picking_03.volume, 2)
        self.assertEqual(self.picking_03.volume, 2)
        self.assertEqual(
            self.picking_03.weight + self.picking_04.weight, batch_weight)
        self.assertEqual(
            self.picking_03.volume + self.picking_04.volume, batch_volume)
        self.assertEqual(batch.total_weight, 20)
        self.assertEqual(batch.total_volume, 4)
        self.assertEqual(batch.number_of_packages, 2)

    def test_check_not_change_carrier_picking_state_not_valid(self):
        self.assertEqual(self.picking_01.carrier_id, self.free_delivery)
        self.assertEqual(self.picking_02.carrier_id, self.free_delivery)
        self.assertEqual(self.batch.carrier_id, self.free_delivery)
        self.env['stock.quant']._update_available_quantity(
            self.product_01, self.env.ref('stock.stock_location_stock'), 10.0)
        self.env['stock.quant']._update_available_quantity(
            self.product_02, self.env.ref('stock.stock_location_stock'), 10.0)
        self.batch.confirm_picking()
        self.assertEqual(self.picking_01.state, 'assigned')
        self.assertEqual(self.picking_02.state, 'assigned')
        self.picking_01.move_lines.quantity_done = 10
        self.picking_02.move_lines.quantity_done = 10
        self.batch.done()
        self.assertEqual(self.batch.state, 'done')
        self.assertEqual(self.picking_01.state, 'done')
        self.assertEqual(self.picking_02.state, 'done')
        self.batch.carrier_id = self.carrier.id
        self.assertEqual(self.batch.carrier_id, self.carrier)
        self.assertNotEqual(self.picking_01.carrier_id, self.carrier)
        self.assertNotEqual(self.picking_02.carrier_id, self.carrier)
        self.assertEqual(self.picking_01.carrier_id, self.free_delivery)
        self.assertEqual(self.picking_02.carrier_id, self.free_delivery)

    def test_create_batch_with_carrier_and_update_carrier(self):
        self.assertTrue(self.picking_01.carrier_id)
        self.assertTrue(self.picking_02.carrier_id)
        self.assertTrue(self.batch.carrier_id)
        self.assertEqual(
            self.picking_01.carrier_id, self.picking_02.carrier_id)
        self.assertEqual(self.batch.carrier_id, self.picking_01.carrier_id)
        self.assertEqual(self.batch.carrier_id, self.picking_02.carrier_id)
        self.assertEqual(self.batch.carrier_id, self.free_delivery)
        self.assertFalse(self.product_01.volume)
        self.assertFalse(self.product_02.volume)
        self.product_01.volume = 1
        self.product_02.volume = 2
        self.assertEqual(self.product_01.volume, 1)
        self.assertEqual(self.product_02.volume, 2)
        self.picking_01.action_calculate_volume()
        self.picking_02.action_calculate_volume()
        self.assertEqual(self.picking_01.weight, 6)
        self.assertEqual(self.picking_01.volume, 2)
        self.assertEqual(self.picking_02.weight, 6)
        self.assertEqual(self.picking_02.volume, 6)
        self.picking_01.action_confirm()
        self.picking_02.action_confirm()
        self.batch.carrier_id = self.carrier.id
        self.batch.onchange_carrier_id()
        self.assertNotEqual(self.batch.carrier_id, self.free_delivery)
        self.assertEqual(self.batch.carrier_id, self.carrier)
        self.assertNotEqual(self.picking_01.carrier_id, self.free_delivery)
        self.assertNotEqual(self.picking_02.carrier_id, self.free_delivery)
        self.assertEqual(self.picking_01.carrier_id, self.carrier)
        self.assertEqual(self.picking_02.carrier_id, self.carrier)

    def test_create_batch_with_wizard_and_update_carrier(self):
        wizard = self.env['stock.picking.batch.creator'].create({
            'name': 'Test wizard',
        })
        wizard.with_context(
            active_ids=[
                self.picking_03.id, self.picking_04.id]).action_create_batch()
        batch = self.env['stock.picking.batch'].search([
            ('name', '=', 'Test wizard'),
        ])
        self.assertEqual(len(batch), 1)
        self.assertEqual(self.picking_03.carrier_id, self.free_delivery)
        self.assertEqual(self.picking_04.carrier_id, self.free_delivery)
        self.assertEqual(batch.carrier_id, self.free_delivery)
        self.assertFalse(self.product_03.volume)
        self.assertFalse(self.product_04.volume)
        self.product_03.volume = 0.5
        self.product_04.volume = 0.5
        self.assertEqual(self.product_03.volume, 0.5)
        self.assertEqual(self.product_04.volume, 0.5)
        self.picking_03.action_calculate_volume()
        self.picking_04.action_calculate_volume()
        self.assertEqual(self.picking_03.weight, 12)
        self.assertEqual(self.picking_03.volume, 2)
        self.assertEqual(self.picking_04.weight, 8)
        self.assertEqual(self.picking_04.volume, 2)
        self.picking_03.action_confirm()
        self.picking_04.action_confirm()
        batch.carrier_id = self.carrier.id
        batch.onchange_carrier_id()
        self.assertNotEqual(batch.carrier_id, self.free_delivery)
        self.assertEqual(batch.carrier_id, self.carrier)
        self.assertNotEqual(self.picking_03.carrier_id, self.free_delivery)
        self.assertNotEqual(self.picking_04.carrier_id, self.free_delivery)
        self.assertEqual(self.picking_03.carrier_id, self.carrier)
        self.assertEqual(self.picking_04.carrier_id, self.carrier)

    def test_create_sale_and_check_info_picking_delivery(self):
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test',
            'standard_price': 5,
            'list_price': 10,
            'volume': 4,
            'weight': 6,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': 1,
                    'price_unit': 15,
                }),
            ],
        })
        self.assertEqual(sale.order_line.product_id.weight, product.weight)
        self.assertEqual(sale.order_line.product_id.volume, product.volume)
        sale.action_confirm()
        picking = sale.picking_ids[0]
        picking.action_assign()
        self.assertEqual(picking.volume, product.volume)
        self.assertEqual(picking.weight, product.weight)
        wizard = self.env['stock.picking.batch.creator'].create({
            'name': 'Test wizard',
        })
        wizard.with_context(
            active_ids=[picking.id]).action_create_batch()
        batch = self.env['stock.picking.batch'].search([
            ('name', '=', 'Test wizard'),
        ])
        self.assertEqual(len(batch), 1)
        self.assertEqual(batch.total_volume, picking.volume)
        self.assertEqual(batch.total_weight, picking.weight)
        self.assertEqual(batch.number_of_packages, picking.number_of_packages)
        self.env['stock.quant']._update_available_quantity(
            product, self.env.ref('stock.stock_location_stock'), 10.0)
        batch.confirm_picking()
        picking.move_lines.quantity_done = 1
        self.assertEqual(batch.total_volume, picking.volume)
        self.assertEqual(batch.total_weight, picking.weight)
        self.assertFalse(batch.shipping_volume)
        self.assertFalse(batch.shipping_weight)
        batch.action_transfer()
        self.assertEqual(batch.total_volume, batch.shipping_volume)
        self.assertEqual(batch.total_weight, batch.shipping_weight)
        self.assertEqual(batch.number_of_packages, picking.number_of_packages)

    def test_check_shipping_volume_and_shipping_weight(self):
        wizard = self.env['stock.picking.batch.creator'].create({
            'name': 'Test wizard',
        })
        wizard.with_context(
            active_ids=[
                self.picking_03.id, self.picking_04.id]).action_create_batch()
        batch = self.env['stock.picking.batch'].search([
            ('name', '=', 'Test wizard'),
        ])
        self.assertEqual(len(batch), 1)
        self.assertFalse(self.product_03.volume)
        self.assertFalse(self.product_04.volume)
        self.product_03.volume = 0.5
        self.product_04.volume = 0.5
        self.assertEqual(self.product_03.volume, 0.5)
        self.assertEqual(self.product_04.volume, 0.5)
        self.assertEqual(self.product_03.weight, 3)
        self.assertEqual(self.product_04.weight, 2)
        self.env['stock.quant']._update_available_quantity(
            self.product_03, self.env.ref('stock.stock_location_stock'), 10.0)
        self.env['stock.quant']._update_available_quantity(
            self.product_04, self.env.ref('stock.stock_location_stock'), 10.0)
        batch.confirm_picking()
        self.picking_03.move_lines.quantity_done = 4
        self.picking_04.move_lines.quantity_done = 4
        batch_volume = batch.total_volume
        batch_weight = batch.total_weight
        self.assertEqual(
            self.picking_03.volume + self.picking_04.volume, batch_volume)
        self.assertEqual(
            self.picking_03.weight + self.picking_04.weight, batch_weight)
        self.assertFalse(batch.shipping_weight)
        self.assertFalse(batch.shipping_volume)
        batch.action_transfer()
        self.assertEqual(self.picking_03.state, 'done')
        self.assertEqual(self.picking_04.state, 'done')
        self.assertEqual(batch.state, 'done')
        self.assertEqual(batch.shipping_volume, batch_volume)
        self.assertEqual(batch.shipping_weight, batch_weight)
        self.product_03.volume = 1
        self.product_04.volume = 1
        self.assertEqual(self.product_03.volume, 1)
        self.assertEqual(self.product_04.volume, 1)
        batch._compute_total_volume()
        batch._compute_total_weight()
        batch_weight_02 = batch.total_volume
        batch_volume_02 = batch.total_weight
        self.assertNotEqual(batch_weight, batch_weight_02)
        self.assertNotEqual(batch_volume, batch_volume_02)
        self.assertNotEqual(batch_volume_02, batch.shipping_volume)
        self.assertNotEqual(batch_weight_02, batch.shipping_weight)
        self.assertEqual(batch_volume, batch.shipping_volume)
        self.assertEqual(batch_weight, batch.shipping_weight)

    def test_check_no_include_cancel_picking_in_calculations(self):
        wizard = self.env['stock.picking.batch.creator'].create({
            'name': 'Test wizard',
        })
        wizard.with_context(
            active_ids=[
                self.picking_03.id, self.picking_04.id]).action_create_batch()
        batch = self.env['stock.picking.batch'].search([
            ('name', '=', 'Test wizard'),
        ])
        self.assertEqual(len(batch), 1)
        self.assertFalse(self.product_03.volume)
        self.assertFalse(self.product_04.volume)
        self.product_03.volume = 0.5
        self.product_04.volume = 0.5
        self.assertEqual(self.product_03.volume, 0.5)
        self.assertEqual(self.product_04.volume, 0.5)
        self.assertEqual(self.product_03.weight, 3)
        self.assertEqual(self.product_04.weight, 2)
        batch.confirm_picking()
        self.picking_03.action_cancel()
        self.assertEqual(self.picking_03.state, 'cancel')
        batch_volume = batch.total_volume
        batch_weight = batch.total_weight
        self.assertNotEqual(
            self.picking_03.weight + self.picking_04.weight, batch_weight)
        self.assertNotEqual(
            self.picking_03.volume + self.picking_04.volume, batch_volume)
        self.assertEqual(self.picking_04.weight, batch_weight)
        self.assertEqual(self.picking_04.volume, batch_volume)

    def test_check_compute_volume_automatic_picking_and_batch(self):
        wizard = self.env['stock.picking.batch.creator'].create({
            'name': 'Test wizard',
        })
        wizard.with_context(
            active_ids=[
                self.picking_03.id, self.picking_04.id]).action_create_batch()
        batch = self.env['stock.picking.batch'].search([
            ('name', '=', 'Test wizard'),
        ])
        self.assertEqual(len(batch), 1)
        self.assertEqual(self.product_03.volume, 0)
        self.assertEqual(self.product_04.volume, 0)
        self.product_03.volume = 1.5
        self.product_04.volume = 3
        self.assertEqual(self.product_03.volume, 1.5)
        self.assertEqual(self.product_04.volume, 3)
        self.assertEqual(self.product_03.weight, 3)
        self.assertEqual(self.product_04.weight, 2)
        batch_volume = batch.total_volume
        batch_weight = batch.total_weight
        self.assertEqual(self.picking_03.volume, 6)
        self.assertEqual(self.picking_04.volume, 12)
        self.assertEqual(batch.total_volume, 18)
        self.assertEqual(self.picking_03.weight, 12)
        self.assertEqual(self.picking_04.weight, 8)
        self.assertEqual(batch.total_weight, 20)
        self.assertEqual(
            self.picking_03.weight + self.picking_04.weight, batch_weight)
        self.assertEqual(
            self.picking_03.volume + self.picking_04.volume, batch_volume)
