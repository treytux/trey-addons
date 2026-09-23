###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestStockInventoryBarcodeIsbn(TransactionCase):

    def setUp(self):
        super().setUp()

    def test_stock_inventory_barcode_isbn(self):
        inventory = self.env['stock.inventory.barcode.isbn'].create({})
        isbn_1 = '9783161484100'
        isbn_2 = '9780306406157'
        self.assertTrue(inventory.name)
        self.assertEqual(len(inventory.line_ids), 0)
        inventory.read_barcode(isbn_1)
        self.assertEqual(len(inventory.line_ids), 1)
        inventory_line = inventory.line_ids[0]
        self.assertEqual(inventory_line.barcode, isbn_1)
        self.assertEqual(inventory_line.product_qty, 1)
        self.assertEqual(inventory_line.inventory_id, inventory)
        inventory.read_barcode(isbn_2)
        self.assertEqual(len(inventory.line_ids), 2)
        inventory_line_02 = inventory.line_ids[1]
        self.assertEqual(inventory_line_02.barcode, isbn_2)
        self.assertEqual(inventory_line_02.product_qty, 1)
        inventory_line_02.product_qty = 2
        self.assertEqual(inventory_line_02.product_qty, 2)

    def test_create_product_by_isbn(self):
        inventory = self.env['stock.inventory.barcode.isbn'].create({})
        inventory.read_barcode('9780321637130')
        product = inventory.line_ids[0].product_id
        self.assertIn('9780321637130', product.barcode_ids.mapped('name'))
        self.assertEqual(product.name, 'The Art of Computer Programming')
