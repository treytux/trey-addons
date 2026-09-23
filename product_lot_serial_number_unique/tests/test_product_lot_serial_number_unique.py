###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class ProductLotSerialNumberUnique(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product_1 = self.env['product.product'].create({
            'name': 'Producto_1',
            'type': 'product',
            'tracking': 'serial',
        })
        self.product_2 = self.env['product.product'].create({
            'name': 'Producto_2',
            'type': 'product',
            'tracking': 'serial',
        })

    def test_diferent_product_unique_serial(self):
        lot_1 = self.env['stock.production.lot'].create({
            'name': '123456',
            'product_id': self.product_1.id,
        })
        self.assertTrue(lot_1)
        self.assertEquals(lot_1.name, '123456')
        with self.assertRaises(ValidationError) as result:
            self.env['stock.production.lot'].create({
                'name': '123456',
                'product_id': self.product_2.id,
            })
        self.assertEquals(
            'This Lot/Serial number already exists in other product!',
            result.exception.name)

    def test_diferent_product_diferent_serial(self):
        lot_1 = self.env['stock.production.lot'].create({
            'name': '123456',
            'product_id': self.product_1.id,
        })
        lot_2 = self.env['stock.production.lot'].create({
            'name': '456789',
            'product_id': self.product_2.id,
        })
        self.assertTrue(lot_1)
        self.assertEquals(lot_1.name, '123456')
        self.assertTrue(lot_2)
        self.assertEquals(lot_2.name, '456789')
