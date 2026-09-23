###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class ProductLotSerialNumberOnlyOneQty(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'name': 'Product TEST',
            'type': 'product',
            'tracking': 'serial',
        })

    def test_add_multiple_lines_by_inventory(self):
        def create_inventory(location, lot, qty):
            inventory = self.env['stock.inventory'].create({
                'name': 'Add products for tests',
                'filter': 'partial',
                'location_id': location.id,
                'exhausted': True,
            })
            inventory.action_start()
            inventory.line_ids.create({
                'inventory_id': inventory.id,
                'product_id': lot.product_id.id,
                'product_qty': qty,
                'location_id': location.id,
                'prod_lot_id': lot.id,
            })
            inventory._action_done()

        def get_stock(location, lot):
            product = self.product.with_context(
                lot_id=lot.id, location=location.id)
            return product.qty_available

        self.assertEquals(self.product.tracking, 'serial')
        lot = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product.id,
        })
        location = self.env['stock.location'].create({
            'name': 'Test location',
            'usage': 'internal',
        })
        stock_location = self.env.ref('stock.stock_location_stock')
        create_inventory(stock_location, lot, 1)
        self.assertEquals(get_stock(stock_location, lot), 1)
        with self.assertRaises(ValidationError) as result:
            create_inventory(location, lot, 1)
        self.assertIn(
            'is serial number tracked, and it is not possible',
            result.exception.name)
        self.assertEquals(get_stock(location, lot), 0)
        self.assertEquals(get_stock(stock_location, lot), 1)
        create_inventory(stock_location, lot, 0)
        self.assertEquals(get_stock(location, lot), 0)
        self.assertEquals(get_stock(stock_location, lot), 0)

    def test_add_multiple_lines_by_inventory_with_tracking_lot(self):
        def create_inventory(location, lot, qty):
            inventory = self.env['stock.inventory'].create({
                'name': 'Add products for tests',
                'filter': 'partial',
                'location_id': location.id,
                'exhausted': True,
            })
            inventory.action_start()
            inventory.line_ids.create({
                'inventory_id': inventory.id,
                'product_id': lot.product_id.id,
                'product_qty': qty,
                'location_id': location.id,
                'prod_lot_id': lot.id,
            })
            inventory._action_done()

        def get_stock(location, lot):
            product = self.product.with_context(
                lot_id=lot.id, location=location.id)
            return product.qty_available

        self.product.tracking = 'lot'
        self.assertEquals(self.product.tracking, 'lot')
        lot = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product.id,
        })
        location = self.env['stock.location'].create({
            'name': 'Test location',
            'usage': 'internal',
        })
        stock_location = self.env.ref('stock.stock_location_stock')
        create_inventory(stock_location, lot, 1)
        self.assertEquals(get_stock(stock_location, lot), 1)
        create_inventory(location, lot, 1)
        self.assertEquals(get_stock(location, lot), 1)
        self.assertEquals(get_stock(stock_location, lot), 1)
        create_inventory(location, lot, 0)
        self.assertEquals(get_stock(location, lot), 0)
        self.assertEquals(get_stock(stock_location, lot), 1)
        create_inventory(stock_location, lot, 0)
        self.assertEquals(get_stock(location, lot), 0)
        self.assertEquals(get_stock(stock_location, lot), 0)

    def test_add_multiple_lines_by_picking(self):
        stock_location = self.env.ref('stock.stock_location_stock')
        supplier_location = self.env.ref('stock.stock_location_suppliers')
        picking = self.env['stock.picking'].create({
            'location_id': supplier_location.id,
            'location_dest_id': stock_location.id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_uom': self.product.uom_id.id,
                    'product_uom_qty': 1,
                    'procure_method': 'make_to_stock',
                }),
            ],
        })
        picking.action_confirm()
        picking.action_assign()
        lot = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product.id,
        })
        picking.move_line_ids[0].lot_id = lot.id
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()

        def get_stock(location, lot):
            product = self.product.with_context(
                lot_id=lot.id, location=location.id)
            return product.qty_available

        self.assertEquals(get_stock(stock_location, lot), 1)
        picking = self.env['stock.picking'].create({
            'location_id': supplier_location.id,
            'location_dest_id': stock_location.id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_uom': self.product.uom_id.id,
                    'product_uom_qty': 1,
                    'procure_method': 'make_to_stock',
                }),
            ],
        })
        picking.action_confirm()
        picking.action_assign()
        picking.move_line_ids[0].lot_id = lot.id
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        with self.assertRaises(ValidationError) as result:
            picking.action_done()
        self.assertIn(
            'is serial number tracked, and it is not possible',
            result.exception.name)
