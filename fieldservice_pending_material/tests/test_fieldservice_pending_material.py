###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo.tests import common

_log = logging.getLogger(__name__)


class TestFieldservicePendingMaterial(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.customer = self.env['res.partner'].create({
            'name': 'Customer test',
            'customer': True,
        })
        self.supplier = self.env['res.partner'].create({
            'name': 'Supplier test',
            'supplier': True,
        })
        self.location = self.env['fsm.location'].create({
            'name': 'Location test',
            'owner_id': self.customer.id,
            'partner_id': self.customer.id,
        })
        self.fsm_order = self.env['fsm.order'].create({
            'location_id': self.location.id,
        })
        self.buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        self.mto_route = self.env.ref('stock.route_warehouse0_mto')
        self.product_1 = self.env['product.product'].create({
            'name': 'Product 1',
            'type': 'product',
            'invoice_policy': 'delivery',
            'field_service_tracking': 'sale',
            'list_price': 100,
            'route_ids': [(6, 0, [self.buy_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'price': 100.00,
                'delay': 0,
            })],
        })
        self.product_2 = self.env['product.product'].create({
            'name': 'Product 2',
            'type': 'product',
            'invoice_policy': 'delivery',
            'field_service_tracking': 'sale',
            'list_price': 100,
            'route_ids': [(6, 0, [self.buy_route.id, self.mto_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'price': 100.00,
                'delay': 0,
            })],
        })
        self.warehouse = self.env.ref('stock.warehouse0')

    def update_qty_on_hand(self, product, location, new_qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': new_qty,
            'location_id': location.id,
        })
        wizard.change_product_qty()
        self.assertEquals(product.with_context(
            location=location.id).qty_available, new_qty)

    def test_fieldservice_pending_state_with_stock(self):
        self.update_qty_on_hand(
            self.product_1, self.warehouse.lot_stock_id, 10)
        self.assertEquals(self.product_1.with_context(
            location=self.warehouse.lot_stock_id.id).qty_available, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids[0]
        self.assertEquals(picking_out.state, 'assigned')
        self.assertEquals(picking_out.fsm_order_id.pending_material, False)
        self.assertEquals(picking_out.fsm_order_id, sale.fsm_order_ids)
        self.assertEquals(
            picking_out.move_lines.fsm_order_id, sale.fsm_order_ids)
        self.assertEquals(sale.fsm_order_ids.move_ids, picking_out.move_lines)
        picking_out.action_confirm()
        self.assertEquals(picking_out.state, 'assigned')
        self.assertEquals(picking_out.fsm_order_id.pending_material, False)
        picking_out.action_assign()
        self.assertEquals(picking_out.state, 'assigned')
        self.assertEquals(picking_out.fsm_order_id.pending_material, False)
        for move in picking_out.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_out.action_done()
        self.assertEquals(picking_out.state, 'done')
        self.assertEquals(picking_out.fsm_order_id.pending_material, False)

    def test_fieldservice_pending_state_without_stock(self):
        self.assertEquals(self.product_1.with_context(
            location=self.warehouse.lot_stock_id.id).qty_available, 0)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids[0]
        self.assertEquals(picking_out.state, 'waiting')
        self.assertEquals(picking_out.fsm_order_id.pending_material, True)
        self.assertEquals(picking_out.fsm_order_id, sale.fsm_order_ids)
        self.assertEquals(
            picking_out.move_lines.fsm_order_id, sale.fsm_order_ids)
        self.assertEquals(sale.fsm_order_ids.move_ids, picking_out.move_lines)
        self.assertEquals(self.product_2.with_context(
            location=self.location.id).qty_available, 0)
        purchases = self.env['purchase.order'].search([
            ('origin', '=', sale.name),
        ])
        self.assertEquals(len(purchases), 1)
        purchase = purchases[0]
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.order_line.product_id, self.product_2)
        purchase.button_confirm()
        picking_in = purchase.picking_ids[0]
        self.assertEquals(picking_in.state, 'assigned')
        self.assertEquals(picking_in.fsm_order_id.pending_material, True)
        self.assertEquals(picking_in.fsm_order_id, sale.fsm_order_ids)
        self.assertEquals(
            picking_in.move_lines.fsm_order_id, sale.fsm_order_ids)
        self.assertIn(picking_in.move_lines, sale.fsm_order_ids.move_ids)
        self.assertEquals(
            sale.fsm_order_ids.move_ids,
            picking_out.move_lines + picking_in.move_lines)
        self.assertEquals(picking_in.fsm_order_id.pending_material, True)
        for move in picking_in.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_in.action_done()
        self.assertEquals(picking_in.state, 'done')
        self.assertEquals(picking_out.fsm_order_id.pending_material, False)
        for move in picking_out.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_out.action_done()
        self.assertEquals(picking_out.fsm_order_id.pending_material, False)

    def test_fieldservice_pending_state_with_stock_several_lines(self):
        self.update_qty_on_hand(
            self.product_1, self.warehouse.lot_stock_id, 10)
        self.assertEquals(self.product_1.with_context(
            location=self.warehouse.lot_stock_id.id).qty_available, 10)
        self.update_qty_on_hand(
            self.product_2, self.warehouse.lot_stock_id, 10)
        self.assertEquals(self.product_2.with_context(
            location=self.warehouse.lot_stock_id.id).qty_available, 10)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 2,
                })
            ],
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids[0]
        self.assertEquals(picking_out.state, 'assigned')
        self.assertEquals(picking_out.fsm_order_id.pending_material, False)
        self.assertEquals(picking_out.fsm_order_id, sale.fsm_order_ids)
        self.assertEquals(
            picking_out.move_lines.mapped('fsm_order_id'), sale.fsm_order_ids)
        self.assertEquals(sale.fsm_order_ids.move_ids, picking_out.move_lines)
        picking_out.action_confirm()
        self.assertEquals(picking_out.state, 'assigned')
        self.assertEquals(picking_out.fsm_order_id.pending_material, False)
        picking_out.action_assign()
        self.assertEquals(picking_out.state, 'assigned')
        self.assertEquals(picking_out.fsm_order_id.pending_material, False)
        for move in picking_out.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_out.action_done()
        self.assertEquals(picking_out.state, 'done')
        self.assertEquals(picking_out.fsm_order_id.pending_material, False)

    def test_fieldservice_pending_state_without_stock_several_lines(self):
        self.assertEquals(self.product_1.with_context(
            location=self.warehouse.lot_stock_id.id).qty_available, 0)
        self.assertEquals(self.product_2.with_context(
            location=self.warehouse.lot_stock_id.id).qty_available, 0)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 2,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids[0]
        self.assertEquals(picking_out.state, 'waiting')
        self.assertEquals(picking_out.fsm_order_id.pending_material, True)
        self.assertEquals(picking_out.fsm_order_id, sale.fsm_order_ids)
        self.assertEquals(
            picking_out.move_lines.mapped('fsm_order_id'), sale.fsm_order_ids)
        self.assertEquals(sale.fsm_order_ids.move_ids, picking_out.move_lines)
        self.assertEquals(self.product_2.with_context(
            location=self.location.id).qty_available, 0)
        purchases = self.env['purchase.order'].search([
            ('origin', '=', sale.name),
        ])
        self.assertEquals(len(purchases), 1)
        purchase = purchases[0]
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.order_line.product_id, self.product_2)
        purchase.button_confirm()
        picking_in = purchase.picking_ids[0]
        self.assertEquals(picking_in.state, 'assigned')
        self.assertEquals(picking_in.fsm_order_id.pending_material, True)
        self.assertEquals(picking_in.fsm_order_id, sale.fsm_order_ids)
        self.assertEquals(
            picking_in.move_lines.fsm_order_id, sale.fsm_order_ids)
        self.assertIn(picking_in.move_lines, sale.fsm_order_ids.move_ids)
        self.assertEquals(
            sale.fsm_order_ids.move_ids,
            picking_out.move_lines + picking_in.move_lines)
        self.assertEquals(picking_in.fsm_order_id.pending_material, True)
        for move in picking_in.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_in.action_done()
        self.assertEquals(picking_in.state, 'done')
        self.assertEquals(picking_out.fsm_order_id.pending_material, False)
        for move in picking_out.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_out.action_done()
        self.assertEquals(picking_out.fsm_order_id.pending_material, False)
