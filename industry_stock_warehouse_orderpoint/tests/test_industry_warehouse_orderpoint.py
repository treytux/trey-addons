###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)


class TestIndustryWarehouseOrderpoint(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product1 = self.env['product.template'].create({
            'name': 'Test Product',
            'purchase_method': 'purchase',
            'type': 'product',
            'standard_price': 10.00,
            'list_price': 100.00,
        })
        self.rule = self.env['stock.warehouse.orderpoint'].create({
            'warehouse_id': self.warehouse_1.id,
            'location_id': self.warehouse_1.lot_stock_id.id,
            'product_id': self.product1.id,
            'product_min_qty': 25.00,
            'product_max_qty': 50.00,
            'product_min_qty_year': 50.00,
        })
        self.stock_location = self.env.ref('stock.stock_location_stock')

    def create_initial_inventory(self):
        self.env['stock.quant']._update_available_quantity(
            self.product1, self.stock_location, 25)

    def test_product_suggested_qty(self):
        self.create_initial_inventory()
        self.assertEqual(
            self.env['stock.quant']._get_available_quantity(
                self.product1, self.stock_location), 25.0)
