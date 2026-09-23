###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestStockLotBarcode(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.scan_read_picking = self.env['wiz.stock.barcodes.read.picking']
        self.product_01 = self.env['product.product'].create({
            'name': 'Test product 01',
            'type': 'product',
            'barcode': '123456789A',
            'tracking': 'lot',
        })
        self.lot_01 = self.env['stock.lot'].create({
            'name': 'Lote_test_01',
            'product_id': self.product_01.id,
        })
        self.product_02 = self.env['product.product'].create({
            'name': 'Test product 02',
            'type': 'product',
            'barcode': '987654321B',
            'tracking': 'lot',
        })
        self.lot_02 = self.env['stock.lot'].create({
            'name': 'Lote_test_02',
            'product_id': self.product_02.id,
            'barcode': 'LOTBARCODE123',
        })
        self.lot_03 = self.env['stock.lot'].create({
            'name': 'Lote_test_03',
            'product_id': self.product_02.id,
            'barcode': 'LOTBARCODEDUPLICATE',
        })
        self.lot_04 = self.env['stock.lot'].create({
            'name': 'Lote_test_04',
            'product_id': self.product_02.id,
            'barcode': 'LOTBARCODEDUPLICATE',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': False,
        })
        self.warehouse01 = self.env['stock.warehouse'].create({
            'name': 'Warehouse 01',
            'code': 'WH01',
        })

    def create_picking_in(self , product, qty):
        supplier_location = self.env.ref('stock.stock_location_suppliers')
        stock_location = self.env.ref('stock.stock_location_stock')
        return self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.warehouse01.in_type_id.id,
            'location_id': supplier_location.id,
            'location_dest_id': stock_location.id,
            'move_ids': [(0, 0, {
                'product_id': product.id,
                'name': product.name,
                'product_uom': product.uom_id.id,
                'product_uom_qty': qty,
                'location_id': supplier_location.id,
                'location_dest_id': stock_location.id,
            })]
        })

    def action_barcode_scanned(self, wizard, barcode):
        wizard._barcode_scanned = barcode
        wizard._on_barcode_scanned()
        if wizard._name != 'wiz.stock.barcodes.new.lot':
            wizard.dummy_on_barcode_scanned()

    def test_scan_name_of_lot(self):
        picking = self.create_picking_in(self.product_01, 1)
        action = picking.action_barcode_scan()
        wiz_scan_picking = self.scan_read_picking.browse(action['res_id'])
        wiz_scan_picking.location_dest_id = picking.location_dest_id
        wiz_scan_picking = wiz_scan_picking.with_context(
            force_create_move=True, no_increase_qty_done=True
        )
        self.assertEqual(
            wiz_scan_picking.message, 'Scan Packaging, Product, Lot')
        self.action_barcode_scanned(wiz_scan_picking, 'Lote_test_01')
        self.assertEqual(wiz_scan_picking.message_type, 'info_page')
        self.assertEqual(
            wiz_scan_picking.message, 'Lote_test_01 (Scan Packaging, Product, Lot)')
        sml = picking.move_line_ids.filtered(
            lambda x: x.product_id == self.product_01
        )
        self.assertEqual(sml.lot_id, self.lot_01)
        self.assertEqual(sml.qty_done, 1.0)

    def test_scan_barcode_of_lot(self):
        picking = self.create_picking_in(self.product_02, 1)
        action = picking.action_barcode_scan()
        wiz_scan_picking = self.scan_read_picking.browse(action['res_id'])
        wiz_scan_picking.location_dest_id = picking.location_dest_id
        wiz_scan_picking = wiz_scan_picking.with_context(
            force_create_move=True, no_increase_qty_done=True
        )
        self.assertEqual(
            wiz_scan_picking.message, 'Scan Packaging, Product, Lot')
        self.action_barcode_scanned(wiz_scan_picking, 'LOTBARCODE123')
        self.assertEqual(wiz_scan_picking.message_type, 'info_page')
        self.assertEqual(
            wiz_scan_picking.message, 'LOTBARCODE123 (Scan Packaging, Product, Lot)')
        sml = picking.move_line_ids.filtered(
            lambda x: x.product_id == self.product_02
        )
        self.assertEqual(sml.lot_id, self.lot_02)
        self.assertEqual(sml.qty_done, 1.0)

    def test_scan_lot_error(self):
        picking = self.create_picking_in(self.product_02, 1)
        action = picking.action_barcode_scan()
        wiz_scan_picking = self.scan_read_picking.browse(action['res_id'])
        wiz_scan_picking = wiz_scan_picking.with_context(
            force_create_move=True, no_increase_qty_done=True
        )
        self.assertEqual(
            wiz_scan_picking.message, 'Scan Packaging, Product, Lot')
        self.action_barcode_scanned(wiz_scan_picking, 'TestErrorLot')
        self.assertEqual(wiz_scan_picking.message_type, 'not_found')
        self.assertEqual(
            wiz_scan_picking.message, 'TestErrorLot '
            '(Barcode not found with this screen values)')
        sml = picking.move_line_ids.filtered(
            lambda x: x.product_id == self.product_02
        )
        self.assertFalse(sml.lot_id.id)
        self.assertEqual(sml.qty_done, 0)

    def test_scan_barcode_lot_duplicate(self):
        picking = self.create_picking_in(self.product_02, 1)
        action = picking.action_barcode_scan()
        wiz_scan_picking = self.scan_read_picking.browse(action['res_id'])
        wiz_scan_picking = wiz_scan_picking.with_context(
            force_create_move=True, no_increase_qty_done=True
        )
        self.assertEqual(
            wiz_scan_picking.message, 'Scan Packaging, Product, Lot')
        self.action_barcode_scanned(wiz_scan_picking, 'LOTBARCODEDUPLICATE')
        self.assertEqual(wiz_scan_picking.message_type, 'more_match')
        self.assertEqual(
            wiz_scan_picking.message, 'LOTBARCODEDUPLICATE (More than one lot '
            'found\nScan product before)')
        sml = picking.move_line_ids.filtered(
            lambda x: x.product_id == self.product_02
        )
        self.assertEqual(sml.lot_id.id, False)
        self.assertEqual(sml.qty_done, 0)
