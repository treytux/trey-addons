###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestMoveLineUnreserve(TransactionCase):

    def setUp(self):
        super().setUp()
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
        self.update_qty_on_hand(self.product, self.location_stock, 1)
        product_wh = self.product.with_context(location=self.location_stock.id)
        self.assertEquals(product_wh.qty_available, 1)
        picking_1 = self.env['stock.picking'].create({
            'picking_type_id': self.stock_wh.out_type_id.id,
            'location_id': self.location_stock.id,
            'location_dest_id': self.location_customer.id,
        })
        self.env['stock.move'].create({
            'name': 'Test move out',
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'product_uom': self.product.uom_id.id,
            'picking_id': picking_1.id,
            'location_id': self.location_stock.id,
            'location_dest_id': self.location_customer.id,
        })
        picking_1.action_confirm()
        picking_1.action_assign()
        self.assertEqual(picking_1.state, 'assigned')
        self.assertEqual(picking_1.move_lines.state, 'assigned')
        picking_2 = self.env['stock.picking'].create({
            'picking_type_id': self.stock_wh.out_type_id.id,
            'location_id': self.location_stock.id,
            'location_dest_id': self.location_customer.id,
        })
        self.env['stock.move'].create({
            'name': 'Test move out',
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'product_uom': self.product.uom_id.id,
            'picking_id': picking_2.id,
            'location_id': self.location_stock.id,
            'location_dest_id': self.location_customer.id,
        })
        picking_2.action_confirm()
        picking_2.action_assign()
        self.assertEqual(picking_2.state, 'confirmed')
        self.assertEqual(picking_2.move_lines.state, 'confirmed')

        def get_reserved(picking):
            return sum(picking.move_line_ids.mapped('product_uom_qty'))

        self.assertEqual(get_reserved(picking_1), 1)
        self.assertEqual(get_reserved(picking_2), 0)
        picking_1.move_lines.unreserve_stock_line()
        self.assertEqual(get_reserved(picking_1), 0)
        self.assertEqual(get_reserved(picking_2), 0)
        self.assertEqual(picking_1.state, 'confirmed')
        self.assertEqual(picking_1.move_lines.state, 'confirmed')
        picking_2.action_assign()
        self.assertEqual(get_reserved(picking_1), 0)
        self.assertEqual(get_reserved(picking_2), 1)
        self.assertEqual(picking_2.state, 'assigned')
        self.assertEqual(picking_2.move_lines.state, 'assigned')
