###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests import common


class TestStockBarcodesInternalTransfers(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env.ref('product.product_product_8')
        self.barcode_product = '123456789A'
        self.barcode_location = 'ABC987'
        self.barcode_sublocation = 'EFG654'
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

    def test_simple_check_barcodes_internal_transfers(self):
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product, location, 1, lot_id=self.lot.id)
        wizard = self.env['stock.barcodes.internal.transfers'].create({})
        wizard._origin = wizard
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertFalse(wizard.location_dest_id)
        wizard.identify_barcode(self.barcode_product)
        wizard._compute_line_ids()
        self.assertEqual(len(wizard.line_ids), 1)
        wizard.identify_barcode(self.barcode_location)
        wizard._compute_line_ids()
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertTrue(wizard.location_dest_id)
        self.assertEqual(wizard.location_dest_id, self.location_test)
        line = wizard.line_ids[0]
        self.assertEqual(line.wizard_id, wizard)
        self.assertEqual(line.barcode, self.barcode_product)
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.lot_id, self.lot)
        self.assertEqual(line.location_id, location)
        self.assertEqual(line.location_dest_id, self.location_test)
        self.assertEqual(line.qty, 1)

    def test_barcodes_internal_transfers_sublocation(self):
        location = self.env.ref('stock.stock_location_stock')
        sublocation_test = self.env['stock.location'].create({
            'name': 'Test internal sublocation',
            'usage': 'internal',
            'barcode': self.barcode_sublocation,
            'location_id': location.id,
        })
        self.assertIn(sublocation_test, location.child_ids)
        self.assertEqual(sublocation_test.location_id, location)
        self.create_inventory(self.product, location, 1, lot_id=self.lot.id)
        wizard = self.env['stock.barcodes.internal.transfers'].create({})
        wizard._origin = wizard
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertFalse(wizard.location_dest_id)
        wizard.identify_barcode(self.barcode_product)
        wizard._compute_line_ids()
        self.assertEqual(len(wizard.line_ids), 1)
        wizard.identify_barcode(self.barcode_location)
        wizard._compute_line_ids()
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertTrue(wizard.location_dest_id)
        self.assertEqual(wizard.location_dest_id, self.location_test)
        line = wizard.line_ids[0]
        self.assertEqual(line.wizard_id, wizard)
        self.assertEqual(line.barcode, self.barcode_product)
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.lot_id, self.lot)
        self.assertEqual(line.location_id, location)
        self.assertEqual(line.location_dest_id, self.location_test)
        self.assertEqual(line.qty, 1)

    def test_check_quants_location_validate_internal_transfers(self):
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product, location, 1, lot_id=self.lot.id)
        wizard = self.env['stock.barcodes.internal.transfers'].create({})
        wizard._origin = wizard
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertFalse(wizard.location_dest_id)
        wizard.identify_barcode(self.barcode_product)
        wizard._compute_line_ids()
        self.assertEqual(len(wizard.line_ids), 1)
        wizard.identify_barcode(self.barcode_location)
        wizard._compute_line_ids()
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertTrue(wizard.location_dest_id)
        self.assertEqual(wizard.location_dest_id, self.location_test)
        line = wizard.line_ids[0]
        self.assertEqual(line.wizard_id, wizard)
        self.assertEqual(line.barcode, self.barcode_product)
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.lot_id, self.lot)
        self.assertEqual(line.location_id, location)
        self.assertEqual(line.location_dest_id, self.location_test)
        self.assertEqual(line.qty, 1)
        res = wizard.check_quants_location()
        self.assertTrue(res)
        sublocation_test = self.env['stock.location'].create({
            'name': 'Test internal sublocation',
            'usage': 'internal',
            'barcode': self.barcode_sublocation,
            'location_id': location.id,
        })
        line.location_id = sublocation_test.id
        self.assertNotEqual(line.location_id, location)
        self.assertEqual(line.location_id, sublocation_test)
        res = wizard.check_quants_location()
        self.assertFalse(res)

    def test_validate_picking_barcode(self):
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product, location, 1, lot_id=self.lot.id)
        wizard = self.env['stock.barcodes.internal.transfers'].create({})
        wizard._origin = wizard
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertFalse(wizard.location_dest_id)
        wizard.identify_barcode(self.barcode_product)
        wizard._compute_line_ids()
        self.assertEqual(len(wizard.line_ids), 1)
        wizard.identify_barcode(self.barcode_location)
        wizard._compute_line_ids()
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertTrue(wizard.location_dest_id)
        self.assertEqual(wizard.location_dest_id, self.location_test)
        line = wizard.line_ids[0]
        self.assertEqual(line.wizard_id, wizard)
        self.assertEqual(line.barcode, self.barcode_product)
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.lot_id, self.lot)
        self.assertEqual(line.location_id, location)
        self.assertEqual(line.location_dest_id, self.location_test)
        self.assertEqual(line.qty, 1)
        picking_type = self.env.ref('stock.picking_type_out')
        picking_type_barcode = '56JK89'
        picking_type.validate_barcode_action = picking_type_barcode
        self.assertFalse(wizard.picking_id)
        wizard.with_context(active_id=picking_type.id).identify_barcode(
            picking_type_barcode)
        self.assertTrue(wizard.picking_id)

    def test_validate_picking_internal_barcode(self):
        location_stock_1 = self.env['stock.location'].create({
            'name': 'Stock1',
            'barcode': 'STOCK1',
            'usage': 'internal',
            'location_id': self.env.ref('stock.stock_location_stock').id,
        })
        location_stock_2 = self.env['stock.location'].create({
            'name': 'Stock2',
            'barcode': 'STOCK2',
            'usage': 'internal',
            'location_id': self.env.ref('stock.stock_location_stock').id,
        })
        self.create_inventory(
            self.product, location_stock_1, 1, lot_id=self.lot.id)
        wizard = self.env['stock.barcodes.internal.transfers'].create({})
        wizard._origin = wizard
        wizard.identify_barcode(self.lot.name)
        wizard._compute_line_ids()
        self.assertEqual(len(wizard.line_ids), 1)
        wizard.identify_barcode(location_stock_2.barcode)
        wizard._compute_line_ids()
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(wizard.location_dest_id, location_stock_2)
        line = wizard.line_ids[0]
        self.assertEqual(line.wizard_id, wizard)
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.lot_id, self.lot)
        self.assertEqual(line.location_id, location_stock_1)
        self.assertEqual(line.location_dest_id, location_stock_2)
        self.assertEqual(line.qty, 1)
        picking_type = self.env.ref('stock.picking_type_internal')
        picking_type_barcode = '56JK89'
        picking_type.validate_barcode_action = picking_type_barcode
        self.assertFalse(wizard.picking_id)
        quants = self.env['stock.quant'].search([('lot_id', '=', self.lot.id)])
        self.assertEquals(len(quants), 2)

        def get_quant_in_location(location):
            return quants.filtered(lambda q: q.location_id == location)

        stock_1_quant = get_quant_in_location(location_stock_1)
        self.assertEqual(len(stock_1_quant), 1)
        self.assertTrue(stock_1_quant.quantity, 1)
        wizard.validate_picking(picking_type)
        picking = wizard.picking_id
        self.assertTrue(picking)
        self.assertEqual(picking.state, 'done')
        quants = self.env['stock.quant'].search([('lot_id', '=', self.lot.id)])
        self.assertEquals(len(quants), 3)
        stock_1_quant = get_quant_in_location(location_stock_1)
        self.assertEqual(len(stock_1_quant), 1)
        self.assertEqual(stock_1_quant.quantity, 0)
        stock_2_quant = get_quant_in_location(location_stock_2)
        self.assertEqual(len(stock_2_quant), 1)
        self.assertEqual(stock_2_quant.quantity, 1)

    def test_no_qty_available_quant(self):
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product, location, 1, lot_id=self.lot.id)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 20,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.assertEqual(len(sale.picking_ids), 0)
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        self.assertEqual(picking.state, 'confirmed')
        picking.action_assign()
        line = picking.move_line_ids[0]
        self.assertEqual(picking.state, 'assigned')
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.lot_id, self.lot)
        self.assertEqual(line.product_uom_qty, 1)
        wizard = self.env['stock.barcodes.internal.transfers'].create({})
        wizard._origin = wizard
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertFalse(wizard.location_dest_id)
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.identify_barcode(self.barcode_product)
        self.assertEqual(
            result.exception.name,
            'There is no available quantity in quant or all units of lot '
            '[%s] are reserved.' % self.barcode_product)

    def test_stock_barcodes_internal_popup_info(self):
        lot_02 = self.env['stock.production.lot'].create({
            'name': 'LOT987654321',
            'product_id': self.product.id,
        })
        lot_03 = self.env['stock.production.lot'].create({
            'name': 'LOT963852741',
            'product_id': self.product.id,
        })
        lot_04 = self.env['stock.production.lot'].create({
            'name': 'LOT147258369',
            'product_id': self.product.id,
        })
        lot_05 = self.env['stock.production.lot'].create({
            'name': 'LOT357159852',
            'product_id': self.product.id,
        })
        lot_06 = self.env['stock.production.lot'].create({
            'name': 'LOT654987321',
            'product_id': self.product.id,
        })
        lot_07 = self.env['stock.production.lot'].create({
            'name': 'LOT371985468',
            'product_id': self.product.id,
        })
        location_02 = self.env['stock.location'].create({
            'name': 'INTERNAL_02',
            'usage': 'internal',
            'barcode': 'LOCATION8547965',
        })
        location_03 = self.env['stock.location'].create({
            'name': 'INTERNAL_03',
            'usage': 'internal',
            'barcode': 'LOCATION8495623',
        })
        location_04 = self.env['stock.location'].create({
            'name': 'INTERNAL_04',
            'usage': 'internal',
            'barcode': 'LOCATION1486521',
        })
        location_05 = self.env['stock.location'].create({
            'name': 'INTERNAL_05',
            'usage': 'internal',
            'barcode': 'LOCATION6935842',
        })
        location_06 = self.env['stock.location'].create({
            'name': 'INTERNAL_06',
            'usage': 'internal',
            'barcode': 'LOCATION7312456',
        })
        location_07 = self.env['stock.location'].create({
            'name': 'INTERNAL_07',
            'usage': 'internal',
            'barcode': 'LOCATION8462468',
        })
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product, location, 7, lot_id=self.lot.id)
        self.create_inventory(self.product, location_02, 6, lot_id=lot_02.id)
        self.create_inventory(self.product, location_03, 5, lot_id=lot_03.id)
        self.create_inventory(self.product, location_04, 4, lot_id=lot_04.id)
        self.create_inventory(self.product, location_05, 3, lot_id=lot_05.id)
        self.create_inventory(self.product, location_06, 2, lot_id=lot_06.id)
        self.create_inventory(self.product, location_07, 1, lot_id=lot_07.id)
        wizard = self.env['stock.barcodes.internal.transfers'].create({})
        wizard._origin = wizard
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertFalse(wizard.location_dest_id)
        wizard.identify_barcode(self.barcode_product)
        wizard._compute_line_ids()
        self.assertEqual(len(wizard.line_ids), 1)
        line = wizard.line_ids[0]
        self.assertEqual(line.barcode, self.barcode_product)
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.lot_id, self.lot)
        self.assertEqual(line.qty, 1)
        self.assertTrue(line.stock_info)
        stock_info = line.stock_info.split(',')
        self.assertEqual(len(stock_info), 5)
        self.assertEqual('INTERNAL_02: 6.0', stock_info[0])
        self.assertEqual('INTERNAL_03: 5.0', stock_info[1])
        self.assertEqual('INTERNAL_04: 4.0', stock_info[2])
        self.assertEqual('INTERNAL_05: 3.0', stock_info[3])
        self.assertEqual('INTERNAL_06: 2.0', stock_info[4])
        wizard.identify_barcode(lot_02.name)
        wizard._compute_line_ids()
        self.assertEqual(len(wizard.line_ids), 2)
        line = wizard.line_ids[1]
        self.assertEqual(line.barcode, lot_02.name)
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.lot_id, lot_02)
        self.assertEqual(line.qty, 1)
        self.assertTrue(line.stock_info)
        stock_info = line.stock_info.split(',')
        self.assertEqual(len(stock_info), 5)
        self.assertEqual('Stock: 7.0', stock_info[0])
        self.assertEqual('INTERNAL_03: 5.0', stock_info[1])
        self.assertEqual('INTERNAL_04: 4.0', stock_info[2])
        self.assertEqual('INTERNAL_05: 3.0', stock_info[3])
        self.assertEqual('INTERNAL_06: 2.0', stock_info[4])
        lot_08 = self.env['stock.production.lot'].create({
            'name': 'LOT666932145',
            'product_id': self.product.id,
        })
        self.create_inventory(self.product, location_02, 2, lot_id=lot_08.id)
        wizard.identify_barcode(lot_03.name)
        wizard._compute_line_ids()
        self.assertEqual(len(wizard.line_ids), 3)
        line = wizard.line_ids[2]
        self.assertEqual(line.barcode, lot_03.name)
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.lot_id, lot_03)
        self.assertEqual(line.qty, 1)
        self.assertTrue(line.stock_info)
        stock_info = line.stock_info.split(',')
        self.assertEqual(len(stock_info), 5)
        self.assertEqual('INTERNAL_02: 8.0', stock_info[0])
        self.assertEqual('Stock: 7.0', stock_info[1])
        self.assertEqual('INTERNAL_04: 4.0', stock_info[2])
        self.assertEqual('INTERNAL_05: 3.0', stock_info[3])
        self.assertEqual('INTERNAL_06: 2.0', stock_info[4])
