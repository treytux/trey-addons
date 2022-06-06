###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestProductStockMove(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.location = self.env.ref('stock.stock_location_stock')
        self.inventory = self.env['stock.inventory'].create({
            'name': 'Add products for tests',
            'filter': 'partial',
            'location_id': self.location.id,
            'exhausted': True,
        })
        self.inventory.line_ids.create({
            'inventory_id': self.inventory.id,
            'product_id': self.product.id,
            'product_qty': 10,
            'location_id': self.location.id,
        })

    def test_link_product_without_stock_move(self):
        stock_moves_ids = self.product.get_stock_moves_ids()
        self.assertEqual(len(stock_moves_ids), 0)
        stock_moves_ids = self.product.product_tmpl_id.get_stock_moves_ids()
        self.assertEqual(len(stock_moves_ids), 0)

    def test_link_product_with_multiple_stock_move(self):
        product_test = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product test 2',
            'standard_price': 3,
            'list_price': 6,
        })
        self.inventory.action_start()
        self.inventory._action_done()
        second_inventory = self.env['stock.inventory'].create({
            'name': 'Add products for tests 2',
            'filter': 'partial',
            'location_id': self.location.id,
            'exhausted': True,
        })
        second_inventory.action_start()
        second_inventory.line_ids.create({
            'inventory_id': second_inventory.id,
            'product_id': self.product.id,
            'product_qty': 5,
            'location_id': self.location.id,
        })
        second_inventory.line_ids.create({
            'inventory_id': second_inventory.id,
            'product_id': product_test.id,
            'product_qty': 3,
            'location_id': self.location.id,
        })
        self.assertEqual(len(second_inventory.line_ids), 2)
        second_inventory._action_done()
        stock_moves_ids = self.product.get_stock_moves_ids()
        self.assertEqual(len(stock_moves_ids), 2)
        stock_moves_ids = self.product.product_tmpl_id.get_stock_moves_ids()
        self.assertEqual(len(stock_moves_ids), 2)
        stock_moves_ids = product_test.get_stock_moves_ids()
        self.assertEqual(len(stock_moves_ids), 1)
        stock_moves_ids = product_test.product_tmpl_id.get_stock_moves_ids()
        self.assertEqual(len(stock_moves_ids), 1)

    def test_link_product_with_one_stock_move(self):
        self.inventory.action_start()
        self.inventory._action_done()
        stock_moves_ids = self.product.get_stock_moves_ids()
        self.assertEqual(len(stock_moves_ids), 1)
        stock_moves_ids = self.product.product_tmpl_id.get_stock_moves_ids()
        self.assertEqual(len(stock_moves_ids), 1)
