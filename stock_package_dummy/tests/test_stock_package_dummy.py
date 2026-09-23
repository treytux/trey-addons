###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestStockPackageDummy(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env.ref('product.product_product_8')
        self.product.packaging_ids = [(0, 0, {
            'name': 'Box 12',
            'qty': 12,
            'barcode': '1234567890123',
        })]
        self.lot = self.env['stock.production.lot'].create({
            'product_id': self.product.id,
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

    def test_barcodes(self):
        dummy_obj = self.env['stock.quant.package_dummy']
        barcodes = dummy_obj._get_barcodes('1234567890', 2, 1)
        self.assertEquals(len(barcodes), 2)
        self.assertEquals(barcodes[0], '123456789000000012')
        barcodes = dummy_obj._get_barcodes('1234567890', 2)
        self.assertEquals(barcodes[0], '123456789000000005')
        self.assertEquals(barcodes[1], '123456789000000012')
        self.env['ir.config_parameter'].set_param(
            'stock_package_dummy.prefix', '123456789012345678')
        wizard = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 100,
            'product_id': self.product.id,
            'dummy_type': 'dummy',
        })
        with self.assertRaises(exceptions.UserError):
            wizard.action_print()
        self.env['ir.config_parameter'].set_param(
            'stock_package_dummy.prefix', '999999')
        value = self.env['ir.config_parameter'].get_param(
            'stock_package_dummy.prefix')
        self.assertEquals(value, '999999')
        wizard = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 100,
            'product_id': self.product.id,
            'dummy_type': 'dummy',
        })
        wizard.action_print()
        barcodes = wizard.get_barcodes()
        self.assertTrue(barcodes[0].startswith(self.dummy_type.prefix))
        self.assertEquals(len(barcodes), 100)
        sizes = list(set([len(b) for b in barcodes]))
        self.assertEquals(sizes, [18])

    def test_wizard_create_stock(self):
        wizard = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 10,
            'product_id': self.product.id,
            'packaging_id': self.product.packaging_ids[0].id,
            'lot_id': self.lot.id,
            'dummy_type': 'dummy',
        })
        wizard.action_print()
        self.assertTrue(wizard.dummy_id.barcode_prefix)
        barcodes = wizard.get_barcodes()
        self.assertEquals(len(barcodes), 10)
        self.assertTrue(
            all([b.startswith(self.dummy_type.prefix) for b in barcodes]))
        wizard.action_print()
        dummy = self.env['stock.quant.package_dummy'].search_from_barcode(
            barcodes[0])
        self.assertTrue(dummy)
        self.assertIn(dummy.barcode_prefix, barcodes[0])
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product, location, 12)
        wizard_create = self.env['stock.package_dummy.read'].create({
            'location_id': location.id,
            'barcodes': '\n'.join([barcodes[0], '000'])
        })
        wizard_create.simulate()
        self.assertIn('000', wizard_create.line_ids[0].barcode)
        wizard_create.action = 'not_exist'
        with self.assertRaises(exceptions.UserError):
            wizard_create.action_run()
        wizard_create.write({
            'action': 'stock',
            'barcodes': barcodes[0],
        })
        wizard_create.action_simulate()
        wizard_create.action_run()
        self.assertTrue(wizard_create.picking_id)
        self.assertEquals(wizard_create.picking_id.state, 'done')
        packages = wizard_create.picking_id.move_line_ids.mapped(
            'result_package_id')
        self.assertEquals(packages.quant_ids.quantity, 12)
        self.assertEquals(packages.quant_ids.product_id, self.product)
        self.assertEquals(packages.quant_ids.lot_id, self.lot)

    def test_create_dummy_with_other_lot_and_packaging(self):
        product = self.env.ref('product.product_product_5')
        wizard = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 10,
            'product_id': product.id,
            'packaging_id': self.product.packaging_ids[0].id,
            'lot_id': self.lot.id,
            'dummy_type': 'dummy',
        })
        with self.assertRaises(exceptions.ValidationError):
            wizard.action_print()
        wizard = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 10,
            'product_id': product.id,
            'packaging_id': False,
            'lot_id': self.lot.id,
            'dummy_type': 'dummy',
        })
        with self.assertRaises(exceptions.ValidationError):
            wizard.action_print()
        wizard = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 10,
            'product_id': product.id,
            'packaging_id': self.product.packaging_ids[0].id,
            'lot_id': False,
            'dummy_type': 'dummy',
        })
        with self.assertRaises(exceptions.ValidationError):
            wizard.action_print()
        wizard = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 10,
            'product_id': product.id,
            'packaging_id': False,
            'lot_id': False,
            'dummy_type': 'dummy',
        })
        wizard.action_print()
        barcodes = wizard.get_barcodes()
        dummy = self.env['stock.quant.package_dummy'].search_from_barcode(
            barcodes[0])
        self.assertFalse(dummy.lot_id)
        self.assertFalse(dummy.packaging_id)
        self.assertEquals(dummy.product_id, product)
        self.assertEquals(dummy.qty, 10)
        self.assertEquals(len(dummy.barcodes.split('\n')), 10)
        with self.assertRaises(exceptions.ValidationError):
            dummy = self.env['stock.quant.package_dummy'].create({
                'qty': 10,
                'product_id': product.id,
                'lot_id': self.lot.id,
            })
        with self.assertRaises(exceptions.ValidationError):
            dummy = self.env['stock.quant.package_dummy'].create({
                'qty': 10,
                'product_id': product.id,
                'lot_id': self.lot.id,
            })
        with self.assertRaises(exceptions.ValidationError):
            dummy = self.env['stock.quant.package_dummy'].create({
                'qty': 10,
                'product_id': product.id,
                'packaging_id': self.product.packaging_ids[0].id,
            })
        dummy = self.env['stock.quant.package_dummy'].create({
            'qty': 10,
            'product_id': product.id,
        })

    def test_wizard_create_stock_picking(self):
        product = self.env.ref('product.product_product_5')
        wizard = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 10,
            'product_id': product.id,
            'dummy_type': 'dummy',
        })
        wizard.action_print()
        self.assertTrue(wizard.dummy_id.barcode_prefix)
        bad_barcodes = wizard.get_barcodes()
        wizard = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 10,
            'product_id': self.product.id,
            'packaging_id': self.product.packaging_ids[0].id,
            'lot_id': self.lot.id,
            'dummy_type': 'dummy',
        })
        wizard.action_print()
        self.assertTrue(wizard.dummy_id.barcode_prefix)
        barcodes = wizard.get_barcodes()
        self.assertEquals(len(barcodes), 10)
        self.assertTrue(
            all([b.startswith(
                wizard.dummy_id.barcode_prefix) for b in barcodes]))
        wizard.action_print()
        dummy = self.env['stock.quant.package_dummy'].search_from_barcode(
            barcodes[0])
        self.assertTrue(dummy)
        self.assertIn(dummy.barcode_prefix, barcodes[0])
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product, location, 100, self.lot.id)
        stock_location = self.env.ref('stock.stock_location_stock')
        picking = self.env['stock.picking'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'location_id': stock_location.id,
            'location_dest_id': stock_location.id,
            'picking_type_id': self.env.ref('stock.picking_type_internal').id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_uom': self.product.uom_id.id,
                    'product_uom_qty': 12,
                    'procure_method': 'make_to_stock',
                }),
            ],
        })
        picking.action_confirm()
        picking.action_assign()
        wizard_create = self.env['stock.package_dummy.read'].create({
            'location_id': location.id,
            'action': 'stock_picking',
            'picking_id': picking.id,
            'barcodes': '\n'.join([bad_barcodes[0], bad_barcodes[1]])
        })
        wizard_create.simulate()
        errors = wizard_create.line_ids.mapped('name')
        self.assertTrue(any(
            ['The product is not required' in e for e in errors]))
        wizard_create.write({
            'barcodes': barcodes[0],
        })
        wizard_create.action_simulate()
        self.assertFalse(wizard_create.line_ids)
        wizard_create.action_run()
        self.assertTrue(wizard_create.picking_id)
        picking.action_done()
        packages = picking.mapped(
            'move_lines.move_line_ids.result_package_id')
        self.assertEquals(packages.quant_ids.quantity, 12)
        self.assertEquals(packages.quant_ids.product_id, self.product)
        self.assertEquals(packages.quant_ids.lot_id, self.lot)
        self.assertEquals(picking.state, 'done')

    def test_wizard_create_stock_picking_without_packaging(self):
        self.product.packaging_ids = [(6, 0, [])]
        wizard = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 10,
            'product_id': self.product.id,
            'dummy_type': 'dummy',
        })
        wizard.action_print()
        barcodes = wizard.get_barcodes()
        location = self.env.ref('stock.stock_location_stock')
        location_child = location.copy({
            'name': 'Child',
            'location_id': location.id,
        })
        location_customer = self.env.ref('stock.stock_location_customers')
        self.create_inventory(self.product, location_child, 100)
        picking = self.env['stock.picking'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'location_id': location.id,
            'location_dest_id': location_customer.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_uom': self.product.uom_id.id,
                    'product_uom_qty': 10,
                    'procure_method': 'make_to_stock',
                }),
            ],
        })
        picking.action_confirm()
        picking.action_assign()
        self.assertEquals(len(picking.mapped('move_lines.move_line_ids')), 1)
        self.assertEquals(picking.move_line_ids.location_id, location_child)
        wizard_create = self.env['stock.package_dummy.read'].create({
            'location_id': location.id,
            'action': 'stock_picking',
            'picking_id': picking.id,
            'barcodes': '\n'.join([barcodes[0], barcodes[1]])
        })
        wizard_create.simulate()
        self.assertEquals(len(wizard_create.line_ids), 0)
        wizard_create.action_run()
        self.assertTrue(wizard_create.picking_id)
        move_lines = picking.mapped('move_lines.move_line_ids')
        self.assertEquals(len(move_lines), 3)
        self.assertEquals(sum(move_lines.mapped('product_uom_qty')), 10)
        self.assertEquals(sum(move_lines.mapped('qty_done')), 2)
        self.assertEquals(len(move_lines.mapped('result_package_id')), 2)
        move_lines[0].qty_done = 8
        self.assertEquals(sum(move_lines.mapped('qty_done')), 10)
        self.assertEquals(self.product.qty_available, 100)
        picking.action_done()
        self.assertEquals(self.product.qty_available, 90)
        packages = picking.mapped('move_lines.move_line_ids.result_package_id')
        self.assertEquals(packages[0].quant_ids.quantity, 1)
        self.assertEquals(packages[0].quant_ids.product_id, self.product)
        self.assertEquals(picking.state, 'done')

    def test_wizard_create_all_product_reserved(self):
        wizard = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 10,
            'product_id': self.product.id,
            'packaging_id': self.product.packaging_ids[0].id,
            'lot_id': self.lot.id,
            'dummy_type': 'dummy',
        })
        wizard.action_print()
        barcodes = wizard.get_barcodes()
        self.env['stock.quant.package_dummy'].search_from_barcode(barcodes[0])
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product, location, 12)
        picking = self.env['stock.picking'].create({
            'partner_id': self.env.ref('base.res_partner_12').id,
            'location_id': location.id,
            'location_dest_id': self.env.ref('stock.stock_location_output').id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_uom': self.product.uom_id.id,
                    'product_uom_qty': 12,
                    'procure_method': 'make_to_stock',
                }),
            ],
        })
        picking.action_confirm()
        picking.action_assign()
        wizard_create = self.env['stock.package_dummy.read'].create({
            'location_id': location.id,
            'barcodes': barcodes[0],
        })
        wizard_create.simulate()
        self.assertIn(barcodes[0], wizard_create.line_ids[0].barcode)
        errors = wizard_create.line_ids.mapped('name')
        self.assertTrue(any(['Not available' in e for e in errors]))
        with self.assertRaises(exceptions.UserError):
            wizard_create.action_run()

    def test_wizard_create_barcodes_not_found(self):
        location = self.env.ref('stock.stock_location_stock')
        wizard_create = self.env['stock.package_dummy.read'].create({
            'location_id': location.id,
            'barcodes': 'NO_EXIST\nOTHER_NOT_EXIST',
        })
        wizard_create.simulate()
        self.assertEquals(len(wizard_create.line_ids), 2)
        with self.assertRaises(exceptions.UserError):
            wizard_create.action_run()

    def test_wizard_create_simulation(self):
        wizard = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 2,
            'product_id': self.product.id,
            'packaging_id': self.product.packaging_ids[0].id,
            'lot_id': self.lot.id,
            'dummy_type': 'dummy',
        })
        wizard.action_print()
        barcodes = wizard.get_barcodes()
        location = self.env.ref('stock.stock_location_stock')
        wizard_create = self.env['stock.package_dummy.read'].create({
            'location_id': location.id,
            'barcodes': '\n'.join([barcodes[0], barcodes[0]]),
        })
        wizard_create.simulate()
        self.assertEquals(len(wizard_create.line_ids), 2)
        errors = wizard_create.line_ids.mapped('name')
        self.assertTrue(any(['Not available quantity' in e for e in errors]))
        self.create_inventory(self.product, location, 6)
        wizard_create.action_simulate()
        self.assertEquals(len(wizard_create.line_ids), 2)
        errors = wizard_create.line_ids.mapped('name')
        self.assertTrue(any(['Duplicate dummy' in e for e in errors]))
        self.assertTrue(any(['Not available quantity' in e for e in errors]))
        package = self.env['stock.quant.package'].create({
            'name': barcodes[0],
        })
        self.create_inventory(
            self.product, location, 12, package_id=package.id)
        wizard_create = self.env['stock.package_dummy.read'].create({
            'location_id': location.id,
            'barcodes': barcodes[0],
        })
        wizard_create.simulate()
        errors = wizard_create.line_ids.mapped('name')
        self.assertTrue(any(['Dummy label in use' in e for e in errors]))

    def test_wizard_unpackage(self):
        product = self.env.ref('product.product_product_5')
        wizard = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 10,
            'product_id': product.id,
            'dummy_type': 'dummy',
        })
        wizard.action_print()
        self.assertTrue(wizard.dummy_id.barcode_prefix)
        wizard.get_barcodes()
        wizard = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 12,
            'product_id': self.product.id,
            'lot_id': self.lot.id,
            'dummy_type': 'dummy',
        })
        wizard.action_print()
        barcodes = wizard.get_barcodes()
        dummy = self.env['stock.quant.package_dummy'].search_from_barcode(
            barcodes[0])
        self.assertTrue(dummy)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product, location, 12)
        wizard_create = self.env['stock.package_dummy.read'].create({
            'action': 'stock',
            'location_id': location.id,
            'barcodes': '\n'.join(barcodes),
        })
        wizard_create.action_simulate()
        wizard_create.action_run()
        self.assertTrue(wizard_create.picking_id)
        self.assertEquals(wizard_create.picking_id.state, 'done')
        packages = wizard_create.picking_id.move_line_ids.mapped(
            'result_package_id')
        self.assertEquals(packages.quant_ids.quantity, 12)
        self.assertEquals(packages.quant_ids.product_id, self.product)
        self.assertEquals(packages.quant_ids.lot_id, self.lot)

    def test_wizard_create_pallet_dummy(self):
        wizard = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'pallet',
        })
        wizard.action_print()
        self.assertTrue(wizard.dummy_id.barcode_prefix)
        barcodes = wizard.get_barcodes()
        self.assertEquals(len(barcodes), 1)
        self.assertTrue(
            all([b.startswith(self.pallet_type.prefix) for b in barcodes]))
        pallet = self.env['stock.quant.package_dummy'].search_from_barcode(
            barcodes[0])
        self.assertTrue(pallet)
        self.assertIn(pallet.barcode_prefix, barcodes[0])

    def test_wizard_create_mixed_package_dummy(self):
        wizard = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'dummy_type': 'mixed_package',
        })
        wizard.action_print()
        self.assertTrue(wizard.dummy_id.barcode_prefix)
        barcodes = wizard.get_barcodes()
        self.assertEquals(len(barcodes), 1)
        self.assertTrue(
            all([b.startswith(self.mixed_type.prefix) for b in barcodes]))
        dummy_obj = self.env['stock.quant.package_dummy']
        mixed_package = dummy_obj.search_from_barcode(
            barcodes[0])
        self.assertTrue(mixed_package)
        self.assertIn(mixed_package.barcode_prefix, barcodes[0])

    def test_dummy_unique_type_constraint(self):
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['stock.quant_package.dummy.type'].create({
                'name': 'Dummy duplicated test',
                'prefix': '4721357',
                'dummy_type': 'dummy',
            })
        self.assertEquals(
            result.exception.name,
            'There is already a record with this selection in the company')
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['stock.quant_package.dummy.type'].create({
                'name': 'Mixed package duplicated test',
                'prefix': '6985214',
                'dummy_type': 'mixed_package',
            })
        self.assertEquals(
            result.exception.name,
            'There is already a record with this selection in the company')
        with self.assertRaises(exceptions.ValidationError) as result:
            self.env['stock.quant_package.dummy.type'].create({
                'name': 'Pallet duplicated test',
                'prefix': '8597654',
                'dummy_type': 'pallet',
            })
        self.assertEquals(
            result.exception.name,
            'There is already a record with this selection in the company')

    def test_dummy_read_reserved_qty_error_no_qty_enough_01(self):
        lot_01 = self.env['stock.production.lot'].create({
            'product_id': self.product.id,
        })
        wizard_01 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product.id,
            'packaging_id': self.product.packaging_ids[0].id,
            'lot_id': lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_01.action_print()
        barcodes_01 = wizard_01.get_barcodes()
        self.assertEqual(len(barcodes_01), 1)
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product, location, 23, lot_01.id)
        picking = self.env['stock.picking'].create({
            'partner_id': self.env.ref('base.res_partner_2').id,
            'location_id': location.id,
            'location_dest_id': location.id,
            'picking_type_id': self.env.ref('stock.picking_type_internal').id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_uom': self.product.uom_id.id,
                    'product_uom_qty': 12,
                    'procure_method': 'make_to_stock',
                }),
            ],
        })
        picking.action_confirm()
        self.assertEqual(picking.state, 'confirmed')
        picking.action_assign()
        self.assertEqual(picking.state, 'assigned')
        dummy = self.env['stock.quant.package_dummy'].search_from_barcode(
            barcodes_01[0])
        self.assertTrue(dummy)
        self.assertEqual(len(dummy), 1)
        self.assertEqual(dummy.product_id, self.product)
        available_qty = self.env['stock.quant']._get_available_quantity(
            dummy.product_id, location)
        self.assertEqual(available_qty, 11)
        need_qty = dummy.packaging_id and dummy.packaging_id.qty or 1
        self.assertEqual(need_qty, 12)
        wizard_read_01 = self.env['stock.package_dummy.read'].create({
            'location_id': location.id,
            'action': 'stock_picking',
            'picking_id': picking.id,
            'barcodes': barcodes_01[0],
        })
        wizard_read_01.simulate()
        errors = wizard_read_01.line_ids.mapped('name')
        self.assertFalse(
            any(['Not available quantity in' in e for e in errors]))
        self.product.packaging_ids = [(0, 0, {
            'name': 'Box 15',
            'qty': 15,
            'barcode': '9873216549518',
        })]
        self.assertEqual(len(self.product.packaging_ids), 2)
        wizard_02 = self.env['stock.package_dummy.print'].create({
            'qty_to_print': 1,
            'product_id': self.product.id,
            'packaging_id': self.product.packaging_ids[1].id,
            'lot_id': lot_01.id,
            'dummy_type': 'dummy',
        })
        wizard_02.action_print()
        barcodes_02 = wizard_02.get_barcodes()
        self.assertEqual(len(barcodes_02), 1)
        wizard_read_02 = self.env['stock.package_dummy.read'].create({
            'location_id': location.id,
            'action': 'stock_picking',
            'picking_id': picking.id,
            'barcodes': barcodes_02[0],
        })
        wizard_read_02.simulate()
        errors = wizard_read_02.line_ids.mapped('name')
        self.assertFalse(
            any(['Not available quantity in' in e for e in errors]))
        with self.assertRaises(exceptions.ValidationError):
            wizard_read_02.action_run()
