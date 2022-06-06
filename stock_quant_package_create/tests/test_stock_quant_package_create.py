###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestStockQuantPackageCreate(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env.ref('product.product_product_8')
        self.product.packaging_ids = [
            (0, 0, {
                'name': 'Box 12',
                'qty': 12,
                'barcode': '1234567890123',
            }),
        ]
        self.lot = self.env['stock.production.lot'].create({
            'product_id': self.product.id,
        })

    def create_inventory(self, product, location, qty, lot_id=False,
                         package_id=False):
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
            'product_qty': qty,
            'location_id': location.id,
            'prod_lot_id': lot_id,
            'package_id': package_id,
        })
        inventory._action_done()

    def test_simple_operation(self):
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product, location, 10, lot_id=self.lot.id)
        wizard = self.env['stock.quant.package.create'].create({
            'name': 'PACKAGE-CREATE-TEST',
            'location_id': location.id,
            'line_ids': [
                (0, 0, {
                    'location_id': location.id,
                    'product_id': self.product.id,
                    'lot_id': self.lot.id,
                    'product_qty': 10,
                }),
            ]
        })
        self.assertEquals(wizard.line_ids[0].available_qty, 10)
        wizard.action_confirm()
        pack = self.env['stock.quant.package'].search([
            ('name', '=', 'PACKAGE-CREATE-TEST')])
        self.assertTrue(pack)
        picking = self.env['stock.picking'].search([
            ('origin', 'like', 'PACKAGE-CREATE-TEST')])
        self.assertTrue(picking.state, 'done')

    def test_without_stock(self):
        location = self.env.ref('stock.stock_location_stock')
        self.assertEqual(self.product.type, 'product')
        wizard = self.env['stock.quant.package.create'].create({
            'name': 'PACKAGE-CREATE-TEST',
            'location_id': location.id,
            'line_ids': [
                (0, 0, {
                    'location_id': location.id,
                    'product_id': self.product.id,
                    'lot_id': self.lot.id,
                    'product_qty': 10,
                }),
            ]
        })
        self.assertEquals(wizard.line_ids.available_qty, 0)
        with self.assertRaises(exceptions.ValidationError):
            wizard.action_confirm()
