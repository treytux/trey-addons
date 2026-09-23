###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from odoo.tests.common import TransactionCase


class TestProductQtyManufacture(TransactionCase):
    def setUp(self):
        super().setUp()
        self.table = self.env['product.product'].create({
            'name': 'Test Table',
            'type': 'product',
        })
        self.board = self.env['product.product'].create({
            'name': 'Test Board',
            'type': 'product',
        })
        self.leg = self.env['product.product'].create({
            'name': 'Test Leg',
            'type': 'product',
        })
        self.bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.table.product_tmpl_id.id,
            'product_id': self.table.id,
            'product_uom_id': self.table.uom_id.id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.board.id,
                    'product_qty': 1,
                    'product_uom_id': self.board.uom_id.id,
                }),
                (0, 0, {
                    'product_id': self.leg.id,
                    'product_qty': 4,
                    'product_uom_id': self.leg.uom_id.id,
                })
            ]
        })
        self.table.stock_bom_id = self.bom.id
        self.location = self.env.ref('stock.stock_location_stock')
        self.env['stock.quant']._update_available_quantity(
            self.board,
            self.location, 1.0
        )
        self.env['stock.quant']._update_available_quantity(
            self.leg,
            self.location, 12.0
        )

    def test_product_qty_manufacture(self):
        self.assertEqual(self.board.qty_available, 1)
        self.assertEqual(self.leg.qty_available, 12)
        self.assertEqual(self.table.qty_available, 0)
        self.assertEqual(self.table.qty_manufacture, 1)
        self.env['stock.quant']._update_available_quantity(
            self.board,
            self.location, 9.0
        )
        self.board.invalidate_model(['qty_available'])
        self.assertEqual(self.board.qty_available, 10)
        self.assertEqual(self.leg.qty_available, 12)
        self.assertEqual(self.table.qty_available, 0)
        self.assertEqual(self.table.qty_manufacture, 3)
        bom_double = self.env['mrp.bom'].create({
            'product_tmpl_id': self.table.product_tmpl_id.id,
            'product_id': self.table.id,
            'product_uom_id': self.table.uom_id.id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.board.id,
                    'product_qty': 2,
                    'product_uom_id': self.board.uom_id.id,
                }),
                (0, 0, {
                    'product_id': self.leg.id,
                    'product_qty': 8,
                    'product_uom_id': self.leg.uom_id.id,
                })
            ],
        })
        table_double = self.table.with_context(bom_id=bom_double.id)
        self.table.invalidate_model(['qty_available'])
        self.assertEqual(table_double.qty_available, 0)
        self.assertEqual(table_double.qty_manufacture, 1)
        bom_x2 = self.env['mrp.bom'].create({
            'product_tmpl_id': self.table.product_tmpl_id.id,
            'product_id': self.table.id,
            'product_uom_id': self.table.uom_id.id,
            'product_qty': 2,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.board.id,
                    'product_qty': 1,
                    'product_uom_id': self.board.uom_id.id,
                }),
                (0, 0, {
                    'product_id': self.leg.id,
                    'product_qty': 4,
                    'product_uom_id': self.leg.uom_id.id,
                })
            ],
        })
        table_double = self.table.with_context(bom_id=bom_x2.id)
        self.table.invalidate_model(['qty_available'])
        self.assertEqual(self.board.qty_available, 10)
        self.assertEqual(self.leg.qty_available, 12)
        self.assertEqual(table_double.qty_available, 0)
        self.assertEqual(table_double.qty_manufacture, 6)

    def test_product_qty_virtual(self):
        table_virtual = self.table.with_context(
            qty_manufacture_add_to_virtual=True)
        self.assertEqual(self.table.virtual_available, 0)
        self.assertEqual(self.table.free_qty, 0)
        self.assertEqual(self.table.qty_manufacture, 1)
        table_virtual.invalidate_model(['virtual_available', 'free_qty'])
        self.assertEqual(table_virtual.qty_manufacture, 1)
        self.assertEqual(table_virtual.virtual_available, 1)
        self.assertEqual(table_virtual.free_qty, 1)
        location_dest = self.env.ref('stock.stock_location_customers')
        outgoing_picking_type = self.env.ref('stock.picking_type_out')
        picking = self.env['stock.picking'].create({
            'picking_type_id': outgoing_picking_type.id,
            'move_type': 'direct',
            'location_id': self.location.id,
            'location_dest_id': location_dest.id,
        })
        self.env['stock.move'].create({
            'picking_id': picking.id,
            'product_id': self.table.id,
            'location_id': self.location.id,
            'location_dest_id': location_dest.id,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'name': self.table.name,
            'procure_method': 'make_to_stock',
            'product_uom': self.table.uom_id.id,
            'product_uom_qty': 1.0,
        })
        self.assertEqual(self.table.virtual_available, 0)
        self.assertEqual(self.table.free_qty, 0)
        table_virtual.invalidate_model(['virtual_available', 'free_qty'])
        self.assertEqual(table_virtual.virtual_available, 1)
        self.assertEqual(table_virtual.free_qty, 1)
        self.assertEqual(self.table.qty_manufacture, 1)
        picking.action_confirm()
        self.assertEqual(self.table.virtual_available, -1)
        table_virtual.invalidate_model(['virtual_available', 'free_qty'])
        self.assertEqual(table_virtual.virtual_available, 0)
        self.assertEqual(table_virtual.free_qty, 1)
        self.assertEqual(self.table.qty_manufacture, 1)
        self.env['stock.quant']._update_available_quantity(
            self.board,
            self.location, 9.0
        )
        self.board.invalidate_model(['qty_available'])
        self.table.invalidate_model(['virtual_available', 'free_qty'])
        self.assertEqual(self.table.virtual_available, -1)
        self.assertEqual(self.table.free_qty, 0)
        self.table.invalidate_model(['qty_manufacture'])
        self.assertEqual(self.table.qty_manufacture, 3)
        table_virtual.invalidate_model(['virtual_available', 'free_qty'])
        self.assertEqual(table_virtual.qty_manufacture, 3)
        table_virtual.invalidate_model(['qty_manufacture'])
        self.assertEqual(table_virtual.virtual_available, 2)
        self.assertEqual(table_virtual.free_qty, 3)
