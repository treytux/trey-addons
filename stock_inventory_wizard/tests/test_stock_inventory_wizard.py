###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestStockInventoryWizard(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.product_01 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 1',
            'standard_price': 10,
            'list_price': 100,
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 2',
            'standard_price': 10,
            'list_price': 100,
        })

    def test_create_stock_inventory_one_product(self):
        wizard = self.env['stock.inventory.product'].with_context(
            active_ids=self.product_01.id).create({
                'name': 'Wizard test',
            })
        self.assertEqual(
            wizard.location_id.id,
            self.env['stock.inventory']._default_location_id())
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(wizard.line_ids[0].wizard_id, wizard)
        self.assertEqual(wizard.line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.line_ids[0].barcode, self.product_01.barcode)
        self.assertEqual(
            wizard.line_ids[0].theoretical_available,
            self.product_01.with_context(
                location=wizard.location_id.id).qty_available)
        self.assertEqual(
            wizard.line_ids[0].qty_available, 0)
        res = wizard.button_create_stock_inventory()
        self.assertEqual(res['view_mode'], 'form')
        self.assertEqual(res['view_type'], 'form')
        self.assertEqual(
            res['view_id'], self.env.ref('stock.view_inventory_form').id)
        inventory = self.env['stock.inventory'].browse(res['res_id'])
        self.assertEqual(inventory.state, 'draft')

    def test_create_stock_inventory_multiple_products(self):
        wizard = self.env['stock.inventory.product'].with_context(
            active_ids=[self.product_01.id, self.product_02.id]).create({
                'name': 'Wizard test',
            })
        self.assertEqual(
            wizard.location_id.id,
            self.env['stock.inventory']._default_location_id())
        self.assertEqual(
            wizard.line_ids[0].theoretical_available,
            self.product_01.with_context(
                location=wizard.location_id.id).qty_available)
        self.assertEqual(
            wizard.line_ids[1].theoretical_available,
            self.product_02.with_context(
                location=wizard.location_id.id).qty_available)
        self.assertEqual(
            wizard.line_ids[0].qty_available, 0)
        self.assertEqual(
            wizard.line_ids[1].qty_available, 0)
        self.assertEqual(len(wizard.line_ids), 2)
        res = wizard.button_create_stock_inventory()
        inventory = self.env['stock.inventory'].browse(res['res_id'])
        self.assertEqual(len(inventory.line_ids), 2)
        self.assertEqual(inventory.state, 'draft')

    def test_create_stock_inventory_change_location(self):
        wizard = self.env['stock.inventory.product'].with_context(
            active_ids=self.product_01.ids).create({
                'name': 'Wizard test',
            })
        self.assertEqual(
            wizard.location_id.id,
            self.env['stock.inventory']._default_location_id())
        location = self.env.ref('stock.stock_location_shop0')
        wizard.location_id = location.id
        self.assertNotEqual(
            wizard.location_id.id,
            self.env['stock.inventory']._default_location_id())
        self.assertEqual(wizard.location_id, location)
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(
            wizard.line_ids[0].theoretical_available,
            self.product_01.with_context(
                location=wizard.location_id.id).qty_available)
        self.assertEqual(
            wizard.line_ids[0].qty_available, 0)
        res = wizard.button_create_stock_inventory()
        inventory = self.env['stock.inventory'].browse(res['res_id'])
        self.assertEqual(len(inventory.line_ids), 1)
        self.assertEqual(inventory.state, 'draft')

    def test_different_theoretical_qty_in_different_location_and_confirm(self):
        location_01 = self.env.ref('stock.stock_location_stock')
        location_02 = self.env.ref('stock.stock_location_shop0')
        inventory_01 = self.env['stock.inventory'].create({
            'name': 'Add products for tests in location 01',
            'filter': 'partial',
            'location_id': location_01.id,
            'exhausted': True,
        })
        inventory_01.action_start()
        inventory_01.line_ids.create({
            'inventory_id': inventory_01.id,
            'product_id': self.product_01.id,
            'product_qty': 10,
            'location_id': location_01.id,
        })
        inventory_01._action_done()
        inventory_02 = self.env['stock.inventory'].create({
            'name': 'Add products for tests in location 02',
            'filter': 'partial',
            'location_id': location_02.id,
            'exhausted': True,
        })
        inventory_02.action_start()
        inventory_02.line_ids.create({
            'inventory_id': inventory_02.id,
            'product_id': self.product_01.id,
            'product_qty': 20,
            'location_id': location_02.id,
        })
        inventory_02._action_done()
        self.assertNotEqual(
            self.product_01.with_context(
                location=location_01.id).qty_available,
            self.product_01.with_context(
                location=location_02.id).qty_available)
        self.assertEqual(
            inventory_01.line_ids[0].product_qty,
            self.product_01.with_context(
                location=location_01.id).qty_available)
        self.assertEqual(
            inventory_02.line_ids[0].product_qty,
            self.product_01.with_context(
                location=location_02.id).qty_available)
        wizard = self.env['stock.inventory.product'].with_context(
            active_ids=self.product_01.ids).create({
                'name': 'Wizard test',
            })
        self.assertEqual(wizard.location_id.id, location_01.id)
        self.assertEqual(
            wizard.line_ids[0].theoretical_available,
            self.product_01.with_context(
                location=location_01.id).qty_available)
        wizard.location_id = location_02.id
        self.assertEqual(wizard.location_id, location_02)
        self.assertEqual(
            wizard.line_ids[0].theoretical_available,
            self.product_01.with_context(
                location=location_02.id).qty_available)
        wizard.line_ids[0].qty_available = 15
        res = wizard.button_create_stock_inventory()
        inventory = self.env['stock.inventory'].browse(res['res_id'])
        self.assertEqual(len(inventory.line_ids), 1)
        self.assertEqual(inventory.state, 'draft')
        inventory.action_start()
        inventory._action_done()
        self.assertEqual(inventory.state, 'done')
        wizard = self.env['stock.inventory.product'].with_context(
            active_ids=self.product_01.ids).create({
                'name': 'Wizard test 2',
            })
        self.assertEqual(wizard.location_id, location_01)
        wizard.location_id = location_02.id
        self.assertEqual(wizard.location_id, location_02)
        self.assertEqual(
            self.product_01.with_context(
                location=location_02.id).qty_available, 15)
        self.assertEqual(
            wizard.line_ids[0].theoretical_available,
            self.product_01.with_context(
                location=location_02.id).qty_available)
