###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestCreateDeposit(TransactionCase):

    def setUp(self):
        super().setUp()
        self.supplier = self.env['res.partner'].create({
            'name': 'Test supplier',
            'supplier': True,
        })
        self.customer = self.env['res.partner'].create({
            'name': 'Test customer',
            'customer': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.stock_wh = self.env.ref('stock.warehouse0')
        self.location_customer = self.env.ref('stock.stock_location_customers')
        self.location_stock = self.env.ref('stock.stock_location_stock')
        self.location_a = self.env['stock.location'].create({
            'name': 'Location A',
            'usage': 'internal',
            'location_id': self.location_stock.id,
        })
        self.location_b = self.env['stock.location'].create({
            'name': 'Location B',
            'usage': 'internal',
            'location_id': self.location_stock.id,
        })

    def update_qty_on_hand(self, product, location, new_qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': new_qty,
            'location_id': location.id,
        })
        wizard.change_product_qty()
        self.assertEquals(
            product.with_context(location=location.id).qty_available, new_qty)

    def test_method_fifo(self):
        self.location_stock.removal_strategy_id = self.env.ref(
            'stock.removal_fifo').id
        self.assertEqual(
            self.location_stock.removal_strategy_id.method, 'fifo')
        self.update_qty_on_hand(self.product, self.location_b, 1)
        self.update_qty_on_hand(self.product, self.location_a, 1)
        product_wh = self.product.with_context(location=self.location_stock.id)
        self.assertEquals(product_wh.qty_available, 2)

        picking_out = self.env['stock.picking'].create({
            'partner_id': self.customer.id,
            'picking_type_id': self.stock_wh.out_type_id.id,
            'location_id': self.location_stock.id,
            'location_dest_id': self.location_customer.id,
        })
        move = self.env['stock.move'].create({
            'name': 'Test move out',
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'product_uom': self.product.uom_id.id,
            'picking_id': picking_out.id,
            'location_id': self.location_stock.id,
            'location_dest_id': self.location_customer.id,
        })
        picking_out.action_confirm()
        picking_out.action_assign()
        self.assertEqual(picking_out.state, 'assigned')
        self.assertEqual(move.state, 'assigned')

        move_lines = move.move_line_ids
        self.assertTrue(move_lines)
        location = move_lines.mapped('location_id')
        self.assertEqual(len(location), 1)
        self.assertEqual(location, self.location_b)

        total_reserved = sum(move_lines.mapped('product_uom_qty'))
        self.assertEqual(total_reserved, 1)

    def test_method_location(self):
        self.location_stock.removal_strategy_id = self.env.ref(
            'stock_removal_strategy_location_order.removal_location').id
        self.assertEqual(
            self.location_stock.removal_strategy_id.method, 'location')
        self.update_qty_on_hand(self.product, self.location_b, 1)
        self.update_qty_on_hand(self.product, self.location_a, 1)
        product_wh = self.product.with_context(location=self.location_stock.id)
        self.assertEquals(product_wh.qty_available, 2)

        picking_out = self.env['stock.picking'].create({
            'partner_id': self.customer.id,
            'picking_type_id': self.stock_wh.out_type_id.id,
            'location_id': self.location_stock.id,
            'location_dest_id': self.location_customer.id,
        })
        move = self.env['stock.move'].create({
            'name': 'Test move out',
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'product_uom': self.product.uom_id.id,
            'picking_id': picking_out.id,
            'location_id': self.location_stock.id,
            'location_dest_id': self.location_customer.id,
        })
        picking_out.action_confirm()
        picking_out.action_assign()
        self.assertEqual(picking_out.state, 'assigned')
        self.assertEqual(move.state, 'assigned')

        move_lines = move.move_line_ids
        self.assertTrue(move_lines)
        location = move_lines.mapped('location_id')
        self.assertEqual(len(location), 1)
        self.assertEqual(location, self.location_a)

        total_reserved = sum(move_lines.mapped('product_uom_qty'))
        self.assertEqual(total_reserved, 1)
