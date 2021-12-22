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
        inventory = self.env['stock.inventory'].create({
            'name': 'Add products for tests',
            'filter': 'partial',
            'location_id': self.location.id,
            'exhausted': True,
        })
        inventory.action_start()
        inventory.line_ids.create({
            'inventory_id': inventory.id,
            'product_id': self.board.id,
            'product_qty': 1,
            'location_id': self.location.id,
        })
        inventory.line_ids.create({
            'inventory_id': inventory.id,
            'product_id': self.leg.id,
            'product_qty': 12,
            'location_id': self.location.id,
        })
        inventory._action_done()

    def test_product_qty_manufacture(self):
        self.assertEquals(self.board.qty_available, 1)
        self.assertEquals(self.leg.qty_available, 12)
        self.assertEquals(self.table.qty_available, 0)
        self.assertEquals(self.table.qty_manufacture, 1)
        inventory = self.env['stock.inventory'].create({
            'name': 'Add products for tests',
            'filter': 'partial',
            'location_id': self.location.id,
            'exhausted': True,
        })
        inventory.action_start()
        inventory.line_ids.create({
            'inventory_id': inventory.id,
            'product_id': self.board.id,
            'product_qty': 10,
            'location_id': self.location.id,
        })
        inventory._action_done()
        self.assertEquals(self.board.qty_available, 10)
        self.assertEquals(self.leg.qty_available, 12)
        self.assertEquals(self.table.qty_available, 0)
        self.assertEquals(self.table.qty_manufacture, 3)
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
            ]
        })
        table_double = self.table.with_context(bom_id=bom_double.id)
        self.assertEquals(table_double.qty_available, 0)
        self.assertEquals(table_double.qty_manufacture, 1)
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
            ]
        })
        table_double = self.table.with_context(bom_id=bom_x2.id)
        self.assertEquals(self.board.qty_available, 10)
        self.assertEquals(self.leg.qty_available, 12)
        self.assertEquals(table_double.qty_available, 0)
        self.assertEquals(table_double.qty_manufacture, 6)

    def test_product_qty_virtual(self):
        table_virtual = self.table.with_context(
            qty_manufacture_add_to_virtual=True)
        self.assertEquals(self.table.virtual_available, 0)
        self.assertEquals(table_virtual.qty_manufacture, 1)
        self.assertEquals(table_virtual.virtual_available, 1)
        self.assertEquals(self.table.qty_manufacture, 1)
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
            'date_expected': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'name': self.table.name,
            'procure_method': 'make_to_stock',
            'product_uom': self.table.uom_id.id,
            'product_uom_qty': 1.0,
        })
        self.assertEquals(self.table.virtual_available, 0)
        self.assertEquals(table_virtual.virtual_available, 1)
        self.assertEquals(self.table.qty_manufacture, 1)
        picking.action_confirm()
        self.assertEquals(self.table.virtual_available, -1)
        self.assertEquals(table_virtual.virtual_available, 0)
        self.assertEquals(self.table.qty_manufacture, 1)
        inventory = self.env['stock.inventory'].create({
            'name': 'Add products for tests',
            'filter': 'partial',
            'location_id': self.location.id,
            'exhausted': True,
        })
        inventory.action_start()
        inventory.line_ids.create({
            'inventory_id': inventory.id,
            'product_id': self.board.id,
            'product_qty': 10,
            'location_id': self.location.id,
        })
        inventory._action_done()
        self.assertEquals(self.table.virtual_available, -1)
        self.assertEquals(self.table.qty_manufacture, 3)
        self.assertEquals(table_virtual.qty_manufacture, 3)
        self.assertEquals(table_virtual.virtual_available, 2)
