###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests import Form, common


class TestStockPickingSplitDeliveryByLocation(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.product_01 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 01',
            'default_code': 'DEF-CODE-01',
            'standard_price': 10,
            'list_price': 100,
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 02',
            'default_code': 'DEF-CODE-02',
            'standard_price': 10,
            'list_price': 100,
        })
        self.product_03 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 03',
            'default_code': 'DEF-CODE-03',
            'standard_price': 10,
            'list_price': 100,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.location_test = self.env['stock.location'].create({
            'name': 'Test internal location',
            'usage': 'internal',
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 9,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': self.product_02.list_price,
                    'product_uom_qty': 6,
                }),
                (0, 0, {
                    'product_id': self.product_03.id,
                    'price_unit': self.product_03.list_price,
                    'product_uom_qty': 3,
                }),
            ],
        })

    def create_warehouse(self, key):
        return self.env['stock.warehouse'].create({
            'name': 'Warehouse %s' % key,
            'code': 'WH%s' % key,
        })

    def create_inventory(self, product, location, qty, lot_id=False):
        inventory = self.env['stock.quant'].create({
            'product_id': product.id,
            'inventory_quantity': qty,
            'location_id': location.id,
            'lot_id': lot_id,
        })
        inventory.action_apply_inventory()

    def validate_picking(self, picking):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()

    def test_picking_split_sale_products_01(self):
        warehouse_01 = self.create_warehouse('1')
        warehouse_02 = self.create_warehouse('2')
        location_01 = warehouse_01.out_type_id.default_location_src_id
        location_02 = warehouse_02.out_type_id.default_location_src_id
        location_main = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location_main, 3)
        self.create_inventory(self.product_01, location_01, 3)
        self.create_inventory(self.product_01, location_02, 3)
        self.create_inventory(self.product_02, location_main, 2)
        self.create_inventory(self.product_02, location_01, 2)
        self.create_inventory(self.product_02, location_02, 2)
        self.create_inventory(self.product_03, location_main, 1)
        self.create_inventory(self.product_03, location_01, 1)
        self.create_inventory(self.product_03, location_02, 1)
        self.assertEqual(self.sale.warehouse_id, location_main.warehouse_id)
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        customer_location = picking.location_dest_id
        self.assertEqual(picking.state, 'assigned')
        action = picking.with_context(
            active_model='stock.picking', active_id=picking.id,
            active_ids=picking.ids).action_open_delivery_distribution()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(wizard.line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.line_ids[0].qty_requested, 9)
        self.assertEqual(wizard.line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.line_ids[1].qty_requested, 6)
        self.assertEqual(wizard.line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.line_ids[2].qty_requested, 3)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard.confirm_line_ids.create([
            {
                'wizard_id': wizard.id,
                'product_id': self.product_01.id,
                'location_id': location_01.id,
                'quantity': 3,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_02.id,
                'location_id': location_01.id,
                'quantity': 2,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_03.id,
                'location_id': location_01.id,
                'quantity': 1,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_01.id,
                'location_id': location_02.id,
                'quantity': 3,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_02.id,
                'location_id': location_02.id,
                'quantity': 2,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_03.id,
                'location_id': location_02.id,
                'quantity': 1,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_01.id,
                'location_id': location_main.id,
                'quantity': 3,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_02.id,
                'location_id': location_main.id,
                'quantity': 2,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_03.id,
                'location_id': location_main.id,
                'quantity': 1,
            },
        ])
        self.assertEqual(len(wizard.confirm_line_ids), 9)
        res = wizard.check_products_qty()
        self.assertTrue(res)
        res = wizard.check_products_availability()
        self.assertTrue(res)
        new_pickings = wizard.action_confirm_distribution()
        self.assertTrue(new_pickings)
        pickings = self.env['stock.picking'].search(
            [('sale_id', '=', self.sale.id)], order='id desc')
        self.assertEqual(len(pickings), 3)
        picking_loc_01 = pickings.filtered(
            lambda p: p.location_id == location_01)
        picking_loc_02 = pickings.filtered(
            lambda p: p.location_id == location_02)
        picking_loc_main = pickings.filtered(
            lambda p: p.location_id == location_main)
        self.assertEqual(picking_loc_01.location_id, location_01)
        self.assertEqual(picking_loc_02.location_id, location_02)
        self.assertEqual(picking_loc_main.location_id, location_main)
        self.assertEqual(picking_loc_02.move_ids[0].product_id, self.product_01)
        self.assertEqual(picking_loc_02.move_ids[0].product_uom_qty, 3)
        self.assertEqual(picking_loc_02.move_ids[1].product_id, self.product_02)
        self.assertEqual(picking_loc_02.move_ids[1].product_uom_qty, 2)
        self.assertEqual(picking_loc_02.move_ids[2].product_id, self.product_03)
        self.assertEqual(picking_loc_02.move_ids[2].product_uom_qty, 1)
        self.assertEqual(picking_loc_01.move_ids[0].product_id, self.product_01)
        self.assertEqual(picking_loc_01.move_ids[0].product_uom_qty, 3)
        self.assertEqual(picking_loc_01.move_ids[1].product_id, self.product_02)
        self.assertEqual(picking_loc_01.move_ids[1].product_uom_qty, 2)
        self.assertEqual(picking_loc_01.move_ids[2].product_id, self.product_03)
        self.assertEqual(picking_loc_01.move_ids[2].product_uom_qty, 1)
        self.assertEqual(
            picking_loc_main.move_ids[0].product_id, self.product_01)
        self.assertEqual(picking_loc_main.move_ids[0].product_uom_qty, 3)
        self.assertEqual(
            picking_loc_main.move_ids[1].product_id, self.product_02)
        self.assertEqual(picking_loc_main.move_ids[1].product_uom_qty, 2)
        self.assertEqual(
            picking_loc_main.move_ids[2].product_id, self.product_03)
        self.assertEqual(picking_loc_main.move_ids[2].product_uom_qty, 1)
        self.assertEqual(picking_loc_01.location_dest_id, customer_location)
        self.assertEqual(picking_loc_02.location_dest_id, customer_location)
        self.assertEqual(picking_loc_main.location_dest_id, customer_location)
        self.assertEqual(picking_loc_01.state, 'assigned')
        self.assertEqual(picking_loc_02.state, 'assigned')
        self.assertEqual(picking_loc_main.state, 'assigned')
        self.validate_picking(picking_loc_02)
        self.assertEqual(picking_loc_02.state, 'done')
        self.assertEqual(self.sale.order_line[0].product_id, self.product_01)
        self.assertEqual(self.sale.order_line[0].product_uom_qty, 9)
        self.assertEqual(self.sale.order_line[0].qty_delivered, 3)
        self.assertEqual(self.sale.order_line[1].product_id, self.product_02)
        self.assertEqual(self.sale.order_line[1].product_uom_qty, 6)
        self.assertEqual(self.sale.order_line[1].qty_delivered, 2)
        self.assertEqual(self.sale.order_line[2].product_id, self.product_03)
        self.assertEqual(self.sale.order_line[2].product_uom_qty, 3)
        self.assertEqual(self.sale.order_line[2].qty_delivered, 1)
        self.validate_picking(pickings[1])
        self.assertEqual(pickings[1].state, 'done')
        self.assertEqual(self.sale.order_line[0].qty_delivered, 6)
        self.assertEqual(self.sale.order_line[1].qty_delivered, 4)
        self.assertEqual(self.sale.order_line[2].qty_delivered, 2)
        self.validate_picking(pickings[2])
        self.assertEqual(pickings[2].state, 'done')
        self.assertEqual(self.sale.order_line[0].qty_delivered, 9)
        self.assertEqual(self.sale.order_line[1].qty_delivered, 6)
        self.assertEqual(self.sale.order_line[2].qty_delivered, 3)

    def test_picking_split_sale_products_02(self):
        warehouse_01 = self.create_warehouse('1')
        warehouse_02 = self.create_warehouse('2')
        location_01 = warehouse_01.out_type_id.default_location_src_id
        location_02 = warehouse_02.out_type_id.default_location_src_id
        location_main = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location_main, 9)
        self.create_inventory(self.product_02, location_main, 4)
        self.create_inventory(self.product_02, location_01, 2)
        self.create_inventory(self.product_03, location_02, 3)
        self.assertEqual(self.sale.warehouse_id, location_main.warehouse_id)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        customer_location = picking.location_dest_id
        self.assertEqual(picking.state, 'assigned')
        action = picking.with_context(
            active_model='stock.picking', active_id=picking.id,
            active_ids=picking.ids).action_open_delivery_distribution()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(wizard.line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.line_ids[0].qty_requested, 9)
        self.assertEqual(wizard.line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.line_ids[1].qty_requested, 6)
        self.assertEqual(wizard.line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.line_ids[2].qty_requested, 3)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard.confirm_line_ids.create([
            {
                'wizard_id': wizard.id,
                'product_id': self.product_01.id,
                'location_id': location_main.id,
                'quantity': 9,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_02.id,
                'location_id': location_main.id,
                'quantity': 4,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_02.id,
                'location_id': location_01.id,
                'quantity': 2,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_03.id,
                'location_id': location_02.id,
                'quantity': 3,
            },
        ])
        self.assertEqual(len(wizard.confirm_line_ids), 4)
        res = wizard.check_products_qty()
        self.assertTrue(res)
        res = wizard.check_products_availability()
        self.assertTrue(res)
        new_pickings = wizard.action_confirm_distribution()
        self.assertTrue(new_pickings)
        pickings = self.env['stock.picking'].search(
            [('sale_id', '=', self.sale.id)], order='id desc')
        self.assertEqual(len(pickings), 3)
        self.assertEqual(pickings[0].location_id, location_02)
        self.assertEqual(pickings[0].move_ids[0].product_id, self.product_03)
        self.assertEqual(pickings[0].move_ids[0].product_uom_qty, 3)
        self.assertEqual(pickings[1].location_id, location_01)
        self.assertEqual(pickings[1].move_ids[0].product_id, self.product_02)
        self.assertEqual(pickings[1].move_ids[0].product_uom_qty, 2)
        self.assertEqual(pickings[2].location_id, location_main)
        self.assertEqual(pickings[2].move_ids[0].product_id, self.product_01)
        self.assertEqual(pickings[2].move_ids[0].product_uom_qty, 9)
        self.assertEqual(pickings[2].move_ids[1].product_id, self.product_02)
        self.assertEqual(pickings[2].move_ids[1].product_uom_qty, 4)
        self.assertEqual(pickings[0].location_dest_id, customer_location)
        self.assertEqual(pickings[1].location_dest_id, customer_location)
        self.assertEqual(pickings[2].location_dest_id, customer_location)
        self.assertEqual(pickings[0].state, 'assigned')
        self.assertEqual(pickings[1].state, 'assigned')
        self.assertEqual(pickings[2].state, 'assigned')
        self.validate_picking(pickings[0])
        self.assertEqual(pickings[0].state, 'done')
        self.validate_picking(pickings[1])
        self.assertEqual(pickings[1].state, 'done')
        self.validate_picking(pickings[2])
        self.assertEqual(pickings[2].state, 'done')
        self.assertEqual(self.sale.order_line[0].qty_delivered, 9)
        self.assertEqual(self.sale.order_line[1].qty_delivered, 6)
        self.assertEqual(self.sale.order_line[2].qty_delivered, 3)

    def test_picking_split_sale_products_03(self):
        warehouse_01 = self.create_warehouse('1')
        warehouse_02 = self.create_warehouse('2')
        location_01 = warehouse_01.out_type_id.default_location_src_id
        location_02 = warehouse_02.out_type_id.default_location_src_id
        location_main = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location_main, 5)
        self.create_inventory(self.product_02, location_main, 4)
        self.create_inventory(self.product_02, location_01, 2)
        self.create_inventory(self.product_03, location_02, 3)
        self.assertEqual(self.sale.warehouse_id, location_main.warehouse_id)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertEqual(picking.state, 'assigned')
        action = picking.with_context(
            active_model='stock.picking', active_id=picking.id,
            active_ids=picking.ids).action_open_delivery_distribution()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(wizard.line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.line_ids[0].qty_requested, 9)
        self.assertEqual(wizard.line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.line_ids[1].qty_requested, 6)
        self.assertEqual(wizard.line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.line_ids[2].qty_requested, 3)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard.confirm_line_ids.create([
            {
                'wizard_id': wizard.id,
                'product_id': self.product_01.id,
                'location_id': location_main.id,
                'quantity': 10,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_02.id,
                'location_id': location_main.id,
                'quantity': 4,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_02.id,
                'location_id': location_01.id,
                'quantity': 2,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_03.id,
                'location_id': location_02.id,
                'quantity': 3,
            },
        ])
        self.assertEqual(len(wizard.confirm_line_ids), 4)
        with self.assertRaises(ValidationError) as result:
            wizard.check_products_qty()
        self.assertIn('exceeds the original quantity', result.exception.args[0])
        wizard.confirm_line_ids[0].quantity = 9
        self.assertEqual(wizard.confirm_line_ids[0].quantity, 9)
        res = wizard.check_products_qty()
        self.assertTrue(res)
        with self.assertRaises(ValidationError) as result:
            wizard.check_products_availability()
        self.assertIn(
            'exceeds the available quantity', result.exception.args[0])
        wizard.confirm_line_ids[0].quantity = 5
        self.assertEqual(wizard.confirm_line_ids[0].quantity, 5)
        with self.assertRaises(ValidationError) as result:
            wizard.action_confirm_distribution()
        self.assertIn('must match', result.exception.args[0])

    def test_picking_split_missing_product(self):
        warehouse_01 = self.create_warehouse('1')
        warehouse_02 = self.create_warehouse('2')
        location_01 = warehouse_01.out_type_id.default_location_src_id
        location_02 = warehouse_02.out_type_id.default_location_src_id
        location_main = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location_main, 9)
        self.create_inventory(self.product_02, location_main, 4)
        self.create_inventory(self.product_02, location_01, 2)
        self.create_inventory(self.product_03, location_02, 3)
        self.assertEqual(self.sale.warehouse_id, location_main.warehouse_id)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertEqual(picking.state, 'assigned')
        action = picking.with_context(
            active_model='stock.picking', active_id=picking.id,
            active_ids=picking.ids).action_open_delivery_distribution()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(wizard.line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.line_ids[0].qty_requested, 9)
        self.assertEqual(wizard.line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.line_ids[1].qty_requested, 6)
        self.assertEqual(wizard.line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.line_ids[2].qty_requested, 3)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard.confirm_line_ids.create([
            {
                'wizard_id': wizard.id,
                'product_id': self.product_01.id,
                'location_id': location_main.id,
                'quantity': 9,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_02.id,
                'location_id': location_main.id,
                'quantity': 4,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_02.id,
                'location_id': location_01.id,
                'quantity': 2,
            },
        ])
        self.assertEqual(len(wizard.confirm_line_ids), 3)
        with self.assertRaises(ValidationError) as result:
            wizard.check_products_qty()
        self.assertIn(
            'All picking products must be distributed',
            result.exception.args[0])
        with self.assertRaises(ValidationError) as result:
            wizard.action_confirm_distribution()
        self.assertIn(
            'All picking products must be distributed',
            result.exception.args[0])

    def test_picking_split_wizard_lines_qty_zero(self):
        warehouse_01 = self.create_warehouse('1')
        warehouse_02 = self.create_warehouse('2')
        location_01 = warehouse_01.out_type_id.default_location_src_id
        location_02 = warehouse_02.out_type_id.default_location_src_id
        location_main = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location_main, 9)
        self.create_inventory(self.product_02, location_main, 4)
        self.create_inventory(self.product_02, location_01, 2)
        self.create_inventory(self.product_03, location_02, 3)
        self.assertEqual(self.sale.warehouse_id, location_main.warehouse_id)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertEqual(picking.state, 'assigned')
        action = picking.with_context(
            active_model='stock.picking', active_id=picking.id,
            active_ids=picking.ids).action_open_delivery_distribution()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(wizard.line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.line_ids[0].qty_requested, 9)
        self.assertEqual(wizard.line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.line_ids[1].qty_requested, 6)
        self.assertEqual(wizard.line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.line_ids[2].qty_requested, 3)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard.confirm_line_ids.create([
            {
                'wizard_id': wizard.id,
                'product_id': self.product_01.id,
                'location_id': location_main.id,
                'quantity': 9,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_02.id,
                'location_id': location_main.id,
                'quantity': 4,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_02.id,
                'location_id': location_01.id,
                'quantity': 2,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_03.id,
                'location_id': location_02.id,
                'quantity': 3,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_03.id,
                'location_id': location_01.id,
                'quantity': 0,
            },
        ])
        self.assertEqual(len(wizard.confirm_line_ids), 5)
        self.assertEqual(wizard.confirm_line_ids[4].quantity, 0)
        with self.assertRaises(ValidationError) as result:
            wizard.check_products_qty()
        self.assertIn(
            'You cannot request zero quantity', result.exception.args[0])
        with self.assertRaises(ValidationError) as result:
            wizard.action_confirm_distribution()
        self.assertIn(
            'You cannot request zero quantity', result.exception.args[0])

    def test_picking_split_remove_empty_picking(self):
        warehouse_01 = self.create_warehouse('1')
        warehouse_02 = self.create_warehouse('2')
        location_01 = warehouse_01.out_type_id.default_location_src_id
        location_02 = warehouse_02.out_type_id.default_location_src_id
        location_main = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location_01, 9)
        self.create_inventory(self.product_02, location_01, 4)
        self.create_inventory(self.product_02, location_02, 2)
        self.create_inventory(self.product_03, location_02, 3)
        self.assertEqual(self.sale.warehouse_id, location_main.warehouse_id)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertEqual(picking.location_id, location_main)
        self.assertEqual(picking.state, 'confirmed')
        action = picking.with_context(
            active_model='stock.picking', active_id=picking.id,
            active_ids=picking.ids).action_open_delivery_distribution()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(wizard.line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.line_ids[0].qty_requested, 9)
        self.assertEqual(wizard.line_ids[1].product_id, self.product_02)
        self.assertEqual(wizard.line_ids[1].qty_requested, 6)
        self.assertEqual(wizard.line_ids[2].product_id, self.product_03)
        self.assertEqual(wizard.line_ids[2].qty_requested, 3)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard.confirm_line_ids.create([
            {
                'wizard_id': wizard.id,
                'product_id': self.product_01.id,
                'location_id': location_01.id,
                'quantity': 9,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_02.id,
                'location_id': location_01.id,
                'quantity': 4,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_02.id,
                'location_id': location_02.id,
                'quantity': 2,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_03.id,
                'location_id': location_02.id,
                'quantity': 3,
            },
        ])
        self.assertEqual(len(wizard.confirm_line_ids), 4)
        locations_distributed = wizard.confirm_line_ids.mapped('location_id')
        self.assertEqual(len(locations_distributed), 2)
        res = wizard.check_products_qty()
        self.assertTrue(res)
        res = wizard.check_products_availability()
        self.assertTrue(res)
        new_pickings = wizard.action_confirm_distribution()
        pickings_location = self.sale.picking_ids.mapped('location_id')
        self.assertEqual(len(pickings_location), 2)
        self.assertEqual(pickings_location, locations_distributed)
        self.assertTrue(new_pickings)
        pickings = self.env['stock.picking'].search(
            [('sale_id', '=', self.sale.id)], order='id desc')
        self.assertEqual(len(pickings), 2)

    def test_split_delivery_partial_no_remove_picking_done(self):
        warehouse_01 = self.create_warehouse('1')
        warehouse_02 = self.create_warehouse('2')
        location_01 = warehouse_01.out_type_id.default_location_src_id
        location_02 = warehouse_02.out_type_id.default_location_src_id
        location_main = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location_main, 7)
        self.create_inventory(self.product_01, location_01, 2)
        self.create_inventory(self.product_02, location_01, 4)
        self.create_inventory(self.product_02, location_02, 2)
        self.create_inventory(self.product_03, location_02, 3)
        self.assertEqual(self.sale.warehouse_id, location_main.warehouse_id)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertEqual(picking.location_id, location_main)
        self.assertEqual(picking.state, 'assigned')
        move_01 = picking.move_ids.filtered(
            lambda m: m.product_id == self.product_01)
        move_01.quantity_done = 7
        action_data = picking.button_validate()
        backorder_wizard = Form(
            self.env['stock.backorder.confirmation'].with_context(
                action_data['context'])).save()
        backorder_wizard.process()
        self.assertEqual(len(self.sale.picking_ids), 2)
        picking_done = self.sale.picking_ids.filtered(
            lambda p: p.state == 'done')
        picking_done_id = picking_done.id
        move_01 = picking_done.move_ids.filtered(
            lambda m: m.product_id == self.product_01)
        self.assertEqual(move_01.quantity_done, 7)
        picking_res = self.sale.picking_ids.filtered(
            lambda p: p.state == 'confirmed')
        picking_res_id = picking_res.id
        move_01 = picking_res.move_ids.filtered(
            lambda m: m.product_id == self.product_01)
        move_02 = picking_res.move_ids.filtered(
            lambda m: m.product_id == self.product_02)
        move_03 = picking_res.move_ids.filtered(
            lambda m: m.product_id == self.product_03)
        self.assertEqual(move_01.product_uom_qty, 2)
        self.assertEqual(move_02.product_uom_qty, 6)
        self.assertEqual(move_03.product_uom_qty, 3)
        self.assertEqual(picking_done.location_id, picking_res.location_id)
        action = picking_res.with_context(
            active_model='stock.picking', active_id=picking_res.id,
            active_ids=picking_res.ids).action_open_delivery_distribution()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking_res)
        self.assertEqual(len(wizard.line_ids), 3)
        self.assertEqual(wizard.line_ids[0].product_id, self.product_02)
        self.assertEqual(wizard.line_ids[0].qty_requested, 6)
        self.assertEqual(wizard.line_ids[1].product_id, self.product_03)
        self.assertEqual(wizard.line_ids[1].qty_requested, 3)
        self.assertEqual(wizard.line_ids[2].product_id, self.product_01)
        self.assertEqual(wizard.line_ids[2].qty_requested, 2)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard.confirm_line_ids.create([
            {
                'wizard_id': wizard.id,
                'product_id': self.product_01.id,
                'location_id': location_01.id,
                'quantity': 2,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_02.id,
                'location_id': location_01.id,
                'quantity': 4,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_02.id,
                'location_id': location_02.id,
                'quantity': 2,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_03.id,
                'location_id': location_02.id,
                'quantity': 3,
            },
        ])
        self.assertEqual(len(wizard.confirm_line_ids), 4)
        locations_distributed = wizard.confirm_line_ids.mapped('location_id')
        self.assertEqual(len(locations_distributed), 2)
        res = wizard.check_products_qty()
        self.assertTrue(res)
        res = wizard.check_products_availability()
        self.assertTrue(res)
        new_pickings = wizard.action_confirm_distribution()
        self.assertEqual(len(self.sale.picking_ids), 3)
        pickings_location = self.sale.picking_ids.mapped('location_id')
        self.assertEqual(len(pickings_location), 3)
        self.assertTrue(new_pickings)
        pickings = self.env['stock.picking'].search(
            [('sale_id', '=', self.sale.id)], order='id desc')
        self.assertEqual(len(pickings), 3)
        self.assertIn(picking_done_id, pickings.ids)
        self.assertNotIn(picking_res_id, pickings.ids)
        pickings_done = self.sale.picking_ids.filtered(
            lambda p: p.state == 'done')
        pickings_assigned = self.sale.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(pickings_done), 1)
        self.assertEqual(len(pickings_assigned), 2)

    def test_picking_split_all_to_another_location_remove_empty_picking(self):
        warehouse_01 = self.create_warehouse('1')
        location_01 = warehouse_01.out_type_id.default_location_src_id
        location_main = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product_01, location_01, 9)
        self.assertEqual(self.sale.warehouse_id, location_main.warehouse_id)
        self.sale.order_line = self.sale.order_line.filtered(
            lambda line: line.product_id == self.product_01)
        self.assertEqual(len(self.sale.order_line), 1)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertEqual(picking.location_id, location_main)
        self.assertEqual(picking.state, 'confirmed')
        action = picking.with_context(
            active_model='stock.picking', active_id=picking.id,
            active_ids=picking.ids).action_open_delivery_distribution()
        wizard = self.env[action['res_model']].browse(action['res_id'])
        self.assertEqual(wizard.picking_id, picking)
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(wizard.line_ids[0].product_id, self.product_01)
        self.assertEqual(wizard.line_ids[0].qty_requested, 9)
        self.assertEqual(len(wizard.confirm_line_ids), 0)
        wizard.confirm_line_ids.create([{
            'wizard_id': wizard.id,
            'product_id': self.product_01.id,
            'location_id': location_01.id,
            'quantity': 9,
        }])
        self.assertEqual(len(wizard.confirm_line_ids), 1)
        locations_distributed = wizard.confirm_line_ids.mapped('location_id')
        self.assertEqual(len(locations_distributed), 1)
        res = wizard.check_products_qty()
        self.assertTrue(res)
        res = wizard.check_products_availability()
        self.assertTrue(res)
        self.assertEqual(picking.state, 'confirmed')
        self.assertIn(picking, self.sale.picking_ids)
        new_pickings = wizard.action_confirm_distribution()
        self.assertFalse(picking.exists())
        self.assertNotIn(picking, self.sale.picking_ids)
        pickings_location = self.sale.picking_ids.mapped('location_id')
        self.assertEqual(len(pickings_location), 1)
        self.assertEqual(pickings_location, locations_distributed)
        self.assertTrue(new_pickings)
        pickings = self.env['stock.picking'].search([
            ('sale_id', '=', self.sale.id),
        ])
        self.assertEqual(len(pickings), 1)
