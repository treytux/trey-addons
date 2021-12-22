###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductLastInventory(TransactionCase):

    def test_inventory(self):
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.assertFalse(product.last_inventory)
        location = self.env.ref('stock.stock_location_stock')
        inventory = self.env['stock.inventory'].create({
            'name': 'Add products for tests',
            'filter': 'partial',
            'location_id': location.id,
            'exhausted': True,
        })
        inventory.action_start()
        inventory.line_ids.create({
            'inventory_id': inventory.id,
            'product_id': product.id,
            'product_qty': 10,
            'location_id': location.id,
        })
        inventory._action_done()
        self.assertEquals(product.last_inventory, inventory.move_ids[0].date)
