###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestFieldserviceSalePurchaseStock(common.TransactionCase):

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
        self.warehouse = self.env.ref('stock.warehouse0')
        self.buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        self.mto_route = self.env.ref('stock.route_warehouse0_mto')

    def create_orderpoint(self, warehouse, product, min_qty=0, max_qty=0):
        return self.env['stock.warehouse.orderpoint'].create({
            'name': 'OP/%s' % product.name,
            'product_id': product.id,
            'warehouse_id': warehouse.id,
            'location_id': warehouse.out_type_id.default_location_src_id.id,
            'product_min_qty': min_qty,
            'product_max_qty': max_qty,
        })

    def test_fieldservice_move_ids_buy_and_mto_route(self):
        product_mto_buy = self.env['product.product'].create({
            'name': 'Product MTO buy',
            'type': 'product',
            'invoice_policy': 'delivery',
            'field_service_tracking': 'sale',
            'list_price': 100,
            'route_ids': [(6, 0, [self.buy_route.id, self.mto_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'price': 100.00,
            })],
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_mto_buy.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids[0]
        self.assertEquals(picking_out.fsm_order_id, sale.fsm_order_ids)
        self.assertEquals(sale.fsm_order_ids.move_ids, picking_out.move_lines)
        self.assertEquals(product_mto_buy.with_context(
            location=self.location.id).qty_available, 0)
        purchases = self.env['purchase.order'].search([
            ('origin', '=', sale.name),
        ])
        self.assertEquals(len(purchases), 1)
        purchase = purchases[0]
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.order_line.product_id, product_mto_buy)
        purchase.button_confirm()
        picking_in = purchase.picking_ids[0]
        self.assertEquals(picking_in.fsm_order_id, sale.fsm_order_ids)
        self.assertEquals(
            picking_in.move_lines.fsm_order_id, sale.fsm_order_ids)
        self.assertIn(picking_in.move_lines, sale.fsm_order_ids.move_ids)
        self.assertEquals(
            sale.fsm_order_ids.move_ids,
            picking_out.move_lines + picking_in.move_lines)

    def test_fieldservice_move_ids_buy_route_not_link(self):
        product_buy = self.env['product.product'].create({
            'name': 'Product buy',
            'type': 'product',
            'invoice_policy': 'delivery',
            'field_service_tracking': 'sale',
            'list_price': 100,
            'route_ids': [(6, 0, [self.buy_route.id])],
            'seller_ids': [(0, 0, {
                'name': self.supplier.id,
                'price': 100.00,
            })],
        })
        self.create_orderpoint(self.warehouse, product_buy)
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_buy.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids[0]
        self.assertEquals(picking_out.fsm_order_id, sale.fsm_order_ids)
        self.assertEquals(sale.fsm_order_ids.move_ids, picking_out.move_lines)
        self.assertEquals(product_buy.with_context(
            location=self.location.id).qty_available, 0)
        self.env['procurement.group'].run_scheduler()
        purchases = self.env['purchase.order'].search([
            ('partner_id', '=', self.supplier.id),
        ])
        self.assertEquals(len(purchases), 1)
        purchase = purchases[0]
        self.assertEquals(len(purchase.order_line), 1)
        self.assertEquals(purchase.order_line.product_id, product_buy)
        self.assertEquals(purchase.order_line.product_uom_qty, 1)
        purchase.button_confirm()
        picking_in = purchase.picking_ids[0]
        self.assertFalse(picking_in.fsm_order_id)
        picking_in.action_confirm()
        picking_in.action_assign()
        for move in picking_in.move_lines:
            move.quantity_done = move.product_uom_qty
        picking_in.action_done()
        self.assertFalse(picking_in.fsm_order_id)
        self.assertFalse(picking_in.move_lines.fsm_order_id)
        self.assertNotIn(picking_in.move_lines, sale.fsm_order_ids.move_ids)
