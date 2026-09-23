###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests import common


class TestStockBarcodesDummyLabel(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product_01 = self.env.ref('product.product_product_8')
        self.product_01.packaging_ids = [(0, 0, {
            'name': 'Box 12',
            'qty': 12,
            'barcode': '1234567890123',
        })]
        self.product_01.default_code = 'PRD-01'
        self.product_02 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 2',
            'standard_price': 10,
            'default_code': '02-PROD',
            'list_price': 100,
            'packaging_ids': [
                (0, 0, {
                    'name': 'Box 6',
                    'qty': 6,
                    'barcode': '9876543219876',
                })
            ]
        })
        self.product_03 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 3',
            'standard_price': 20,
            'list_price': 50,
            'default_code': 'RTEST-03',
            'barcode': '65781369852',
        })
        self.product_04 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 4',
            'standard_price': 30,
            'list_price': 78,
            'default_code': 'PKM-04',
            'barcode': '978020137962',
        })
        self.product_05 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 5',
            'standard_price': 40,
            'list_price': 60,
            'default_code': 'PBC-05',
            'barcode': '932195175684',
        })
        self.lot_01 = self.env['stock.production.lot'].create({
            'product_id': self.product_01.id,
        })
        self.lot_02 = self.env['stock.production.lot'].create({
            'product_id': self.product_02.id,
        })
        self.dummy_type = self.env['stock.quant_package.dummy.type'].create({
            'name': 'Dummy',
            'prefix': '4841255',
            'dummy_type': 'dummy',
        })
        self.pallet_type = self.env['stock.quant_package.dummy.type'].create({
            'name': 'Mixed package',
            'prefix': '5821479',
            'dummy_type': 'pallet',
        })
        self.mixed_type = self.env['stock.quant_package.dummy.type'].create({
            'name': 'Pallet',
            'prefix': '7894561',
            'dummy_type': 'mixed_package',
        })

    def create_inventory(self, product, location, qty, lot_id=False,
                         package_id=False):
        inventory = self.env['stock.inventory'].create({
            'name': 'Inventory test',
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

    def test_stock_barcodes_sale_dummy(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 2)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(wizard_line_01.product_id, self.product_01)
        self.assertEqual(wizard_line_01.qty, 12)
        self.assertEqual(wizard_line_02.product_id, self.product_02)
        self.assertEqual(wizard_line_02.qty, 6)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)

    def test_stock_barcodes_sale_dummy_pallet(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 2)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(wizard_line_01.product_id, self.product_01)
        self.assertEqual(wizard_line_01.qty, 12)
        self.assertEqual(wizard_line_02.product_id, self.product_02)
        self.assertEqual(wizard_line_02.qty, 6)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 1)
        self.assertEqual(
            len(wizard.confirm_line_ids),
            len(wizard.confirm_line_ids.filtered(
                lambda ln: not ln.pallet_barcode)))
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            len(wizard.confirm_line_ids.filtered(
                lambda ln: not ln.pallet_barcode)), 0)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])

    def test_stock_barcodes_sale_dummy_mixed_package(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        wizard_line_03 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_03)
        self.assertEqual(wizard_line_01.product_id, self.product_01)
        self.assertEqual(wizard_line_01.qty, 12)
        self.assertEqual(wizard_line_02.product_id, self.product_02)
        self.assertEqual(wizard_line_02.qty, 6)
        self.assertEqual(wizard_line_03.product_id, self.product_03)
        self.assertEqual(wizard_line_03.qty, 1)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        self.assertNotEqual(wizard.line_ids[2].qty, 0)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertTrue(wizard.is_packaging)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.package_barcode, barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard.on_barcode_scanned(self.product_03.barcode)
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.confirm_line_ids[2].barcode, barcode_mixed[0])
        self.assertEqual(wizard.confirm_line_ids[2].qty, 1)
        self.assertEqual(wizard.line_ids[2].qty, 0)

    def test_stock_barcodes_sale_dummy_mixed_package_pallet(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        wizard_line_03 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_03)
        self.assertEqual(wizard_line_01.product_id, self.product_01)
        self.assertEqual(wizard_line_01.qty, 12)
        self.assertEqual(wizard_line_02.product_id, self.product_02)
        self.assertEqual(wizard_line_02.qty, 6)
        self.assertEqual(wizard_line_03.product_id, self.product_03)
        self.assertEqual(wizard_line_03.qty, 1)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        self.assertNotEqual(wizard.line_ids[2].qty, 0)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertTrue(wizard.is_packaging)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.package_barcode, barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.confirm_line_ids[2].barcode, barcode_mixed[0])
        self.assertEqual(wizard.confirm_line_ids[2].qty, 1)
        self.assertEqual(wizard.line_ids[2].qty, 0)
        self.assertEqual(
            len(wizard.confirm_line_ids),
            len(wizard.confirm_line_ids.filtered(
                lambda ln: not ln.pallet_barcode)))
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 1)
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            len(wizard.confirm_line_ids.filtered(
                lambda ln: not ln.pallet_barcode)), 0)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[0])

    def test_stock_barcodes_sale_dummy_all_completed(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        wizard_03 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_03.action_print()
        barcodes_03 = wizard_03.get_barcodes()
        self.assertEqual(len(barcodes_03), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 2)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(wizard_line_01.product_id, self.product_01)
        self.assertEqual(wizard_line_01.qty, 12)
        self.assertEqual(wizard_line_02.product_id, self.product_02)
        self.assertEqual(wizard_line_02.qty, 6)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        wizard.on_barcode_scanned(barcodes_03[0])
        self.assertEqual('error', wizard.message_type)
        self.assertIn('No quantity left to serve', wizard.message)

    def test_stock_barcodes_sale_mixed_package_all_completed(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        wizard_line_03 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_03)
        self.assertEqual(wizard_line_01.product_id, self.product_01)
        self.assertEqual(wizard_line_01.qty, 12)
        self.assertEqual(wizard_line_02.product_id, self.product_02)
        self.assertEqual(wizard_line_02.qty, 6)
        self.assertEqual(wizard_line_03.product_id, self.product_03)
        self.assertEqual(wizard_line_03.qty, 1)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.confirm_line_ids[2].barcode, barcode_mixed[0])
        self.assertEqual(wizard.confirm_line_ids[2].qty, 1)
        self.assertEqual(wizard.line_ids[2].qty, 0)
        wizard_mixed_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed_02.action_print()
        barcode_mixed_02 = wizard_mixed_02.get_barcodes()
        self.assertEqual(len(barcode_mixed_02), 1)
        wizard.on_barcode_scanned(barcode_mixed_02[0])
        self.assertEqual('error', wizard.message_type)
        self.assertIn('No quantity left to serve', wizard.message)

    def test_stock_barcodes_sale_dummy_too_much_qty(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        wizard_03 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_03.action_print()
        barcodes_03 = wizard_03.get_barcodes()
        self.assertEqual(len(barcodes_03), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 10,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 2)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(wizard_line_01.product_id, self.product_01)
        self.assertEqual(wizard_line_01.qty, 12)
        self.assertEqual(wizard_line_02.product_id, self.product_02)
        self.assertEqual(wizard_line_02.qty, 10)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard_line_02.qty, 4)
        self.assertEqual(wizard_line_01.qty, 0)
        wizard.on_barcode_scanned(barcodes_03[0])
        self.assertEqual(wizard.message_type, 'error')
        self.assertIn(
            'The box contains more than the remaining quantity', wizard.message)

    def test_stock_barcodes_sale_product_without_mixed_package(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        wizard_line_03 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_03)
        self.assertEqual(wizard_line_01.product_id, self.product_01)
        self.assertEqual(wizard_line_01.qty, 12)
        self.assertEqual(wizard_line_02.product_id, self.product_02)
        self.assertEqual(wizard_line_02.qty, 6)
        self.assertEqual(wizard_line_03.product_id, self.product_03)
        self.assertEqual(wizard_line_03.qty, 1)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(self.product_03.barcode)
        self.assertEqual(wizard.message_type, 'error')
        self.assertIn(
            'To put a product in a box, you must first read the box code',
            wizard.message)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.confirm_line_ids[2].barcode, barcode_mixed[0])
        self.assertEqual(wizard.confirm_line_ids[2].qty, 1)
        self.assertEqual(wizard.line_ids[2].qty, 0)

    def test_stock_barcodes_dummy_not_found(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 2)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(wizard_line_01.product_id, self.product_01)
        self.assertEqual(wizard_line_01.qty, 12)
        self.assertEqual(wizard_line_02.product_id, self.product_02)
        self.assertEqual(wizard_line_02.qty, 6)
        wizard._origin = wizard
        bad_barcode = '123456789'
        self.assertNotEqual(barcodes_01[0], bad_barcode)
        self.assertNotEqual(barcodes_02[0], bad_barcode)
        wizard.on_barcode_scanned(bad_barcode)
        self.assertEqual(wizard.message_type, 'not_found')
        self.assertIn('Barcode not found', wizard.message)

    def test_stock_barcodes_product_not_found_in_picking(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        wizard_line_03 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_03)
        self.assertEqual(wizard_line_01.product_id, self.product_01)
        self.assertEqual(wizard_line_01.qty, 12)
        self.assertEqual(wizard_line_02.product_id, self.product_02)
        self.assertEqual(wizard_line_02.qty, 6)
        self.assertEqual(wizard_line_03.product_id, self.product_03)
        self.assertEqual(wizard_line_03.qty, 1)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_04.barcode)
        self.assertEqual(wizard.message_type, 'error')
        self.assertIn(
            'Product not belongs to picking', wizard.message)

    def test_stock_barcodes_transfer_mixed_package_without_opening_first(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        wizard_line_03 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_03)
        self.assertEqual(wizard_line_01.product_id, self.product_01)
        self.assertEqual(wizard_line_01.qty, 12)
        self.assertEqual(wizard_line_02.product_id, self.product_02)
        self.assertEqual(wizard_line_02.qty, 6)
        self.assertEqual(wizard_line_03.product_id, self.product_03)
        self.assertEqual(wizard_line_03.qty, 1)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(self.product_03.barcode)
        self.assertEqual(wizard.message_type, 'error')
        self.assertIn(
            'To put a product in a box, you must first read the box code',
            wizard.message)

    def test_stock_barcodes_mixed_package_close_empty_and_reopen(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        self.create_inventory(self.product_04, location, 50)
        self.create_inventory(self.product_05, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_04.id,
                    'price_unit': 60,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_05.id,
                    'price_unit': 70,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 5)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        self.assertEqual(wizard_line_01.qty, 0)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(wizard_line_02.qty, 0)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard_mixed_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed_02.action_print()
        barcode_mixed_02 = wizard_mixed_02.get_barcodes()
        self.assertEqual(len(barcode_mixed_02), 1)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard.on_barcode_scanned(barcode_mixed_02[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(self.product_04.barcode)
        wizard.on_barcode_scanned(barcode_mixed_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 4)
        wizard_line_03 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_03)
        self.assertEqual(wizard_line_03.qty, 0)
        wizard_line_04 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_04)
        self.assertEqual(wizard_line_04.qty, 0)
        self.assertEqual(len(wizard.confirm_line_ids), 4)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_05.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 5)
        wizard_line_05 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_05)
        self.assertEqual(wizard_line_05.qty, 0)
        self.assertEqual(
            len(wizard.line_ids.filtered(lambda ln: ln.qty != 0)), 0)

    def test_stock_barcodes_delete_dummy_package(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 2)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(wizard_line_01.product_id, self.product_01)
        self.assertEqual(wizard_line_01.qty, 12)
        self.assertEqual(wizard_line_02.product_id, self.product_02)
        self.assertEqual(wizard_line_02.qty, 6)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        self.assertEqual(wizard_line_01.qty, 0)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(wizard_line_02.qty, 0)
        confirm_line_02 = wizard.confirm_line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        confirm_line_02.action_remove_line()
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(wizard_line_02.qty, 6)
        self.assertEqual(wizard_line_01.qty, 0)

    def test_stock_barcodes_delete_products_mixed_package(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        wizard_line_03 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_03)
        self.assertEqual(wizard_line_01.product_id, self.product_01)
        self.assertEqual(wizard_line_01.qty, 12)
        self.assertEqual(wizard_line_02.product_id, self.product_02)
        self.assertEqual(wizard_line_02.qty, 6)
        self.assertEqual(wizard_line_03.product_id, self.product_03)
        self.assertEqual(wizard_line_03.qty, 1)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        self.assertNotEqual(wizard.line_ids[2].qty, 0)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertTrue(wizard.is_packaging)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.package_barcode, barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard.on_barcode_scanned(self.product_03.barcode)
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.confirm_line_ids[2].barcode, barcode_mixed[0])
        self.assertEqual(wizard.confirm_line_ids[2].qty, 1)
        self.assertEqual(wizard.line_ids[2].qty, 0)
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(len(wizard.line_ids), 3)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_03)
        self.assertEqual(wizard_line_01.qty, 0)
        confirm_line_01 = wizard.confirm_line_ids.filtered(
            lambda ln: ln.product_id == self.product_03)
        confirm_line_01.action_remove_line()
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(wizard_line_01.qty, 1)

    def test_stock_barcodes_validate_dummy_scan_01(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        self.create_inventory(self.product_04, location, 50)
        self.create_inventory(self.product_05, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_04.id,
                    'price_unit': 60,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_05.id,
                    'price_unit': 70,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 5)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        self.assertEqual(wizard_line_01.qty, 0)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(wizard_line_02.qty, 0)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard_mixed_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed_02.action_print()
        barcode_mixed_02 = wizard_mixed_02.get_barcodes()
        self.assertEqual(len(barcode_mixed_02), 1)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard.on_barcode_scanned(barcode_mixed_02[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(self.product_04.barcode)
        wizard.on_barcode_scanned(barcode_mixed_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 4)
        wizard_line_03 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_03)
        self.assertEqual(wizard_line_03.qty, 0)
        wizard_line_04 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_04)
        self.assertEqual(wizard_line_04.qty, 0)
        self.assertEqual(len(wizard.confirm_line_ids), 4)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_05.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 5)
        wizard_line_05 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_05)
        self.assertEqual(wizard_line_05.qty, 0)
        self.assertEqual(
            len(wizard.line_ids.filtered(lambda ln: ln.qty != 0)), 0)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 1)
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.button_validate_dummy_scan()
        self.assertTrue(len(picking.move_line_ids) > 0)
        self.assertEqual(
            sum(picking.move_line_ids.mapped('product_uom_qty')),
            sum(picking.move_line_ids.mapped('qty_done')))

    def test_stock_barcodes_validate_dummy_scan_02(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        self.create_inventory(self.product_04, location, 50)
        self.create_inventory(self.product_05, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_04.id,
                    'price_unit': 60,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_05.id,
                    'price_unit': 70,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 5)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard_mixed_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed_02.action_print()
        barcode_mixed_02 = wizard_mixed_02.get_barcodes()
        self.assertEqual(len(barcode_mixed_02), 1)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard.on_barcode_scanned(barcode_mixed_02[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(barcode_mixed_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_05.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 4)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 1)
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.button_validate_dummy_scan()
        self.assertNotEqual(
            sum(picking.move_line_ids.mapped('product_uom_qty')),
            sum(picking.move_line_ids.mapped('qty_done')))
        self.assertEqual(
            len(picking.move_line_ids.mapped('result_package_id')), 4)
        self.assertEqual(
            len(picking.move_line_ids.mapped('result_package_id.parent_id')), 1)
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_04.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        wizard.button_validate_dummy_scan()
        self.assertEqual(
            sum(picking.move_line_ids.mapped('product_uom_qty')),
            sum(picking.move_line_ids.mapped('qty_done')))
        self.assertEqual(
            len(picking.move_line_ids.mapped('result_package_id')), 4)
        self.assertEqual(
            len(picking.move_line_ids.mapped('result_package_id.parent_id')), 1)

    def test_stock_barcodes_validate_dummy_scan_03(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        self.create_inventory(self.product_04, location, 50)
        self.create_inventory(self.product_05, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_04.id,
                    'price_unit': 60,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_05.id,
                    'price_unit': 70,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 5)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard_mixed_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed_02.action_print()
        barcode_mixed_02 = wizard_mixed_02.get_barcodes()
        self.assertEqual(len(barcode_mixed_02), 1)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard.on_barcode_scanned(barcode_mixed_02[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(self.product_04.barcode)
        wizard.on_barcode_scanned(barcode_mixed_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 4)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 1)
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.button_validate_dummy_scan()
        self.assertNotEqual(
            sum(picking.move_line_ids.mapped('product_uom_qty')),
            sum(picking.move_line_ids.mapped('qty_done')))
        self.assertEqual(
            len(picking.move_line_ids.mapped('result_package_id')), 3)
        self.assertEqual(
            len(picking.move_line_ids.mapped('result_package_id.parent_id')), 1)
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_05.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        wizard.button_validate_dummy_scan()
        self.assertEqual(
            sum(picking.move_line_ids.mapped('product_uom_qty')),
            sum(picking.move_line_ids.mapped('qty_done')))
        self.assertEqual(
            len(picking.move_line_ids.mapped('result_package_id')), 4)
        self.assertEqual(
            len(picking.move_line_ids.mapped('result_package_id.parent_id')), 1)

    def test_stock_barcodes_validate_dummy_scan_04(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        self.create_inventory(self.product_04, location, 50)
        self.create_inventory(self.product_05, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_04.id,
                    'price_unit': 60,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_05.id,
                    'price_unit': 70,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 5)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        wizard_mixed_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed_02.action_print()
        barcode_mixed_02 = wizard_mixed_02.get_barcodes()
        self.assertEqual(len(barcode_mixed_02), 1)
        wizard.on_barcode_scanned(barcode_mixed_02[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(self.product_04.barcode)
        wizard.on_barcode_scanned(barcode_mixed_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 1)
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.button_validate_dummy_scan()
        self.assertNotEqual(
            sum(picking.move_line_ids.mapped('product_uom_qty')),
            sum(picking.move_line_ids.mapped('qty_done')))
        self.assertEqual(
            len(picking.move_line_ids.mapped('result_package_id')), 2)
        self.assertEqual(
            len(picking.move_line_ids.mapped('result_package_id.parent_id')), 1)
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_05.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard.button_validate_dummy_scan()
        self.assertEqual(
            sum(picking.move_line_ids.mapped('product_uom_qty')),
            sum(picking.move_line_ids.mapped('qty_done')))
        self.assertEqual(
            len(picking.move_line_ids.mapped('result_package_id')), 4)
        self.assertEqual(
            len(picking.move_line_ids.mapped('result_package_id.parent_id')), 1)

    def test_stock_barcodes_reorganize_packages_in_pallet_01(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        self.assertNotEqual(wizard.line_ids[2].qty, 0)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 2)
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.confirm_line_ids[2].barcode, barcode_mixed[0])
        self.assertEqual(wizard.confirm_line_ids[2].qty, 1)
        self.assertFalse(wizard.confirm_line_ids[2].pallet_barcode)
        wizard.on_barcode_scanned(barcode_pallet[1])
        self.assertTrue(wizard.confirm_line_ids[2].pallet_barcode)
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[1])
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertFalse(wizard.reorganize_packages)
        wizard.reorganize_packages = True
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcodes_01[0])
        wizard.on_barcode_scanned(barcodes_02[0])
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.button_reorganize_packages()
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[1])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[1])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[0])
        self.assertFalse(wizard.reorganize_packages)

    def test_stock_barcodes_reorganize_packages_in_pallet_02(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        self.assertNotEqual(wizard.line_ids[2].qty, 0)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 2)
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.confirm_line_ids[2].barcode, barcode_mixed[0])
        self.assertEqual(wizard.confirm_line_ids[2].qty, 1)
        self.assertFalse(wizard.confirm_line_ids[2].pallet_barcode)
        wizard.on_barcode_scanned(barcode_pallet[1])
        self.assertTrue(wizard.confirm_line_ids[2].pallet_barcode)
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[1])
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertFalse(wizard.reorganize_packages)
        wizard.reorganize_packages = True
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcodes_01[0])
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.button_reorganize_packages()
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[1])
        self.assertFalse(wizard.confirm_line_ids[1].pallet_barcode)
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[0])
        self.assertFalse(wizard.reorganize_packages)

    def test_stock_barcodes_error_reorganize_with_no_reads_made(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 2)
        self.assertFalse(wizard.reorganize_packages)
        wizard.reorganize_packages = True
        wizard.on_barcode_scanned(barcode_pallet[1])
        self.assertEqual('error', wizard.message_type)
        self.assertIn('Nothing to reorganize, no read made', wizard.message)

    def test_stock_barcodes_reorganize_packages_in_pallet_03(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        self.assertNotEqual(wizard.line_ids[2].qty, 0)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 2)
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.confirm_line_ids[2].barcode, barcode_mixed[0])
        self.assertEqual(wizard.confirm_line_ids[2].qty, 1)
        self.assertFalse(wizard.confirm_line_ids[2].pallet_barcode)
        wizard.on_barcode_scanned(barcode_pallet[1])
        self.assertTrue(wizard.confirm_line_ids[2].pallet_barcode)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[1])
        self.assertFalse(wizard.reorganize_packages)
        wizard.reorganize_packages = True
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcodes_01[0])
        wizard.on_barcode_scanned(barcodes_02[0])
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertTrue(wizard.reorganize_packages)
        wizard.reorganize_packages = False
        self.assertEqual(len(wizard.reorganize_line_ids), 3)
        wizard._onchange_reorganize_packages()
        self.assertEqual(len(wizard.reorganize_line_ids), 0)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[1])
        wizard.reorganize_packages = True
        self.assertEqual(len(wizard.reorganize_line_ids), 0)

    def test_stock_barcodes_reorganize_packages_not_all_01(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 2)
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_03)
        wizard.on_barcode_scanned(barcode_pallet[1])
        self.assertTrue(wizard.confirm_line_ids[2].pallet_barcode)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[1])
        self.assertFalse(wizard.reorganize_packages)
        wizard.reorganize_packages = True
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcodes_01[0])
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertTrue(wizard.reorganize_packages)
        wizard.button_reorganize_packages()
        self.assertFalse(wizard.reorganize_packages)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[1])
        self.assertFalse(wizard.confirm_line_ids[1].pallet_barcode)
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[0])

    def test_stock_barcodes_reorganize_packages_not_all_02(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 2)
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_03)
        wizard.on_barcode_scanned(barcode_pallet[1])
        self.assertTrue(wizard.confirm_line_ids[2].pallet_barcode)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[1])
        self.assertFalse(wizard.reorganize_packages)
        wizard.reorganize_packages = True
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcodes_01[0])
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertTrue(wizard.reorganize_packages)
        wizard.button_reorganize_packages()
        self.assertFalse(wizard.reorganize_packages)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[1])
        self.assertFalse(wizard.confirm_line_ids[1].pallet_barcode)
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[0])
        self.assertEqual(wizard.pallet_mode, 'complete_empty_mode')
        wizard.pallet_mode = 'individual_mode'
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(wizard.confirm_line_ids[1].barcode)
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[1])

    def test_stock_barcodes_reorganize_packages_not_all_03(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 2)
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_03)
        wizard.on_barcode_scanned(barcode_pallet[1])
        self.assertTrue(wizard.confirm_line_ids[2].pallet_barcode)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[1])
        self.assertFalse(wizard.reorganize_packages)
        wizard.reorganize_packages = True
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcodes_01[0])
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.on_barcode_scanned(barcodes_02[0])
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertTrue(wizard.reorganize_packages)
        wizard.button_reorganize_packages()
        self.assertFalse(wizard.reorganize_packages)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[1])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertFalse(wizard.confirm_line_ids[2].pallet_barcode)
        self.assertEqual(wizard.pallet_mode, 'complete_empty_mode')
        wizard.pallet_mode = 'individual_mode'
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(wizard.confirm_line_ids[2].barcode)
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[1])

    def test_stock_barcodes_reorganize_packages_not_all_04(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 2)
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_03)
        wizard.on_barcode_scanned(barcode_pallet[1])
        self.assertTrue(wizard.confirm_line_ids[2].pallet_barcode)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[1])
        self.assertEqual(wizard.pallet_mode, 'complete_empty_mode')
        wizard.pallet_mode = 'individual_mode'
        self.assertEqual(wizard.pallet_mode, 'individual_mode')
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(wizard.confirm_line_ids[0].barcode)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[1])
        wizard.on_barcode_scanned(wizard.confirm_line_ids[1].barcode)
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[1])
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.on_barcode_scanned(wizard.confirm_line_ids[2].barcode)
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[0])

    def test_stock_barcodes_reorganize_packages_not_all_05(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 2)
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_03)
        wizard.on_barcode_scanned(barcode_pallet[1])
        self.assertTrue(wizard.confirm_line_ids[2].pallet_barcode)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[1])
        self.assertFalse(wizard.reorganize_packages)
        wizard.reorganize_packages = True
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcodes_01[0])
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.on_barcode_scanned(barcodes_02[0])
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertTrue(wizard.reorganize_packages)
        wizard.button_reorganize_packages()
        self.assertFalse(wizard.reorganize_packages)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[1])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertFalse(wizard.confirm_line_ids[2].pallet_barcode)
        self.assertEqual(wizard.pallet_mode, 'complete_empty_mode')
        wizard.pallet_mode = 'individual_mode'
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned('98766543234567')
        self.assertEqual('not_found', wizard.message_type)

    def test_stock_button_action_update_line(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 3,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        wizard_line_03 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_03)
        self.assertEqual(wizard_line_01.product_id, self.product_01)
        self.assertEqual(wizard_line_01.qty, 12)
        self.assertEqual(wizard_line_02.product_id, self.product_02)
        self.assertEqual(wizard_line_02.qty, 6)
        self.assertEqual(wizard_line_03.product_id, self.product_03)
        self.assertEqual(wizard_line_03.qty, 3)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        self.assertNotEqual(wizard.line_ids[2].qty, 0)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertTrue(wizard.is_packaging)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.package_barcode, barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard.on_barcode_scanned(self.product_03.barcode)
        self.assertEqual(wizard.product_packaging, self.product_03)
        self.assertEqual(wizard.product_qty, 1)
        wizard.product_qty = 3
        wizard.action_update_qty_line()
        self.assertEqual(wizard.confirm_line_ids[2].qty, 3)
        self.assertEqual(wizard.line_ids[2].qty, 0)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.confirm_line_ids[2].barcode, barcode_mixed[0])
        self.assertEqual(
            len(wizard.confirm_line_ids),
            len(wizard.confirm_line_ids.filtered(
                lambda ln: not ln.pallet_barcode)))
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 1)
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            len(wizard.confirm_line_ids.filtered(
                lambda ln: not ln.pallet_barcode)), 0)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[0])

    def test_stock_log_update_line(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 3,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        wizard_line_03 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_03)
        self.assertEqual(wizard_line_01.product_id, self.product_01)
        self.assertEqual(wizard_line_01.qty, 12)
        self.assertEqual(wizard_line_02.product_id, self.product_02)
        self.assertEqual(wizard_line_02.qty, 6)
        self.assertEqual(wizard_line_03.product_id, self.product_03)
        self.assertEqual(wizard_line_03.qty, 3)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        self.assertNotEqual(wizard.line_ids[2].qty, 0)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertTrue(wizard.is_packaging)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.package_barcode, barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard.on_barcode_scanned(self.product_03.barcode)
        self.assertEqual(wizard.product_packaging, self.product_03)
        self.assertEqual(wizard.product_qty, 1)
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('picking_id', '=', picking.id),
        ])
        self.assertEqual(len(logs), 3)
        self.assertEqual(logs[2].qty, wizard.confirm_line_ids[2].qty)
        self.assertEqual(logs[2].qty, 1)
        wizard.product_qty = 3
        wizard.action_update_qty_line()
        self.assertEqual(wizard.confirm_line_ids[2].qty, 3)
        self.assertEqual(wizard.line_ids[2].qty, 0)
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('picking_id', '=', picking.id),
        ])
        self.assertEqual(len(logs), 3)
        self.assertEqual(logs[2].qty, wizard.confirm_line_ids[2].qty)
        self.assertEqual(logs[2].qty, 3)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.confirm_line_ids[2].barcode, barcode_mixed[0])
        self.assertEqual(
            len(wizard.confirm_line_ids),
            len(wizard.confirm_line_ids.filtered(
                lambda ln: not ln.pallet_barcode)))
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 1)
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            len(wizard.confirm_line_ids.filtered(
                lambda ln: not ln.pallet_barcode)), 0)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[0])

    def test_stock_log_remove_confirm_line(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 2)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(wizard_line_01.product_id, self.product_01)
        self.assertEqual(wizard_line_01.qty, 12)
        self.assertEqual(wizard_line_02.product_id, self.product_02)
        self.assertEqual(wizard_line_02.qty, 6)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        self.assertEqual(wizard_line_01.qty, 0)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        self.assertEqual(wizard_line_02.qty, 0)
        confirm_line_02 = wizard.confirm_line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('picking_id', '=', picking.id),
        ])
        self.assertEqual(len(logs), 2)
        confirm_line_02.action_remove_line()
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('picking_id', '=', picking.id),
        ])
        self.assertEqual(len(logs), 1)
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(wizard_line_02.qty, 6)
        self.assertEqual(wizard_line_01.qty, 0)

    def test_stock_barcodes_reorganize_log(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        self.assertNotEqual(wizard.line_ids[2].qty, 0)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 2)
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.confirm_line_ids[2].barcode, barcode_mixed[0])
        self.assertEqual(wizard.confirm_line_ids[2].qty, 1)
        self.assertFalse(wizard.confirm_line_ids[2].pallet_barcode)
        wizard.on_barcode_scanned(barcode_pallet[1])
        self.assertTrue(wizard.confirm_line_ids[2].pallet_barcode)
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[1])
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertFalse(wizard.reorganize_packages)
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('picking_id', '=', picking.id),
        ])
        self.assertTrue(logs)
        self.assertEqual(len(logs), 3)
        self.assertEqual(
            logs[0].pallet_barcode, wizard.confirm_line_ids[0].pallet_barcode)
        self.assertEqual(
            logs[1].pallet_barcode, wizard.confirm_line_ids[1].pallet_barcode)
        self.assertEqual(
            logs[2].pallet_barcode, wizard.confirm_line_ids[2].pallet_barcode)
        wizard.reorganize_packages = True
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcodes_01[0])
        wizard.on_barcode_scanned(barcodes_02[0])
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.button_reorganize_packages()
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('picking_id', '=', picking.id),
        ])
        self.assertTrue(logs)
        self.assertEqual(len(logs), 3)
        self.assertEqual(
            logs[0].pallet_barcode, wizard.confirm_line_ids[0].pallet_barcode)
        self.assertEqual(
            logs[1].pallet_barcode, wizard.confirm_line_ids[1].pallet_barcode)
        self.assertEqual(
            logs[2].pallet_barcode, wizard.confirm_line_ids[2].pallet_barcode)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[1])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[1])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[0])
        self.assertFalse(wizard.reorganize_packages)

    def test_stock_barcodes_example_full_log(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        wizard_line_03 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_03)
        self.assertEqual(wizard_line_01.product_id, self.product_01)
        self.assertEqual(wizard_line_01.qty, 12)
        self.assertEqual(wizard_line_02.product_id, self.product_02)
        self.assertEqual(wizard_line_02.qty, 6)
        self.assertEqual(wizard_line_03.product_id, self.product_03)
        self.assertEqual(wizard_line_03.qty, 1)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        self.assertNotEqual(wizard.line_ids[2].qty, 0)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertTrue(wizard.is_packaging)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.package_barcode, barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.confirm_line_ids[2].barcode, barcode_mixed[0])
        self.assertEqual(wizard.confirm_line_ids[2].qty, 1)
        self.assertEqual(wizard.line_ids[2].qty, 0)
        self.assertEqual(
            len(wizard.confirm_line_ids),
            len(wizard.confirm_line_ids.filtered(
                lambda ln: not ln.pallet_barcode)))
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 1)
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            len(wizard.confirm_line_ids.filtered(
                lambda ln: not ln.pallet_barcode)), 0)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[0])
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('picking_id', '=', picking.id),
        ])
        self.assertTrue(logs)
        self.assertEqual(len(logs), 3)
        self.assertEqual(logs[0].barcode, wizard.confirm_line_ids[0].barcode)
        self.assertEqual(logs[0].qty, wizard.confirm_line_ids[0].qty)
        self.assertEqual(logs[1].barcode, wizard.confirm_line_ids[1].barcode)
        self.assertEqual(logs[1].qty, wizard.confirm_line_ids[1].qty)
        self.assertEqual(logs[2].barcode, wizard.confirm_line_ids[2].barcode)
        self.assertEqual(logs[2].qty, wizard.confirm_line_ids[2].qty)

    def test_stock_barcodes_close_and_reopen_wizard_save_log(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        wizard_line_03 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_03)
        self.assertEqual(wizard_line_01.product_id, self.product_01)
        self.assertEqual(wizard_line_01.qty, 12)
        self.assertEqual(wizard_line_02.product_id, self.product_02)
        self.assertEqual(wizard_line_02.qty, 6)
        self.assertEqual(wizard_line_03.product_id, self.product_03)
        self.assertEqual(wizard_line_03.qty, 1)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        self.assertNotEqual(wizard.line_ids[2].qty, 0)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertTrue(wizard.is_packaging)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.package_barcode, barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.confirm_line_ids[2].barcode, barcode_mixed[0])
        self.assertEqual(wizard.confirm_line_ids[2].qty, 1)
        self.assertEqual(wizard.line_ids[2].qty, 0)
        self.assertEqual(
            len(wizard.confirm_line_ids),
            len(wizard.confirm_line_ids.filtered(
                lambda ln: not ln.pallet_barcode)))
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 1)
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            len(wizard.confirm_line_ids.filtered(
                lambda ln: not ln.pallet_barcode)), 0)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[0])
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('picking_id', '=', picking.id),
        ])
        self.assertTrue(logs)
        self.assertEqual(len(logs), 3)
        self.assertEqual(logs[0].barcode, wizard.confirm_line_ids[0].barcode)
        self.assertEqual(logs[0].qty, wizard.confirm_line_ids[0].qty)
        self.assertEqual(logs[1].barcode, wizard.confirm_line_ids[1].barcode)
        self.assertEqual(logs[1].qty, wizard.confirm_line_ids[1].qty)
        self.assertEqual(logs[2].barcode, wizard.confirm_line_ids[2].barcode)
        self.assertEqual(logs[2].qty, wizard.confirm_line_ids[2].qty)
        wizard.unlink()
        action_2 = picking.action_barcode_scan_dummy_label()
        wizard_02 = self.env['stock.barcodes.dummy.label'].browse(
            action_2['res_id'])
        self.assertEqual(wizard_02.picking_id, picking)
        self.assertEqual(len(wizard_02.line_ids), 3)
        self.assertEqual(wizard_02.line_ids[0].qty, 0)
        self.assertEqual(wizard_02.line_ids[1].qty, 0)
        self.assertEqual(wizard_02.line_ids[2].qty, 0)
        self.assertEqual(len(wizard_02.confirm_line_ids), 3)
        self.assertEqual(wizard_02.confirm_line_ids[0].qty, 6)
        self.assertEqual(wizard_02.confirm_line_ids[1].qty, 12)
        self.assertEqual(wizard_02.confirm_line_ids[2].qty, 1)

    def test_stock_barcodes_button_remove_logs_and_reopen_wizard(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        wizard_line_02 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_02)
        wizard_line_03 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_03)
        self.assertEqual(wizard_line_01.product_id, self.product_01)
        self.assertEqual(wizard_line_01.qty, 12)
        self.assertEqual(wizard_line_02.product_id, self.product_02)
        self.assertEqual(wizard_line_02.qty, 6)
        self.assertEqual(wizard_line_03.product_id, self.product_03)
        self.assertEqual(wizard_line_03.qty, 1)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        self.assertNotEqual(wizard.line_ids[2].qty, 0)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertTrue(wizard.is_packaging)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.package_barcode, barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.confirm_line_ids[2].barcode, barcode_mixed[0])
        self.assertEqual(wizard.confirm_line_ids[2].qty, 1)
        self.assertEqual(wizard.line_ids[2].qty, 0)
        self.assertEqual(
            len(wizard.confirm_line_ids),
            len(wizard.confirm_line_ids.filtered(
                lambda ln: not ln.pallet_barcode)))
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 1)
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            len(wizard.confirm_line_ids.filtered(
                lambda ln: not ln.pallet_barcode)), 0)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[0])
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('picking_id', '=', picking.id),
        ])
        self.assertEqual(len(logs), 3)
        self.assertEqual(logs[0].barcode, wizard.confirm_line_ids[0].barcode)
        self.assertEqual(logs[0].qty, wizard.confirm_line_ids[0].qty)
        self.assertEqual(logs[1].barcode, wizard.confirm_line_ids[1].barcode)
        self.assertEqual(logs[1].qty, wizard.confirm_line_ids[1].qty)
        self.assertEqual(logs[2].barcode, wizard.confirm_line_ids[2].barcode)
        self.assertEqual(logs[2].qty, wizard.confirm_line_ids[2].qty)
        wizard.unlink()
        action = picking.button_unlink_stock_barcodes_dummy_log()
        wizard_remove = self.env['stock.barcodes.dummy.remove.logs'].browse(
            action['res_id'])
        wizard_remove.button_unlink_stock_barcodes_dummy_log()
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('picking_id', '=', picking.id),
        ])
        self.assertEqual(len(logs), 0)

    def test_stock_barcodes_validate_scan_log(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 3,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcodes_02[0])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        self.assertNotEqual(wizard.line_ids[2].qty, 0)
        self.assertEqual(
            len(wizard.confirm_line_ids),
            len(wizard.confirm_line_ids.filtered(
                lambda ln: not ln.pallet_barcode)))
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 1)
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            len(wizard.confirm_line_ids.filtered(
                lambda ln: not ln.pallet_barcode)), 0)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        wizard.button_validate_dummy_scan()
        self.assertTrue(len(picking.move_line_ids) > 0)
        self.assertNotEqual(
            sum(picking.move_line_ids.mapped('product_uom_qty')),
            sum(picking.move_line_ids.mapped('qty_done')))
        self.assertEqual(
            len(picking.move_line_ids.mapped('result_package_id')), 2)
        self.assertEqual(
            len(picking.move_line_ids.mapped('result_package_id.parent_id')), 1)
        wizard.unlink()
        action_02 = picking.action_barcode_scan_dummy_label()
        wizard_02 = self.env['stock.barcodes.dummy.label'].browse(
            action_02['res_id'])
        self.assertEqual(len(wizard_02.line_ids), 1)
        self.assertEqual(wizard_02.line_ids[0].qty, 3)
        self.assertEqual(len(wizard_02.confirm_line_ids), 0)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard_02._origin = wizard_02
        wizard_02.on_barcode_scanned(barcode_mixed[0])
        wizard_02.on_barcode_scanned(self.product_03.barcode)
        wizard_02.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard_02.confirm_line_ids), 1)
        self.assertEqual(wizard_02.confirm_line_ids[0].qty, 1)
        wizard_pallet_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'pallet',
        })
        wizard_pallet_02.action_print()
        barcode_pallet = wizard_pallet_02.get_barcodes()
        wizard_02.on_barcode_scanned(barcode_pallet[0])
        wizard_02.button_validate_dummy_scan()
        self.assertTrue(len(picking.move_line_ids) > 0)
        self.assertNotEqual(
            sum(picking.move_line_ids.mapped('product_uom_qty')),
            sum(picking.move_line_ids.mapped('qty_done')))
        self.assertEqual(
            len(picking.move_line_ids.mapped('result_package_id')), 3)
        self.assertEqual(
            len(picking.move_line_ids.mapped('result_package_id.parent_id')), 2)
        wizard_02.unlink()
        action_03 = picking.action_barcode_scan_dummy_label()
        wizard_03 = self.env['stock.barcodes.dummy.label'].browse(
            action_03['res_id'])
        self.assertEqual(len(wizard_03.line_ids), 1)
        self.assertEqual(len(wizard_03.confirm_line_ids), 0)
        self.assertEqual(wizard_03.line_ids[0].qty, 2)
        wizard_03._origin = wizard_03
        wizard_03.on_barcode_scanned(barcode_mixed[0])
        wizard_03.on_barcode_scanned(self.product_03.barcode)
        self.assertEqual(wizard_03.product_packaging, self.product_03)
        self.assertEqual(wizard_03.product_qty, 1)
        wizard_03.product_qty = 2
        wizard_03.action_update_qty_line()
        wizard_03.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard_03.confirm_line_ids), 1)
        self.assertEqual(wizard_03.confirm_line_ids[0].qty, 2)
        self.assertEqual(wizard_03.line_ids[0].qty, 0)
        wizard_03.on_barcode_scanned(barcode_pallet[0])
        wizard_03.button_validate_dummy_scan()
        self.assertTrue(len(picking.move_line_ids) > 0)
        self.assertEqual(
            sum(picking.move_line_ids.mapped('product_uom_qty')),
            sum(picking.move_line_ids.mapped('qty_done')))
        self.assertEqual(
            len(picking.move_line_ids.mapped('result_package_id')), 3)
        self.assertEqual(
            len(picking.move_line_ids.mapped('result_package_id.parent_id')), 2)

    def test_barcodes_sale_multiple_lines_same_product_01(self):
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_03, location, 50)
        self.create_inventory(self.product_04, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 20,
                    'product_uom_qty': 2,
                }),
                (0, 0, {
                    'product_id': self.product_04.id,
                    'price_unit': 30,
                    'product_uom_qty': 4,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 5,
                }),
                (0, 0, {
                    'product_id': self.product_04.id,
                    'price_unit': 25,
                    'product_uom_qty': 6,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(len(picking.move_lines), 4)
        self.assertEqual(len(picking.move_line_ids), 4)
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 2)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.product_qty = 7
        wizard.action_update_qty_line()
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(barcode_mixed[1])
        wizard.on_barcode_scanned(self.product_04.barcode)
        wizard.product_qty = 10
        wizard.action_update_qty_line()
        wizard.on_barcode_scanned(barcode_mixed[1])

        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        self.assertEqual(wizard.confirm_line_ids[0].qty, 7)
        self.assertEqual(wizard.confirm_line_ids[1].qty, 10)
        wizard.confirm_line_ids[1].action_remove_line()
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].qty, 7)
        self.assertEqual(wizard.line_ids[0].qty, 10)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        wizard.on_barcode_scanned(barcode_mixed[1])
        wizard.on_barcode_scanned(self.product_04.barcode)
        wizard.product_qty = 10
        wizard.action_update_qty_line()
        wizard.on_barcode_scanned(barcode_mixed[1])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        self.assertEqual(wizard.confirm_line_ids[0].qty, 7)
        self.assertEqual(wizard.confirm_line_ids[1].qty, 10)
        self.assertNotEqual(
            wizard.confirm_line_ids[0].barcode,
            wizard.confirm_line_ids[1].barcode)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 2)
        self.assertEqual(wizard.pallet_mode, 'complete_empty_mode')
        wizard.pallet_mode = 'individual_mode'
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.on_barcode_scanned(wizard.confirm_line_ids[0].barcode)
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(wizard.confirm_line_ids[1].barcode)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[1])
        self.assertNotEqual(
            wizard.confirm_line_ids[0].pallet_barcode,
            wizard.confirm_line_ids[1].pallet_barcode)
        self.assertFalse(wizard.reorganize_packages)
        wizard.reorganize_packages = True
        wizard._onchange_reorganize_packages()
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.on_barcode_scanned(barcode_mixed[1])
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.button_reorganize_packages()
        self.assertFalse(wizard.reorganize_packages)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[1])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 7)
        self.assertEqual(wizard.confirm_line_ids[1].qty, 10)
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)

    def test_barcodes_sale_multiple_lines_same_product_02(self):
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_03, location, 50)
        self.create_inventory(self.product_04, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 20,
                    'product_uom_qty': 2,
                }),
                (0, 0, {
                    'product_id': self.product_04.id,
                    'price_unit': 30,
                    'product_uom_qty': 4,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 5,
                }),
                (0, 0, {
                    'product_id': self.product_04.id,
                    'price_unit': 25,
                    'product_uom_qty': 6,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(len(picking.move_lines), 4)
        self.assertEqual(len(picking.move_line_ids), 4)
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 2)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.product_qty = 4
        wizard.action_update_qty_line()
        wizard.on_barcode_scanned(barcode_mixed[1])
        wizard.on_barcode_scanned(self.product_04.barcode)
        wizard.product_qty = 6
        wizard.action_update_qty_line()
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.product_qty = 3
        wizard.action_update_qty_line()
        wizard.on_barcode_scanned(barcode_mixed[1])
        wizard.on_barcode_scanned(self.product_04.barcode)
        wizard.product_qty = 4
        wizard.action_update_qty_line()
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        self.assertEqual(len(wizard.confirm_line_ids), 4)
        self.assertEqual(wizard.confirm_line_ids[0].qty, 4)
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.confirm_line_ids[2].qty, 3)
        self.assertEqual(wizard.confirm_line_ids[3].qty, 4)
        wizard.confirm_line_ids[3].action_remove_line()
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.line_ids[0].qty, 4)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        wizard.confirm_line_ids[2].action_remove_line()
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.line_ids[1].qty, 3)
        self.assertEqual(wizard.line_ids[0].qty, 4)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.product_qty = 3
        wizard.action_update_qty_line()
        wizard.on_barcode_scanned(barcode_mixed[1])
        wizard.on_barcode_scanned(self.product_04.barcode)
        wizard.product_qty = 4
        wizard.action_update_qty_line()
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        self.assertEqual(len(wizard.confirm_line_ids), 4)
        self.assertEqual(wizard.confirm_line_ids[0].qty, 4)
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.confirm_line_ids[2].qty, 3)
        self.assertEqual(wizard.confirm_line_ids[3].qty, 4)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 2)
        self.assertEqual(wizard.pallet_mode, 'complete_empty_mode')
        wizard.pallet_mode = 'individual_mode'
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.on_barcode_scanned(wizard.confirm_line_ids[0].barcode)
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(wizard.confirm_line_ids[1].barcode)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[1])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[3].pallet_barcode, barcode_pallet[1])
        self.assertFalse(wizard.reorganize_packages)
        wizard.reorganize_packages = True
        wizard._onchange_reorganize_packages()
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.on_barcode_scanned(barcode_mixed[1])
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.button_reorganize_packages()
        self.assertFalse(wizard.reorganize_packages)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[1])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[1])
        self.assertEqual(
            wizard.confirm_line_ids[3].pallet_barcode, barcode_pallet[0])
        self.assertEqual(wizard.line_ids[0].qty, 0)
        self.assertEqual(wizard.line_ids[1].qty, 0)
        self.assertEqual(len(wizard.confirm_line_ids), 4)
        self.assertEqual(wizard.confirm_line_ids[0].qty, 4)
        self.assertEqual(wizard.confirm_line_ids[1].qty, 6)
        self.assertEqual(wizard.confirm_line_ids[2].qty, 3)
        self.assertEqual(wizard.confirm_line_ids[3].qty, 4)

    def test_stock_barcodes_exceeds_qty_button_update_qty(self):
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_03, location, 50)
        self.create_inventory(self.product_04, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 20,
                    'product_uom_qty': 3,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.product_qty = 4
        wizard.action_update_qty_line()
        self.assertEqual(wizard.message_type, 'error')
        self.assertIn(
            'Selected qty exceeds requested qty in picking', wizard.message)
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].qty, 1)

    def test_stock_barcodes_read_all_boxes_same_time_packaged_container(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        wizard_mixed_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed_02.action_print()
        barcode_mixed_02 = wizard_mixed_02.get_barcodes()
        self.assertEqual(len(barcode_mixed_02), 1)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 1)
        wizard_pallet_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'pallet',
        })
        wizard_pallet_02.action_print()
        barcode_pallet_02 = wizard_pallet_02.get_barcodes()
        self.assertEqual(len(barcode_pallet_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        self.create_inventory(self.product_04, location, 50)
        self.create_inventory(self.product_05, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 2,
                }),
                (0, 0, {
                    'product_id': self.product_04.id,
                    'price_unit': 60,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_05.id,
                    'price_unit': 70,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 5)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        self.assertEqual(wizard.pallet_mode, 'complete_empty_mode')
        wizard.pallet_mode = 'individual_mode'
        self.assertEqual(wizard.pallet_mode, 'individual_mode')
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(wizard.pallet_barcode, barcode_pallet[0])
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        wizard.on_barcode_scanned(self.product_04.barcode)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_04)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcode_mixed[0])
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(wizard.pallet_barcode, barcode_pallet[0])
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.on_barcode_scanned(barcode_pallet_02[0])
        self.assertEqual(wizard.pallet_barcode, barcode_pallet_02[0])
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        wizard.on_barcode_scanned(barcode_mixed_02[0])
        wizard.on_barcode_scanned(self.product_05.barcode)
        self.assertEqual(len(wizard.confirm_line_ids), 4)
        wizard.on_barcode_scanned(self.product_03.barcode)
        self.assertEqual(wizard.product_packaging, self.product_03)
        self.assertEqual(wizard.product_qty, 1)
        wizard.product_qty = 2
        wizard.action_update_qty_line()
        wizard.on_barcode_scanned(barcode_mixed_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 5)
        wizard.on_barcode_scanned(barcode_pallet_02[0])
        lines_container_01 = wizard.confirm_line_ids.filtered(
            lambda ln: ln.pallet_barcode == barcode_pallet[0])
        lines_container_02 = wizard.confirm_line_ids.filtered(
            lambda ln: ln.pallet_barcode == barcode_pallet_02[0])
        self.assertEqual(len(lines_container_01), 2)
        self.assertEqual(len(lines_container_02), 3)
        self.assertEqual(sum(lines_container_01.mapped('qty')), 13)
        self.assertEqual(sum(lines_container_02.mapped('qty')), 9)
        wizard.confirm_line_ids[4].action_remove_line()
        wizard.confirm_line_ids[3].action_remove_line()
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        res_lines = wizard.line_ids.filtered(lambda ln: ln.qty > 0)
        self.assertEqual(len(res_lines), 2)
        self.assertEqual(res_lines[0].qty, 1)
        self.assertEqual(res_lines[1].qty, 2)
        wizard.on_barcode_scanned(barcode_pallet_02[0])
        self.assertEqual(wizard.pallet_barcode, barcode_pallet_02[0])
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.product_qty = 2
        wizard.action_update_qty_line()
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 4)
        wizard.on_barcode_scanned(barcode_pallet_02[0])
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_05.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 5)
        lines_container_02 = wizard.confirm_line_ids.filtered(
            lambda ln: ln.pallet_barcode == barcode_pallet_02[0])
        self.assertEqual(len(lines_container_02), 3)

    def test_stock_barcodes_mixed_packages_different_containers_01(self):
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 2)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 2)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_04, location, 50)
        self.create_inventory(self.product_05, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_04.id,
                    'price_unit': 60,
                    'product_uom_qty': 2,
                }),
                (0, 0, {
                    'product_id': self.product_05.id,
                    'price_unit': 70,
                    'product_uom_qty': 2,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        self.assertEqual(wizard.pallet_mode, 'complete_empty_mode')
        wizard.pallet_mode = 'individual_mode'
        self.assertEqual(wizard.pallet_mode, 'individual_mode')
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard.on_barcode_scanned(self.product_04.barcode)
        wizard.product_qty = 2
        wizard.action_update_qty_line()
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcode_mixed[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 2)
        self.assertEqual(wizard.pallet_barcode, barcode_pallet[0])
        wizard.on_barcode_scanned(barcode_mixed[1])
        wizard.on_barcode_scanned(self.product_05.barcode)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcode_mixed[1])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 1)
        wizard.on_barcode_scanned(barcode_mixed[1])
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertFalse(wizard.pallet_barcode)
        wizard.on_barcode_scanned(barcode_pallet[1])
        wizard.on_barcode_scanned(barcode_mixed[1])
        wizard.on_barcode_scanned(self.product_05.barcode)
        wizard.on_barcode_scanned(barcode_mixed[1])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[1])
        self.assertEqual(wizard.confirm_line_ids[2].barcode, barcode_mixed[1])
        self.assertEqual(wizard.confirm_line_ids[2].qty, 1)
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_05)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_05)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcode_mixed[1])
        self.assertEqual(wizard.confirm_line_ids[2].barcode, barcode_mixed[1])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[1])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[1])

    def test_stock_barcodes_mixed_packages_different_containers_02(self):
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 2)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 2)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_04, location, 50)
        self.create_inventory(self.product_05, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_04.id,
                    'price_unit': 60,
                    'product_uom_qty': 2,
                }),
                (0, 0, {
                    'product_id': self.product_05.id,
                    'price_unit': 70,
                    'product_uom_qty': 2,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        self.assertEqual(wizard.pallet_mode, 'complete_empty_mode')
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard.on_barcode_scanned(self.product_04.barcode)
        wizard.product_qty = 2
        wizard.action_update_qty_line()
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcode_mixed[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 2)
        self.assertFalse(wizard.confirm_line_ids[0].pallet_barcode)
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        wizard.on_barcode_scanned(barcode_mixed[1])
        wizard.on_barcode_scanned(self.product_05.barcode)
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertFalse(wizard.confirm_line_ids[1].pallet_barcode)
        wizard.on_barcode_scanned(barcode_mixed[1])
        wizard.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcode_mixed[1])
        self.assertEqual(wizard.confirm_line_ids[1].qty, 1)
        wizard.on_barcode_scanned(barcode_mixed[1])
        wizard.on_barcode_scanned(self.product_05.barcode)
        wizard.on_barcode_scanned(barcode_mixed[1])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertFalse(wizard.confirm_line_ids[2].pallet_barcode)
        self.assertEqual(wizard.confirm_line_ids[2].barcode, barcode_mixed[1])
        self.assertEqual(wizard.confirm_line_ids[2].qty, 1)
        wizard.on_barcode_scanned(barcode_pallet[1])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[1])
        self.assertEqual(wizard.confirm_line_ids[1].product_id, self.product_05)
        self.assertEqual(wizard.confirm_line_ids[2].product_id, self.product_05)
        self.assertEqual(wizard.confirm_line_ids[1].barcode, barcode_mixed[1])
        self.assertEqual(wizard.confirm_line_ids[2].barcode, barcode_mixed[1])
        self.assertEqual(
            wizard.confirm_line_ids[1].pallet_barcode, barcode_pallet[0])
        self.assertEqual(
            wizard.confirm_line_ids[2].pallet_barcode, barcode_pallet[1])
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.button_validate_dummy_scan()
        self.assertIn('must have same container.', result.exception.name)

    def test_read_repeat_dummy_label(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 24,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        self.assertEqual(wizard.pallet_mode, 'complete_empty_mode')
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)

    def test_stock_barcodes_check_log_dummy_others_pickings_dummy_01(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        sale_01 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
            ],
        })
        sale_02 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
            ],
        })
        sale_01.action_confirm()
        self.assertEqual(sale_01.state, 'sale')
        self.assertEqual(len(sale_01.picking_ids), 1)
        picking_01 = sale_01.picking_ids[0]
        picking_01.action_confirm()
        picking_01.action_assign()
        action_01 = picking_01.action_barcode_scan_dummy_label()
        wizard_01 = self.env['stock.barcodes.dummy.label'].browse(
            action_01['res_id'])
        self.assertEqual(len(wizard_01.line_ids), 1)
        self.assertEqual(len(wizard_01.confirm_line_ids), 0)
        self.assertEqual(wizard_01.pallet_mode, 'complete_empty_mode')
        wizard_01._origin = wizard_01
        wizard_01.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard_01.confirm_line_ids), 1)
        self.assertEqual(wizard_01.confirm_line_ids[0].barcode, barcodes_01[0])
        sale_02.action_confirm()
        self.assertEqual(sale_02.state, 'sale')
        self.assertEqual(len(sale_02.picking_ids), 1)
        picking_02 = sale_02.picking_ids[0]
        picking_02.action_confirm()
        picking_02.action_assign()
        action_02 = picking_02.action_barcode_scan_dummy_label()
        wizard_02 = self.env['stock.barcodes.dummy.label'].browse(
            action_02['res_id'])
        self.assertEqual(len(wizard_02.line_ids), 1)
        self.assertEqual(len(wizard_02.confirm_line_ids), 0)
        wizard_02._origin = wizard_02
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('active', '=', True),
            ('picking_id', '!=', picking_02.id),
            '|',
            ('barcode', '=', barcodes_01[0]),
            ('pallet_barcode', '=', barcodes_01[0]),
        ])
        self.assertTrue(logs)
        wizard_02.on_barcode_scanned(barcodes_01[0])
        self.assertEqual('error', wizard_02.message_type)
        self.assertIn(
            f'Barcode: {barcodes_01[0]} (Barcode {barcodes_01[0]}'
            f' is already in use in the picking {picking_01.name})',
            wizard_02.message)

    def test_stock_barcodes_check_log_dummy_others_pickings_mixed_box_02(self):
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_04, location, 50)
        sale_01 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_04.id,
                    'price_unit': 60,
                    'product_uom_qty': 2,
                }),
            ],
        })
        sale_02 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_04.id,
                    'price_unit': 60,
                    'product_uom_qty': 2,
                }),
            ],
        })
        sale_01.action_confirm()
        sale_02.action_confirm()
        self.assertEqual(sale_01.state, 'sale')
        self.assertEqual(sale_02.state, 'sale')
        self.assertEqual(len(sale_01.picking_ids), 1)
        self.assertEqual(len(sale_02.picking_ids), 1)
        picking_01 = sale_01.picking_ids[0]
        picking_02 = sale_02.picking_ids[0]
        picking_01.action_confirm()
        picking_01.action_assign()
        picking_02.action_confirm()
        picking_02.action_assign()
        action_01 = picking_01.action_barcode_scan_dummy_label()
        action_02 = picking_02.action_barcode_scan_dummy_label()
        wizard_01 = self.env['stock.barcodes.dummy.label'].browse(
            action_01['res_id'])
        wizard_02 = self.env['stock.barcodes.dummy.label'].browse(
            action_02['res_id'])
        self.assertEqual(len(wizard_01.line_ids), 1)
        self.assertEqual(len(wizard_01.confirm_line_ids), 0)
        self.assertEqual(wizard_01.pallet_mode, 'complete_empty_mode')
        wizard_01._origin = wizard_01
        wizard_01.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard_01.confirm_line_ids), 0)
        wizard_01.on_barcode_scanned(self.product_04.barcode)
        wizard_01.product_qty = 2
        wizard_01.action_update_qty_line()
        self.assertEqual(len(wizard_01.confirm_line_ids), 1)
        self.assertEqual(
            wizard_01.confirm_line_ids[0].barcode, barcode_mixed[0])
        self.assertEqual(wizard_01.confirm_line_ids[0].qty, 2)
        self.assertFalse(wizard_01.confirm_line_ids[0].pallet_barcode)
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('active', '=', True),
            ('picking_id', '!=', picking_02.id),
            '|',
            ('barcode', '=', barcode_mixed[0]),
            ('pallet_barcode', '=', barcode_mixed[0]),
        ])
        self.assertTrue(logs)
        wizard_02._origin = wizard_01
        wizard_02.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual('error', wizard_02.message_type)
        self.assertIn(f'Barcode: {barcode_mixed[0]} (Barcode {barcode_mixed[0]}'
                      f' is already in use in the picking {picking_01.name})',
                      wizard_02.message)

    def test_stock_barcodes_check_log_dummy_others_pickings_pallet(self):
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 1)
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 2)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        sale_01 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
            ],
        })
        sale_02 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
            ],
        })
        sale_01.action_confirm()
        self.assertEqual(sale_01.state, 'sale')
        self.assertEqual(len(sale_01.picking_ids), 1)
        picking_01 = sale_01.picking_ids[0]
        picking_01.action_confirm()
        picking_01.action_assign()
        action_01 = picking_01.action_barcode_scan_dummy_label()
        wizard_01 = self.env['stock.barcodes.dummy.label'].browse(
            action_01['res_id'])
        self.assertEqual(len(wizard_01.line_ids), 1)
        self.assertEqual(len(wizard_01.confirm_line_ids), 0)
        self.assertEqual(wizard_01.pallet_mode, 'complete_empty_mode')
        wizard_01._origin = wizard_01
        wizard_01.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard_01.confirm_line_ids), 1)
        self.assertEqual(wizard_01.confirm_line_ids[0].barcode, barcodes_01[0])
        wizard_01.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual(
            wizard_01.confirm_line_ids[0].pallet_barcode, barcode_pallet[0])
        sale_02.action_confirm()
        self.assertEqual(sale_02.state, 'sale')
        self.assertEqual(len(sale_02.picking_ids), 1)
        picking_02 = sale_02.picking_ids[0]
        picking_02.action_confirm()
        picking_02.action_assign()
        action_02 = picking_02.action_barcode_scan_dummy_label()
        wizard_02 = self.env['stock.barcodes.dummy.label'].browse(
            action_02['res_id'])
        self.assertEqual(len(wizard_02.line_ids), 1)
        self.assertEqual(len(wizard_02.confirm_line_ids), 0)
        wizard_02._origin = wizard_02
        wizard_02.on_barcode_scanned(barcodes_01[1])
        logs = self.env['stock.barcodes.dummy.log'].search([
            ('active', '=', True),
            ('picking_id', '!=', picking_02.id),
            '|',
            ('barcode', '=', barcode_pallet[0]),
            ('pallet_barcode', '=', barcode_pallet[0]),
        ])
        self.assertTrue(logs)
        wizard_02.on_barcode_scanned(barcode_pallet[0])
        self.assertEqual('error', wizard_02.message_type)
        self.assertIn(f'Barcode: {barcode_pallet[0]} (Barcode {barcode_pallet[0]}'
                      f' is already in use in the picking {picking_01.name})',
                      wizard_02.message)

    def test_scan_twice_the_same_dummy_and_scan_the_same_in_another_picking(self):
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_01.id,
            'packaging_id': self.product_01.packaging_ids[0].id,
            'lot_id': self.lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product_02.id,
            'packaging_id': self.product_02.packaging_ids[0].id,
            'lot_id': self.lot_02.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        self.create_inventory(self.product_03, location, 50)
        self.create_inventory(self.product_04, location, 50)
        self.create_inventory(self.product_05, location, 50)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_04.id,
                    'price_unit': 60,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_05.id,
                    'price_unit': 70,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 4)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        self.assertEqual(wizard.confirm_line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.confirm_line_ids[0].barcode, barcodes_01[0])
        self.assertEqual(wizard.confirm_line_ids[0].qty, 12)
        wizard_line_01 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_01)
        self.assertEqual(wizard_line_01.qty, 0)
        wizard_mixed = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed.action_print()
        barcode_mixed = wizard_mixed.get_barcodes()
        self.assertEqual(len(barcode_mixed), 1)
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        wizard_mixed_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard_mixed_02.action_print()
        barcode_mixed_02 = wizard_mixed_02.get_barcodes()
        self.assertEqual(len(barcode_mixed_02), 1)
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        wizard.on_barcode_scanned(barcode_mixed_02[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(self.product_04.barcode)
        wizard.on_barcode_scanned(barcode_mixed_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        self.assertEqual(wizard.confirm_line_ids[0].dummy_type, 'dummy')
        self.assertEqual(wizard.confirm_line_ids[1].dummy_type, 'mixed_package')
        self.assertEqual(wizard.confirm_line_ids[2].dummy_type, 'mixed_package')
        wizard_line_03 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_03)
        self.assertEqual(wizard_line_03.qty, 0)
        wizard_line_04 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_04)
        self.assertEqual(wizard_line_04.qty, 0)
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        wizard.on_barcode_scanned(barcode_mixed_02[0])
        wizard.on_barcode_scanned(self.product_05.barcode)
        wizard.on_barcode_scanned(barcode_mixed_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 4)
        picking_01 = wizard.picking_id
        wizard_line_05 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_05)
        self.assertEqual(wizard_line_05.qty, 0)
        self.assertEqual(
            len(wizard.line_ids.filtered(lambda ln: ln.qty != 0)), 0)
        wizard_pallet = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'pallet',
        })
        wizard_pallet.action_print()
        barcode_pallet = wizard_pallet.get_barcodes()
        self.assertEqual(len(barcode_pallet), 1)
        wizard.on_barcode_scanned(barcode_pallet[0])
        wizard.button_validate_dummy_scan()
        self.assertTrue(len(picking.move_line_ids) > 0)
        self.assertEqual(
            sum(picking.move_line_ids.mapped('product_uom_qty')),
            sum(picking.move_line_ids.mapped('qty_done')))
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 50,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_04.id,
                    'price_unit': 60,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_05.id,
                    'price_unit': 70,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 4)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard._origin = wizard
        wizard.on_barcode_scanned(barcodes_01[0])
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard.on_barcode_scanned(barcodes_02[0])
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard.on_barcode_scanned(barcode_mixed[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(self.product_04.barcode)
        wizard.on_barcode_scanned(barcode_mixed[0])
        self.assertEqual(len(wizard.confirm_line_ids), 2)
        wizard.on_barcode_scanned(barcode_mixed_02[0])
        wizard.on_barcode_scanned(self.product_03.barcode)
        wizard.on_barcode_scanned(self.product_04.barcode)
        wizard.on_barcode_scanned(barcode_mixed_02[0])
        self.assertEqual(wizard.message, (
            'Barcode: %s (Barcode %s already validated in picking %s)'
        ) % (barcode_mixed_02[0], barcode_mixed_02[0], picking_01.name))
        self.assertEqual(len(wizard.confirm_line_ids), 2)

    def test_open_wizard_scan_in_picking_with_product_without_reserved(self):
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location, 50, self.lot_01.id)
        self.create_inventory(self.product_02, location, 50, self.lot_02.id)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': 20,
                    'product_uom_qty': 12,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 30,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': 40,
                    'product_uom_qty': 4,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.picking_ids), 1)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        action = picking.action_barcode_scan_dummy_label()
        self.assertEqual(len(picking.move_lines), 3)
        self.assertNotEqual(picking.move_lines[0].reserved_availability, 0)
        self.assertNotEqual(picking.move_lines[1].reserved_availability, 0)
        self.assertEqual(picking.move_lines[2].reserved_availability, 0)
        wizard = self.env['stock.barcodes.dummy.label'].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(wizard.partner_id, picking.partner_id)
        self.assertEqual(len(wizard.line_ids), 2)
