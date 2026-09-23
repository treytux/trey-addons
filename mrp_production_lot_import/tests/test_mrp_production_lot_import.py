###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestMrpProductionLotImport(TransactionCase):

    def setUp(self):
        super().setUp()
        product_obj = self.env['product.product']
        self.quant_obj = self.env['stock.quant']
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.mto_route = self.env.ref('stock.route_warehouse0_mto')
        self.product_table = product_obj.create({
            'name': 'Table',
            'type': 'product',
            'tracking': 'serial',
            'route_ids': [(6, 0, [self.mto_route.id])],
        })
        self.product_board = product_obj.create({
            'name': 'Table Board',
            'default_code': 'TABLEBOARD',
            'type': 'product',
            'tracking': 'serial',
        })
        self.product_table_leg = product_obj.create({
            'name': 'Table Leg',
            'type': 'product',
        })
        self.bom = self.env['mrp.bom'].create({
            'product_id': self.product_table.id,
            'product_tmpl_id': self.product_table.product_tmpl_id.id,
            'product_uom_id': self.product_table.uom_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.product_board.id,
                    'product_qty': 1,
                    'product_uom_id': self.product_board.uom_id.id,
                }),
                (0, 0, {
                    'product_id': self.product_table_leg.id,
                    'product_qty': 4,
                    'product_uom_id': self.product_table_leg.uom_id.id,
                }),
            ],
        })
        self.lot_1 = self.env['stock.lot'].create({
            'name': 'TABLEBOARD001',
            'product_id': self.product_board.id,
        })
        self.lot_2 = self.env['stock.lot'].create({
            'name': 'TABLEBOARD002',
            'product_id': self.product_board.id,
        })
        self.lot_3 = self.env['stock.lot'].create({
            'name': 'TABLEBOARD003',
            'product_id': self.product_board.id,
        })
        self.lot_4 = self.env['stock.lot'].create({
            'name': 'TABLEBOARD004',
            'product_id': self.product_board.id,
        })
        self.create_inventory(
            self.product_board, self.stock_location, 1, lot_id=self.lot_1.id)
        self.create_inventory(
            self.product_board, self.stock_location, 1, lot_id=self.lot_2.id)
        self.create_inventory(
            self.product_board, self.stock_location, 1, lot_id=self.lot_3.id)
        self.create_inventory(
            self.product_board, self.stock_location, 1, lot_id=self.lot_4.id)
        self.quant_obj._update_available_quantity(
            self.product_table_leg, self.stock_location, 16)
        self.leg_quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_table_leg.id),
            ('location_id', '=', self.stock_location.id),
        ])
        self.board_quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_board.id),
            ('location_id', '=', self.stock_location.id),
        ])
        self.table_quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_table.id),
            ('location_id', '=', self.stock_location.id),
        ])

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def create_inventory(self, product, location, qty, lot_id=False, package_id=False):
        domain = [
            ('product_id', '=', product.id),
            ('location_id', '=', location.id),
            ('lot_id', '=', lot_id),
            ('package_id', '=', package_id),
        ]
        quant = self.env['stock.quant'].search(domain, limit=1)
        if not quant:
            quant = self.env['stock.quant'].create({
                'product_id': product.id,
                'location_id': location.id,
                'lot_id': lot_id,
                'package_id': package_id,
            })
        quant.with_context(inventory_mode=True).write({
            'inventory_quantity': qty,
        })
        quant.action_apply_inventory()
        return quant

    def create_wizard(self, mo, xls_name):
        fname = self.get_sample(xls_name)
        file = base64.b64encode(open(fname, 'rb').read())
        wizard_obj = self.env['import.production.lots.wizard'].with_context({
            'active_id': mo.id,
            'active_ids': [mo.id],
        })
        return wizard_obj.create({
            'data_file': file,
        })

    def test_import_lot(self):
        xls_name = 'sample_import_lots.xls'
        mo = self.env['mrp.production'].create({
            'name': 'MO 1',
            'product_id': self.product_table.id,
            'product_uom_id': self.product_table.uom_id.id,
            'product_qty': 2.0,
            'bom_id': self.bom.id,
        })
        self.assertEqual(len(mo), 1)
        mo.action_confirm()
        mo.action_assign()
        lots = mo.move_raw_ids.mapped('move_line_ids.lot_id')
        self.assertEqual(lots[0], self.lot_1)
        self.assertEqual(lots[1], self.lot_2)
        wizard = self.create_wizard(mo, xls_name)
        wizard.produce_move_lines()
        mo.button_mark_done()
        lots = self.env['stock.lot'].search([
            ('product_id', '=', self.product_table.id),
        ])
        self.assertEqual(len(lots), 2)
        self.assertEqual(lots[0].name, 'TABLE001')
        self.assertEqual(lots[1].name, 'TABLE002')
        self.assertEqual(len(mo.finished_move_line_ids), 2)
        self.assertEqual(
            mo.finished_move_line_ids[0].product_id.id, self.product_table.id)
        self.assertEqual(
            mo.finished_move_line_ids[1].product_id.id, self.product_table.id)
        self.assertEqual(mo.finished_move_line_ids[0].qty_done, 1)
        self.assertEqual(mo.finished_move_line_ids[1].qty_done, 1)
        self.assertEqual(mo.finished_move_line_ids[0].lot_id, lots[0])
        self.assertEqual(mo.finished_move_line_ids[1].lot_id, lots[1])
        self.assertEqual(
            mo.move_raw_ids[0].product_id.id, self.product_board.id)
        self.assertEqual(
            mo.move_raw_ids[1].product_id.id, self.product_table_leg.id)
        self.assertEqual(mo.move_raw_ids[0].product_uom_qty, 2)
        self.assertEqual(mo.move_raw_ids[1].product_uom_qty, 8)
        self.assertEqual(mo.move_raw_ids[0].quantity_done, 2)
        self.assertEqual(mo.move_raw_ids[1].quantity_done, 8)
        leg_quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_table_leg.id),
            ('location_id', '=', self.stock_location.id),
        ])
        board_quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_board.id),
            ('location_id', '=', self.stock_location.id),
        ])
        table_quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_table.id),
            ('location_id', '=', self.stock_location.id),
        ])
        self.assertEqual(leg_quant.quantity, 8)
        self.assertEqual(sum(board_quant.mapped('quantity')), 2)
        self.assertEqual(sum(table_quant.mapped('quantity')), 2)

    def test_partials_import_lot(self):
        xls_name = 'sample_import_lots.xls'
        mo = self.env['mrp.production'].create({
            'name': 'MO 1',
            'product_id': self.product_table.id,
            'product_uom_id': self.product_table.uom_id.id,
            'product_qty': 4.0,
            'bom_id': self.bom.id,
        })
        self.assertEqual(len(mo), 1)
        mo.action_confirm()
        mo.action_assign()
        lots = mo.move_raw_ids.mapped('move_line_ids.lot_id')
        self.assertEqual(lots[0], self.lot_1)
        self.assertEqual(lots[1], self.lot_2)
        self.assertEqual(lots[2], self.lot_3)
        self.assertEqual(lots[3], self.lot_4)
        wizard = self.create_wizard(mo, xls_name)
        wizard.produce_move_lines()
        lots = self.env['stock.lot'].search([
            ('product_id', '=', self.product_table.id),
        ])
        self.assertEqual(len(lots), 2)
        self.assertEqual(lots[0].name, 'TABLE001')
        self.assertEqual(lots[1].name, 'TABLE002')
        self.assertEqual(len(mo.finished_move_line_ids), 2)
        self.assertEqual(
            mo.finished_move_line_ids[0].product_id.id, self.product_table.id)
        self.assertEqual(
            mo.finished_move_line_ids[1].product_id.id, self.product_table.id)
        self.assertEqual(mo.finished_move_line_ids[0].qty_done, 1)
        self.assertEqual(mo.finished_move_line_ids[1].qty_done, 1)
        self.assertEqual(mo.finished_move_line_ids[0].lot_id, lots[0])
        self.assertEqual(mo.finished_move_line_ids[1].lot_id, lots[1])
        self.assertEqual(
            mo.move_raw_ids[0].product_id.id, self.product_board.id)
        self.assertEqual(
            mo.move_raw_ids[1].product_id.id, self.product_table_leg.id)
        self.assertEqual(mo.move_raw_ids[0].product_uom_qty, 4)
        self.assertEqual(mo.move_raw_ids[1].product_uom_qty, 16)
        self.assertEqual(mo.move_raw_ids[0].quantity_done, 2)
        self.assertEqual(mo.move_raw_ids[1].quantity_done, 8)
        xls_name = 'sample_parcial_import_lots.xls'
        wizard = self.create_wizard(mo, xls_name)
        wizard.produce_move_lines()
        mo.button_mark_done()
        lots = self.env['stock.lot'].search([
            ('product_id', '=', self.product_table.id),
        ])
        self.assertEqual(len(lots), 4)
        self.assertEqual(lots[2].name, 'TABLE003')
        self.assertEqual(lots[3].name, 'TABLE004')
        self.assertEqual(len(mo.finished_move_line_ids), 4)
        self.assertEqual(
            mo.finished_move_line_ids[2].product_id.id, self.product_table.id)
        self.assertEqual(
            mo.finished_move_line_ids[3].product_id.id, self.product_table.id)
        self.assertEqual(mo.finished_move_line_ids[2].qty_done, 1)
        self.assertEqual(mo.finished_move_line_ids[3].qty_done, 1)
        self.assertEqual(mo.finished_move_line_ids[2].lot_id, lots[2])
        self.assertEqual(mo.finished_move_line_ids[3].lot_id, lots[3])
        self.assertEqual(mo.move_raw_ids[0].quantity_done, 4)
        self.assertEqual(mo.move_raw_ids[1].quantity_done, 16)
        leg_quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_table_leg.id),
            ('location_id', '=', self.stock_location.id),
        ])
        board_quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_board.id),
            ('location_id', '=', self.stock_location.id),
        ])
        table_quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_table.id),
            ('location_id', '=', self.stock_location.id),
        ])
        self.assertEqual(leg_quant.quantity, 0)
        self.assertEqual(sum(board_quant.mapped('quantity')), 0)
        self.assertEqual(sum(table_quant.mapped('quantity')), 4)

    def test_duplicate_import_lot(self):
        xls_name = 'sample_import_lots.xls'
        mo = self.env['mrp.production'].create({
            'name': 'MO 1',
            'product_id': self.product_table.id,
            'product_uom_id': self.product_table.uom_id.id,
            'product_qty': 2.0,
            'bom_id': self.bom.id,
        })
        self.assertEqual(len(mo), 1)
        mo.action_confirm()
        mo.action_assign()
        lots = mo.move_raw_ids.mapped('move_line_ids.lot_id')
        wizard = self.create_wizard(mo, xls_name)
        wizard.produce_move_lines()
        mo.button_mark_done()
        lots = self.env['stock.lot'].search([
            ('product_id', '=', self.product_table.id),
        ])
        self.assertEqual(len(lots), 2)
        self.assertEqual(lots[0].name, 'TABLE001')
        self.assertEqual(lots[1].name, 'TABLE002')
        mo_2 = self.env['mrp.production'].create({
            'name': 'MO 2',
            'product_id': self.product_table.id,
            'product_uom_id': self.product_table.uom_id.id,
            'product_qty': 2.0,
            'bom_id': self.bom.id,
        })
        self.assertEqual(len(mo_2), 1)
        mo_2.action_confirm()
        mo_2.action_assign()
        wizard_2 = self.create_wizard(mo_2, xls_name)
        wizard_2.produce_move_lines()
        with self.assertRaises(Exception) as result:
            mo_2.button_mark_done()
        self.assertTrue(isinstance(result.exception, (ValidationError, UserError)))
        self.assertIn(
            'TABLEBOARD001',
            result.exception.args[0],
        )
        mo_2.move_raw_ids[0].move_line_ids[0].lot_id = self.lot_3
        mo_2.move_raw_ids[0].move_line_ids[1].lot_id = self.lot_4
        with self.assertRaises(Exception) as result:
            mo_2.button_mark_done()
        self.assertTrue(isinstance(result.exception, (ValidationError, UserError)))
        self.assertIn(
            'TABLE001',
            result.exception.args[0],
        )
        leg_quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_table_leg.id),
            ('location_id', '=', self.stock_location.id),
        ])
        board_quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_board.id),
            ('location_id', '=', self.stock_location.id),
        ])
        table_quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_table.id),
            ('location_id', '=', self.stock_location.id),
        ])
        self.assertEqual(leg_quant.quantity, 8)
        self.assertEqual(sum(board_quant.mapped('quantity')), 2)
        self.assertEqual(sum(table_quant.mapped('quantity')), 2)

    def test_excel_with_more_lines_than_mo(self):
        xls_name = 'sample_import_lots.xls'
        mo = self.env['mrp.production'].create({
            'name': 'MO 1',
            'product_id': self.product_table.id,
            'product_uom_id': self.product_table.uom_id.id,
            'product_qty': 1.0,
            'bom_id': self.bom.id,
        })
        mo.action_confirm()
        wizard = self.create_wizard(mo, xls_name)
        with self.assertRaises(ValidationError) as result:
            wizard.produce_move_lines()
        self.assertIn(
            'Please, delete lines from the file or modify the '
            'quantity to be produced from the production order.',
            result.exception.args[0])

    def test_default_code_not_exist(self):
        xls_name = 'sample_import_lots.xls'
        mo = self.env['mrp.production'].create({
            'name': 'MO 1',
            'product_id': self.product_table.id,
            'product_uom_id': self.product_table.uom_id.id,
            'product_qty': 2.0,
            'bom_id': self.bom.id,
        })
        mo.action_confirm()
        self.product_board.default_code = 'ANOTHERCODE'
        wizard = self.create_wizard(mo, xls_name)
        with self.assertRaises(ValidationError) as result:
            wizard.produce_move_lines()
        self.assertIn(
            'No product was found for default_code "TABLEBOARD"',
            result.exception.args[0])

    def test_default_code_not_duplicate(self):
        xls_name = 'sample_import_lots.xls'
        mo = self.env['mrp.production'].create({
            'name': 'MO 1',
            'product_id': self.product_table.id,
            'product_uom_id': self.product_table.uom_id.id,
            'product_qty': 2.0,
            'bom_id': self.bom.id,
        })
        mo.action_confirm()
        self.product_table_leg.default_code = 'TABLEBOARD'
        wizard = self.create_wizard(mo, xls_name)
        with self.assertRaises(ValidationError) as result:
            wizard.produce_move_lines()
        self.assertIn(
            'More than one product found for default_code "TABLEBOARD"',
            result.exception.args[0])

    def test_lot_not_exists(self):
        xls_name = 'sample_import_lots.xls'
        mo = self.env['mrp.production'].create({
            'name': 'MO 1',
            'product_id': self.product_table.id,
            'product_uom_id': self.product_table.uom_id.id,
            'product_qty': 2.0,
            'bom_id': self.bom.id,
        })
        mo.action_confirm()
        self.lot_1.name = 'ANOTHER_LOT'
        wizard = self.create_wizard(mo, xls_name)
        with self.assertRaises(ValidationError) as result:
            wizard.produce_move_lines()
        self.assertIn(
            'No lot/serial was found for lot_material "TABLEBOARD001"',
            result.exception.args[0])

    def test_import_without_stock(self):
        xls_name = 'sample_import_lots.xls'
        self.quant_obj._update_available_quantity(
            self.product_table_leg, self.stock_location, -16)
        leg_quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_table_leg.id),
            ('location_id', '=', self.stock_location.id),
        ])
        self.assertEqual(leg_quant.quantity, 0)
        mo = self.env['mrp.production'].create({
            'name': 'MO 1',
            'product_id': self.product_table.id,
            'product_uom_id': self.product_table.uom_id.id,
            'product_qty': 2.0,
            'bom_id': self.bom.id,
        })
        self.assertEqual(len(mo), 1)
        mo.action_confirm()
        mo.action_assign()
        lots = mo.move_raw_ids.mapped('move_line_ids.lot_id')
        self.assertEqual(lots[0], self.lot_1)
        self.assertEqual(lots[1], self.lot_2)
        wizard = self.create_wizard(mo, xls_name)
        wizard.produce_move_lines()
        mo.button_mark_done()
        lots = self.env['stock.lot'].search([
            ('product_id', '=', self.product_table.id),
        ])
        self.assertEqual(len(lots), 2)
        self.assertEqual(lots[0].name, 'TABLE001')
        self.assertEqual(lots[1].name, 'TABLE002')
        self.assertEqual(len(mo.finished_move_line_ids), 2)
        self.assertEqual(
            mo.finished_move_line_ids[0].product_id.id, self.product_table.id)
        self.assertEqual(
            mo.finished_move_line_ids[1].product_id.id, self.product_table.id)
        self.assertEqual(mo.finished_move_line_ids[0].qty_done, 1)
        self.assertEqual(mo.finished_move_line_ids[1].qty_done, 1)
        self.assertEqual(mo.finished_move_line_ids[0].lot_id, lots[0])
        self.assertEqual(mo.finished_move_line_ids[1].lot_id, lots[1])
        self.assertEqual(
            mo.move_raw_ids[0].product_id.id, self.product_board.id)
        self.assertEqual(
            mo.move_raw_ids[1].product_id.id, self.product_table_leg.id)
        self.assertEqual(mo.move_raw_ids[0].product_uom_qty, 2)
        self.assertEqual(mo.move_raw_ids[1].product_uom_qty, 8)
        self.assertEqual(mo.move_raw_ids[0].quantity_done, 2)
        self.assertEqual(mo.move_raw_ids[1].quantity_done, 8)
        leg_quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_table_leg.id),
            ('location_id', '=', self.stock_location.id),
        ])
        board_quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_board.id),
            ('location_id', '=', self.stock_location.id),
        ])
        table_quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_table.id),
            ('location_id', '=', self.stock_location.id),
        ])
        self.assertEqual(leg_quant.quantity, -8)
        self.assertEqual(sum(board_quant.mapped('quantity')), 2)
        self.assertEqual(sum(table_quant.mapped('quantity')), 2)

    def test_import_two_tracking_material(self):
        xls_name = 'sample_import_lots.xls'
        self.product_table_leg.tracking = 'serial'
        mo = self.env['mrp.production'].create({
            'name': 'MO 1',
            'product_id': self.product_table.id,
            'product_uom_id': self.product_table.uom_id.id,
            'product_qty': 2.0,
            'bom_id': self.bom.id,
        })
        mo.action_confirm()
        wizard = self.create_wizard(mo, xls_name)
        with self.assertRaises(UserError) as result:
            wizard.produce_move_lines()
        self.assertEqual(
            'Please enter a lot or serial number for %s !'
            % self.product_table_leg.display_name, result.exception.args[0])
