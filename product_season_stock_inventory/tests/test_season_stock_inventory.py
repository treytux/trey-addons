# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import openerp.tests.common as common


class TestProductSeasonStockInventory(common.TransactionCase):
    def setUp(self):
        super(TestProductSeasonStockInventory, self).setUp()
        self.winter = self.env['product.season'].create({
            'name': 'Winter'})
        self.product1 = self.env['product.product'].create({
            'name': 'Product for inventory 1',
            'season_id': self.winter.id,
            'type': 'product',
            'default_code': 'PROD1'})
        self.product2 = self.env['product.product'].create({
            'name': 'Product for inventory 2',
            'season_id': self.winter.id,
            'type': 'product',
            'default_code': 'PROD2'})
        self.location = self.env['stock.location'].create({
            'name': 'Inventory tests',
            'usage': 'internal'})
        self.inventory = self.env['stock.inventory'].create({
            'name': 'Product1 inventory',
            'filter': 'season_ids',
            'season_ids': [(6, 0, [self.winter.id])],
            'season_id': self.winter.id,
            'line_ids': [(0, 0, {'product_id': self.product1.id,
                                 'product_uom_id': self.env.ref(
                                     'product.product_uom_unit').id,
                                 'product_qty': 2.0,
                                 'location_id': self.location.id}),
                         (0, 0, {'product_id': self.product2.id,
                                 'product_uom_id': self.env.ref(
                                     'product.product_uom_unit').id,
                                 'product_qty': 4.0,
                                 'location_id': self.location.id})]})
        self.inventory.action_done()

    def test_inventory_season_filter(self):
        inventory = self.inventory
        inventory.prepare_inventory()
        self.assertEqual(len(inventory.line_ids), 2)
        line1 = inventory.line_ids[0]
        self.assertEqual(line1.product_id, self.product1)
        self.assertEqual(line1.theoretical_qty, 2.0)
        self.assertEqual(line1.location_id, self.location)
        line2 = inventory.line_ids[1]
        self.assertEqual(line2.product_id, self.product2)
        self.assertEqual(line2.theoretical_qty, 4.0)
        self.assertEqual(line2.location_id, self.location)
