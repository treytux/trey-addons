###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests import common


class TestFieldserviceStockExtend(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.customer_location = self.env.ref('stock.stock_location_customers')
        self.stock_wh = self.env.ref('stock.warehouse0')
        self.picking_internal_type = self.env.ref(
            'stock.picking_type_internal')
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        self.location = self.env['fsm.location'].create({
            'name': 'Location test',
            'owner_id': self.partner.id,
        })
        self.fsm_template = self.env['fsm.template'].create({
            'name': 'Template fsm',
        })
        self.assertTrue(self.location.inventory_location_id)
        self.product_1 = self.env['product.product'].create({
            'name': 'Component 1',
            'type': 'product',
            'field_service_tracking': 'sale',
            'fsm_order_template_id': self.fsm_template.id,
            'list_price': 100,
        })
        self.product_2 = self.env['product.product'].create({
            'name': 'Component 2',
            'type': 'product',
            'field_service_tracking': 'sale',
            'fsm_order_template_id': self.fsm_template.id,
            'list_price': 500,
        })
        self.warehouse_2 = self.env['stock.warehouse'].create({
            'code': 'WH2',
            'name': 'Warehouse 2',
        })

    def update_qty_on_hand(self, product, location, new_qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': new_qty,
            'location_id': location.id,
        })
        wizard.change_product_qty()
        self.assertEquals(product.with_context(
            location=location.id).qty_available, new_qty)

    def picking_transfer(self, picking, qty=0):
        for move in picking.move_lines:
            if qty == 0:
                qty = move.product_uom_qty
            move.quantity_done = qty
        picking.action_done()

    def create_dummy_internal_picking(self, picking):
        return picking.copy({
            'picking_type_id': self.picking_internal_type.id,
            'location_id': self.stock_wh.lot_stock_id.id,
            'location_dest_id': self.stock_wh.lot_stock_id.id,
        })

    def test_fieldservice_sale_picking_out_moves_and_one_move_internal(self):
        self.update_qty_on_hand(self.product_1, self.stock_wh.lot_stock_id, 10)
        self.update_qty_on_hand(self.product_2, self.stock_wh.lot_stock_id, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'picking_policy': 'direct',
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing')
        self.assertEquals(len(picking_out), 1)
        self.assertEquals(len(picking_out.move_lines), 2)
        self.assertEquals(picking_out.state, 'confirmed')
        moves_out = picking_out.move_lines
        move_product_1 = moves_out.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = moves_out.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 1)
        self.assertEquals(sale.fsm_order_ids.move_ids, moves_out)
        self.assertFalse(sale.fsm_order_ids.move_internal_ids)
        self.assertEquals(sale.fsm_order_ids.delivery_count, 1)
        self.assertEquals(sale.fsm_order_ids.internal_count, 0)
        self.assertEquals(sale.fsm_order_ids.warehouse_id, sale.warehouse_id)
        self.assertEquals(
            picking_out.location_id, sale.warehouse_id.lot_stock_id)
        self.assertEquals(picking_out.location_dest_id, self.customer_location)
        for move in picking_out.move_lines:
            self.assertEquals(move.location_id, sale.warehouse_id.lot_stock_id)
            self.assertEquals(move.location_dest_id, self.customer_location)
        picking_out.action_assign()
        with self.assertRaises(UserError) as result:
            sale.fsm_order_ids.write({
                'warehouse_id': self.warehouse_2.id,
            })
        self.assertEqual(
            result.exception.name,
            'Picking %s is in \'Ready\' state but, if you want change the '
            'warehouse, it must be in \'Draft\' or \'Waiting\' state.' %
            picking_out.name)
        picking_out.do_unreserve()
        self.assertEquals(picking_out.state, 'confirmed')
        sale.fsm_order_ids.write({
            'warehouse_id': self.warehouse_2.id,
        })
        self.assertEquals(
            picking_out.location_id, self.warehouse_2.lot_stock_id)
        self.assertEquals(picking_out.location_dest_id, self.customer_location)
        for move in picking_out.move_lines:
            self.assertEquals(move.location_id, self.warehouse_2.lot_stock_id)
            self.assertEquals(move.location_dest_id, self.customer_location)
        self.assertEquals(len(sale.fsm_order_ids.move_internal_ids), 2)
        picking_internal = sale.fsm_order_ids.move_internal_ids.mapped(
            'picking_id')
        self.assertEquals(len(picking_internal), 1)
        self.assertEquals(
            picking_internal.location_id, self.stock_wh.lot_stock_id)
        self.assertEquals(
            picking_internal.location_dest_id, self.warehouse_2.lot_stock_id)
        for move in picking_internal.move_lines:
            self.assertEquals(move.location_id, self.stock_wh.lot_stock_id)
            self.assertEquals(
                move.location_dest_id, self.warehouse_2.lot_stock_id)
        picking_internal.action_confirm()
        self.assertEquals(picking_internal.origin, sale.name)
        self.assertEquals(picking_internal.state, 'confirmed')
        picking_internal.action_assign()
        self.assertEquals(picking_internal.state, 'assigned')
        self.picking_transfer(picking_internal)
        self.assertEquals(picking_internal.state, 'done')
        picking_out.action_confirm()
        self.assertEquals(picking_out.state, 'confirmed')
        picking_out.action_assign()
        self.assertEquals(picking_out.state, 'assigned')
        with self.assertRaises(UserError) as result:
            sale.fsm_order_ids.write({
                'warehouse_id': self.stock_wh.id,
            })
        self.assertEqual(
            result.exception.name,
            'Picking %s is in \'Ready\' state but, if you want change the '
            'warehouse, it must be in \'Draft\' or \'Waiting\' state.' %
            picking_out.name)
        self.picking_transfer(picking_out)
        with self.assertRaises(UserError) as result:
            sale.fsm_order_ids.write({
                'warehouse_id': self.stock_wh.id,
            })
        self.assertEqual(
            result.exception.name,
            'Picking %s is in \'Done\' state but, if you want change the '
            'warehouse, it must be in \'Draft\' or \'Waiting\' state.' %
            picking_out.name)

    def test_fieldservice_sale_picking_move_internal_ids(self):
        self.update_qty_on_hand(self.product_1, self.stock_wh.lot_stock_id, 10)
        self.update_qty_on_hand(self.product_2, self.stock_wh.lot_stock_id, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'picking_policy': 'direct',
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing')
        self.assertEquals(len(picking_out), 1)
        self.assertEquals(len(picking_out.move_lines), 2)
        self.assertEquals(picking_out.state, 'confirmed')
        moves_out = picking_out.move_lines
        move_product_1 = moves_out.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = moves_out.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 1)
        self.assertEquals(sale.fsm_order_ids.move_ids, moves_out)
        picking_internal = self.create_dummy_internal_picking(picking_out)
        self.assertEquals(picking_internal.origin, sale.name)
        self.assertEquals(
            sale.fsm_order_ids.move_internal_ids, picking_internal.move_lines)
        self.assertEquals(sale.fsm_order_ids.delivery_count, 1)
        self.assertEquals(sale.fsm_order_ids.internal_count, 1)
        self.assertEquals(sale.fsm_order_ids.warehouse_id, sale.warehouse_id)
        self.assertEquals(
            picking_internal.location_id, sale.warehouse_id.lot_stock_id)
        self.assertEquals(
            picking_internal.location_dest_id, sale.warehouse_id.lot_stock_id)
        for move in picking_internal.move_lines:
            self.assertEquals(move.location_id, sale.warehouse_id.lot_stock_id)
            self.assertEquals(
                move.location_dest_id, sale.warehouse_id.lot_stock_id)
        picking_out.action_assign()
        with self.assertRaises(UserError) as result:
            sale.fsm_order_ids.write({
                'warehouse_id': self.warehouse_2.id,
            })
        self.assertEqual(
            result.exception.name,
            'Picking %s is in \'Ready\' state but, if you want change the '
            'warehouse, it must be in \'Draft\' or \'Waiting\' state.' %
            picking_out.name)
        picking_out.do_unreserve()
        self.assertEquals(picking_out.state, 'confirmed')
        sale.fsm_order_ids.write({
            'warehouse_id': self.warehouse_2.id,
        })
        self.assertEquals(
            picking_internal.location_id, sale.warehouse_id.lot_stock_id)
        self.assertEquals(
            picking_internal.location_dest_id,
            self.warehouse_2.lot_stock_id)
        for move in picking_internal.move_lines:
            self.assertEquals(move.location_id, sale.warehouse_id.lot_stock_id)
            self.assertEquals(
                move.location_dest_id, self.warehouse_2.lot_stock_id)
        self.assertEquals(len(sale.fsm_order_ids.move_internal_ids), 4)
        picking_internal = sale.fsm_order_ids.move_internal_ids.mapped(
            'picking_id')
        self.assertEquals(len(picking_internal), 1)
        self.assertEquals(
            picking_internal.location_id, self.stock_wh.lot_stock_id)
        self.assertEquals(
            picking_internal.location_dest_id, self.warehouse_2.lot_stock_id)
        for move in picking_internal.move_lines:
            self.assertEquals(move.location_id, self.stock_wh.lot_stock_id)
            self.assertEquals(
                move.location_dest_id, self.warehouse_2.lot_stock_id)
        picking_internal.action_confirm()
        self.assertEquals(picking_internal.state, 'confirmed')
        picking_internal.action_assign()
        self.assertEquals(picking_internal.state, 'assigned')
        self.picking_transfer(picking_internal)
        self.assertEquals(picking_internal.state, 'done')
        picking_out.action_confirm()
        self.assertEquals(picking_out.state, 'confirmed')
        picking_out.action_assign()
        self.assertEquals(picking_out.state, 'assigned')
        with self.assertRaises(UserError) as result:
            sale.fsm_order_ids.write({
                'warehouse_id': self.stock_wh.id,
            })
        self.assertEqual(
            result.exception.name,
            'Picking %s is in \'Ready\' state but, if you want change the '
            'warehouse, it must be in \'Draft\' or \'Waiting\' state.' %
            picking_out.name)
        self.picking_transfer(picking_out)
        with self.assertRaises(UserError) as result:
            sale.fsm_order_ids.write({
                'warehouse_id': self.stock_wh.id,
            })
        self.assertEqual(
            result.exception.name,
            'Picking %s is in \'Done\' state but, if you want change the '
            'warehouse, it must be in \'Draft\' or \'Waiting\' state.' %
            picking_out.name)
