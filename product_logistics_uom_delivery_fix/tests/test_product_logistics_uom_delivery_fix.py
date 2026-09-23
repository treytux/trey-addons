##############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
##############################################################################
from odoo.tests.common import TransactionCase


class TestProductLogisticsUomDeliveryFix(TransactionCase):

    def setUp(self):
        super().setUp()
        self.gram_uom = self.env.ref('uom.product_uom_gram')
        self.kg_uom = self.env.ref('uom.product_uom_kgm')
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.customer_location = self.env.ref('stock.stock_location_customers')
        self.product = self.env['product.product'].create({
            'name': 'Weighted product',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
            'weight': 674.0,
            'weight_uom_id': self.gram_uom.id,
        })
        self.product_kg = self.env['product.product'].create({
            'name': 'Weighted product kg',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
            'weight': 2.0,
            'weight_uom_id': self.kg_uom.id,
        })
        self.env['stock.quant']._update_available_quantity(
            self.product, self.stock_location, 10.0)
        self.env['stock.quant']._update_available_quantity(
            self.product_kg, self.stock_location, 10.0)

    def test_move_weight_is_converted_to_picking_uom(self):
        picking = self.env['stock.picking'].create({
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
        })
        move = self.env['stock.move'].create({
            'name': self.product.name,
            'product_id': self.product.id,
            'product_uom_qty': 2.0,
            'product_uom': self.product.uom_id.id,
            'picking_id': picking.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
        })
        self.assertEqual(picking.weight_uom_id, self.kg_uom)
        self.assertEqual(move.weight, 1.35)
        self.assertEqual(picking.weight, 1.35)

    def test_bulk_weight_is_converted_to_picking_uom(self):
        picking = self.env['stock.picking'].create({
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
        })
        move = self.env['stock.move'].create({
            'name': self.product.name,
            'product_id': self.product.id,
            'product_uom_qty': 2.0,
            'product_uom': self.product.uom_id.id,
            'picking_id': picking.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
        })
        move._action_confirm()
        move._action_assign()
        self.assertTrue(move.move_line_ids)
        move.move_line_ids.write({
            'qty_done': 2.0,
        })
        picking._compute_bulk_weight()
        self.assertEqual(picking.weight_bulk, 1.348)

    def test_move_weight_with_different_line_uom(self):
        product = self.env['product.product'].create({
            'name': 'Weighted product line uom',
            'type': 'product',
            'categ_id': self.env.ref('product.product_category_all').id,
            'uom_id': self.kg_uom.id,
            'uom_po_id': self.kg_uom.id,
            'weight': 674.0,
            'weight_uom_id': self.gram_uom.id,
        })
        picking = self.env['stock.picking'].create({
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
        })
        move = self.env['stock.move'].create({
            'name': product.name,
            'product_id': product.id,
            'product_uom_qty': 500.0,
            'product_uom': self.gram_uom.id,
            'picking_id': picking.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
        })
        self.assertEqual(move.product_qty, 0.5)
        self.assertEqual(move.weight, 0.34)
        self.assertEqual(picking.weight, 0.34)

    def test_picking_weight_with_gram_and_kg_lines(self):
        picking = self.env['stock.picking'].create({
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
        })
        move_gram = self.env['stock.move'].create({
            'name': self.product.name,
            'product_id': self.product.id,
            'product_uom_qty': 2.0,
            'product_uom': self.product.uom_id.id,
            'picking_id': picking.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
        })
        move_kg = self.env['stock.move'].create({
            'name': self.product_kg.name,
            'product_id': self.product_kg.id,
            'product_uom_qty': 3.0,
            'product_uom': self.product_kg.uom_id.id,
            'picking_id': picking.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
        })
        self.assertEqual(move_gram.weight, 1.35)
        self.assertEqual(move_kg.weight, 6.0)
        self.assertEqual(picking.weight, 7.35)
