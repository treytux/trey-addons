###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests import common


class TestStockPickingSplitDeliveryByLocationDelivery(common.TransactionCase):

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
        self.delivery_carrier_01 = self.env['delivery.carrier'].create({
            'name': 'Carrier 01',
            'product_id': self.env.ref('delivery.product_product_delivery').id,
        })
        self.delivery_carrier_02 = self.env['delivery.carrier'].create({
            'name': 'Carrier 02',
            'product_id': self.env.ref('delivery.product_product_delivery').id,
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

    def test_picking_split_lines_with_different_carriers(self):
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
            active_model='stock.picking',
            active_id=picking.id,
            active_ids=picking.ids,
        ).action_open_delivery_distribution()
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
                'delivery_carrier_id': self.delivery_carrier_01.id,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_02.id,
                'location_id': location_01.id,
                'quantity': 2,
                'delivery_carrier_id': self.delivery_carrier_01.id,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_03.id,
                'location_id': location_01.id,
                'quantity': 1,
                'delivery_carrier_id': self.delivery_carrier_01.id,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_01.id,
                'location_id': location_02.id,
                'quantity': 3,
                'delivery_carrier_id': self.delivery_carrier_02.id,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_02.id,
                'location_id': location_02.id,
                'quantity': 2,
                'delivery_carrier_id': self.delivery_carrier_02.id,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_03.id,
                'location_id': location_02.id,
                'quantity': 1,
                'delivery_carrier_id': self.delivery_carrier_02.id,
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
            [('sale_id', '=', self.sale.id)])
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
        self.assertEqual(picking_loc_01.carrier_id, self.delivery_carrier_01)
        self.assertEqual(picking_loc_02.state, 'assigned')
        self.assertEqual(picking_loc_02.carrier_id, self.delivery_carrier_02)
        self.assertEqual(picking_loc_main.state, 'assigned')
        self.assertFalse(picking_loc_main.carrier_id)

    def test_picking_split_lines_error_multiple_carriers(self):
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
        self.assertEqual(picking.state, 'assigned')
        action = picking.with_context(
            active_model='stock.picking',
            active_id=picking.id,
            active_ids=picking.ids,
        ).action_open_delivery_distribution()
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
                'delivery_carrier_id': self.delivery_carrier_01.id,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_02.id,
                'location_id': location_01.id,
                'quantity': 2,
                'delivery_carrier_id': self.delivery_carrier_01.id,
            },
            {
                'wizard_id': wizard.id,
                'product_id': self.product_03.id,
                'location_id': location_01.id,
                'quantity': 1,
                'delivery_carrier_id': self.delivery_carrier_02.id,
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
        with self.assertRaises(UserError) as result:
            wizard.action_confirm_distribution()
        self.assertIn(
            'You cannot distribute products with different delivery carriers '
            'in the same location. Please select a single delivery carrier for '
            'each location.',
            result.exception.args[0]
        )
