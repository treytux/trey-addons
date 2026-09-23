###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import time

from odoo.tests import common


class TestStockInventoryWizard(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 1',
            'standard_price': 1,
            'list_price': 100,
            'cost_method': 'fifo',
        })

    def _create_picking(self, in_or_out, product, qty, price_unit=None):
        if in_or_out == 'in':
            assert price_unit, 'You must assign price_unit for in moves!'
            location_src = self.env.ref('stock.stock_location_suppliers')
            location_dst = self.env.ref('stock.stock_location_stock')
            sign_price = 1
        elif in_or_out == 'out':
            assert not price_unit, (
                'You must not assign price_unit for out moves!')
            location_src = self.env.ref('stock.stock_location_stock')
            location_dst = self.env.ref('stock.stock_location_customers')
            sign_price = -1
        else:
            assert True, ('You must set type in or out for create picking')
        picking_type = self.env.ref(f'stock.picking_type_{in_or_out}')
        data_move_lines = {
            'product_id': product.id,
            'name': product.name,
            'product_uom': product.uom_id.id,
            'product_uom_qty': qty,
            'procure_method': 'make_to_stock',
        }
        if in_or_out == 'in':
            data_move_lines.update({
                'price_unit': sign_price * price_unit,
                'value': sign_price * qty * price_unit,
            })
        picking = self.env['stock.picking'].create({
            'location_id': location_src.id,
            'location_dest_id': location_dst.id,
            'picking_type_id': picking_type.id,
            'move_lines': [
                (0, 0, data_move_lines),
            ],
        })
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        time.sleep(1)
        return picking

    def _create_inventory(self, product, qty):
        location = self.env.ref('stock.stock_location_stock')
        inventory = self.env['stock.inventory'].create({
            'name': 'Add products for tests in location 01',
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
        })
        inventory._action_done()
        return inventory

    def test_create_inventory(self):
        inventory = self._create_inventory(self.product, 10)
        self.assertEquals(self.product.standard_price, 1)
        self.assertEquals(inventory.move_ids.price_unit, 1)
        self.assertEquals(inventory.move_ids.value, 10)

    def test_create_inventory_with_several_picking_in(self):
        self._create_picking('in', self.product, 1, price_unit=250)
        self._create_picking('in', self.product, 1, price_unit=500)
        inventory = self._create_inventory(self.product, 12)
        self.assertEquals(inventory.move_ids.product_uom_qty, 10)
        self.assertEquals(inventory.move_ids.price_unit, 500)
        self.assertEquals(inventory.move_ids.value, 5000)
        self._create_picking('in', self.product, 1, price_unit=750)
        inventory = self._create_inventory(self.product, 23)
        self.assertEquals(inventory.move_ids.product_uom_qty, 10)
        self.assertEquals(inventory.move_ids.price_unit, 750)
        self.assertEquals(inventory.move_ids.value, 7500)
