###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests import common


class TestStockBarcodesRelocateLocation(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env.ref('product.product_product_8')
        self.barcode_product = '123456789A'
        self.barcode_location = 'ABC897'
        self.barcode_location_2 = 'DEF654'
        self.lot = self.env['stock.production.lot'].create({
            'name': self.barcode_product,
            'product_id': self.product.id,
        })
        self.location_test = self.env['stock.location'].create({
            'name': 'Test internal location',
            'usage': 'internal',
            'barcode': self.barcode_location,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': False,
        })
        self.location_test_02 = self.env['stock.location'].create({
            'name': 'Test internal location 2',
            'usage': 'internal',
            'barcode': self.barcode_location_2,
        })

    def create_inventory(self, product, location, qty, lot_id=False):
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
        })
        inventory._action_done()

    def test_relocate_complete_location(self):
        self.create_inventory(
            self.product, self.location_test, 1, lot_id=self.lot.id)
        wizard = self.env['stock.barcodes.relocate.location'].create({})
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertFalse(wizard.location_id)
        self.assertFalse(wizard.location_dest_id)
        wizard.process_barcode(self.barcode_location)
        self.assertEqual(wizard.location_id, self.location_test)
        wizard.process_barcode(self.barcode_location_2)
        self.assertEqual(wizard.location_dest_id, self.location_test_02)
        wizard._compute_line_ids()
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.show_picking_lines()
        wizard._compute_line_ids()
        quants = self.env['stock.quant'].search([
            ('location_id', 'child_of', self.location_test.id),
            ('company_id', '=', self.env.user.company_id.id),
        ])
        self.assertEqual(len(quants), 1)
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertFalse(wizard.picking_id)
        wizard.validate_picking()
        self.assertTrue(wizard.picking_id)
        picking = wizard.picking_id
        self.assertEqual(picking.state, 'draft')

    def test_relocate_error_read_barcode_not_found(self):
        self.create_inventory(
            self.product, self.location_test, 1, lot_id=self.lot.id)
        wizard = self.env['stock.barcodes.relocate.location'].create({})
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertFalse(wizard.location_id)
        self.assertFalse(wizard.location_dest_id)
        barcode_not_found = '9876C'
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.process_barcode(barcode_not_found)
        self.assertEqual(
            result.exception.name,
            'No location found with this barcode %s' % barcode_not_found)

    def test_error_validate_wizard_no_complete_01(self):
        self.create_inventory(
            self.product, self.location_test, 1, lot_id=self.lot.id)
        wizard = self.env['stock.barcodes.relocate.location'].create({})
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertFalse(wizard.location_id)
        self.assertFalse(wizard.location_dest_id)
        wizard.process_barcode(self.barcode_location)
        self.assertTrue(wizard.location_id)
        self.assertFalse(wizard.location_dest_id)
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.show_picking_lines()
        self.assertEqual(
            result.exception.name, 'No destination location asigned')

    def test_error_validate_wizard_no_complete_02(self):
        self.create_inventory(
            self.product, self.location_test, 1, lot_id=self.lot.id)
        wizard = self.env['stock.barcodes.relocate.location'].create({})
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertFalse(wizard.location_id)
        self.assertFalse(wizard.location_dest_id)
        wizard.process_barcode(self.barcode_location)
        self.assertEqual(wizard.location_id, self.location_test)
        wizard.process_barcode(self.barcode_location_2)
        self.assertEqual(wizard.location_dest_id, self.location_test_02)
        wizard.location_id = False
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.show_picking_lines()
        self.assertEqual(result.exception.name, 'No location origin asigned')

    def test_error_validate_picking_same_location_01(self):
        self.create_inventory(
            self.product, self.location_test, 1, lot_id=self.lot.id)
        wizard = self.env['stock.barcodes.relocate.location'].create({})
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertFalse(wizard.location_id)
        self.assertFalse(wizard.location_dest_id)
        wizard.process_barcode(self.barcode_location)
        self.assertEqual(wizard.location_id, self.location_test)
        wizard.process_barcode(self.barcode_location)
        self.assertEqual(wizard.location_id, self.location_test)
        self.assertEqual(wizard.location_id, wizard.location_dest_id)
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.show_picking_lines()
        self.assertEqual(
            result.exception.name,
            'Source and destination location are the same')

    def test_error_validate_picking_same_location_02(self):
        self.create_inventory(
            self.product, self.location_test, 1, lot_id=self.lot.id)
        wizard = self.env['stock.barcodes.relocate.location'].create({})
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertFalse(wizard.location_id)
        self.assertFalse(wizard.location_dest_id)
        wizard.process_barcode(self.barcode_location)
        self.assertEqual(wizard.location_id, self.location_test)
        wizard.process_barcode(self.barcode_location_2)
        self.assertEqual(wizard.location_dest_id, self.location_test_02)
        self.assertNotEqual(wizard.location_id, wizard.location_dest_id)
        wizard.show_picking_lines()
        wizard._compute_line_ids()
        wizard.location_dest_id = self.location_test.id
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.validate_picking()
        self.assertEqual(
            result.exception.name,
            'Source and destination location are the same')

    def test_relocate_location_multiple_products(self):
        self.create_inventory(
            self.product, self.location_test, 1, lot_id=self.lot.id)
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 30,
        })
        lot_id = self.env['stock.production.lot'].create({
            'name': '852A',
            'product_id': product.id,
        })
        self.create_inventory(product, self.location_test, 1, lot_id=lot_id.id)
        wizard = self.env['stock.barcodes.relocate.location'].create({})
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertFalse(wizard.location_id)
        self.assertFalse(wizard.location_dest_id)
        wizard.process_barcode(self.barcode_location)
        wizard.process_barcode(self.barcode_location_2)
        wizard.show_picking_lines()
        wizard._compute_line_ids()
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(wizard.line_ids[0].product_id, self.product)
        self.assertEqual(wizard.line_ids[1].product_id, product)

    def test_check_quants_quantity_reserved(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 40,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.create_inventory(
            self.product, sale.warehouse_id.lot_stock_id, 1,
            lot_id=self.lot.id)
        warehouse_barcode_location = 'ADKJ1283'
        sale.warehouse_id.lot_stock_id.barcode = warehouse_barcode_location
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertTrue(sale.picking_ids[0])
        picking = sale.picking_ids[0]
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        wizard = self.env['stock.barcodes.relocate.location'].create({})
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertFalse(wizard.location_id)
        self.assertFalse(wizard.location_dest_id)
        wizard.process_barcode(warehouse_barcode_location)
        self.assertEqual(wizard.location_id, sale.warehouse_id.lot_stock_id)
        wizard.process_barcode(self.barcode_location)
        self.assertEqual(wizard.location_dest_id, self.location_test)
        wizard.show_picking_lines()
        wizard._compute_line_ids()
        self.assertNotIn(
            self.product.id, wizard.line_ids.mapped('product_id').mapped('id'))

    def test_check_quants_same_product_not_same_lot(self):
        lot_id = self.env['stock.production.lot'].create({
            'name': '852A',
            'product_id': self.product.id,
        })
        self.create_inventory(
            self.product, self.location_test, 1, lot_id=lot_id.id)
        self.create_inventory(
            self.product, self.location_test, 1, lot_id=self.lot.id)
        wizard = self.env['stock.barcodes.relocate.location'].create({})
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertFalse(wizard.location_id)
        self.assertFalse(wizard.location_dest_id)
        wizard.process_barcode(self.barcode_location)
        self.assertEqual(wizard.location_id, self.location_test)
        wizard.process_barcode(self.barcode_location_2)
        self.assertEqual(wizard.location_dest_id, self.location_test_02)
        quants = self.env['stock.quant'].search([
            ('location_id', '=', self.location_test.id),
            ('company_id', '=', self.env.user.company_id.id),
        ])
        self.assertEqual(len(quants), 2)
        wizard.show_picking_lines()
        wizard._compute_line_ids()
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertIn(self.lot, wizard.line_ids.mapped('lot_id'))
        self.assertIn(lot_id, wizard.line_ids.mapped('lot_id'))
        self.assertEqual(wizard.line_ids[0].product_id, self.product)
        self.assertEqual(wizard.line_ids[0].qty, 1)
        self.assertEqual(wizard.line_ids[1].product_id, self.product)
        self.assertEqual(wizard.line_ids[1].qty, 1)
        self.assertFalse(wizard.picking_id)
        wizard.validate_picking()
        self.assertTrue(wizard.picking_id)
        picking_res = wizard.picking_id
        self.assertEqual(picking_res.state, 'draft')
        picking_res.action_confirm()
        self.assertEqual(picking_res.state, 'confirmed')
        picking_res.action_assign()
        self.assertEqual(picking_res.state, 'assigned')
        self.assertIn(
            lot_id.name,
            picking_res.move_line_ids.mapped('lot_id').mapped('name'))
        self.assertIn(
            self.lot.name,
            picking_res.move_line_ids.mapped('lot_id').mapped('name'))
        for move in picking_res.move_line_ids:
            move.qty_done = move.product_uom_qty
        picking_res.action_done()
        self.assertEqual(picking_res.state, 'done')
