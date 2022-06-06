###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSaleOrderRecreatePickingDropshipping(TransactionCase):
    def setUp(self):
        super().setUp()
        self.customer = self.env['res.partner'].create({
            'name': 'Customer test',
        })
        self.supplier = self.env['res.partner'].create({
            'name': 'Supplier test',
        })
        self.customer_loc = self.env.ref('stock.stock_location_customers')
        self.supplier_loc = self.env.ref('stock.stock_location_suppliers')
        self.buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        self.mto_route = self.env.ref('stock.route_warehouse0_mto')
        self.product_buy = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Physical product',
            'standard_price': 10,
            'list_price': 100,
            'invoice_policy': 'delivery',
            'route_ids': [(6, 0, [self.buy_route.id, self.mto_route.id])],
            'seller_ids': [
                (0, 0, {
                    'name': self.supplier.id,
                    'price': 9,
                })],
        })
        self.stock_wh = self.env.ref('stock.warehouse0')
        self.env['stock.warehouse.orderpoint'].create({
            'name': 'Orderpoint test',
            'product_id': self.product_buy.id,
            'warehouse_id': self.stock_wh.id,
            'location_id': (
                self.stock_wh.out_type_id.default_location_src_id.id),
            'product_min_qty': 5,
            'product_max_qty': 20,
        })
        if self.ref('stock_dropshipping.route_drop_shipping'):
            self.picking_type_dropshipping = self.env.ref(
                'stock_dropshipping.picking_type_dropship')
            self.dropshipping_route = self.env.ref(
                'stock_dropshipping.route_drop_shipping')
            self.product_dropshipping = self.env['product.product'].create({
                'type': 'product',
                'company_id': False,
                'name': 'Physical product',
                'standard_price': 10,
                'list_price': 100,
                'invoice_policy': 'delivery',
                'route_ids': [(6, 0, [self.dropshipping_route.id])],
                'seller_ids': [
                    (0, 0, {
                        'name': self.supplier.id,
                        'price': 9,
                    })],
            })

    def picking_transfer(self, picking, qty):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = qty
        picking.action_done()
        self.assertEquals(picking.state, 'done')

    def test_recreate_purchase_by_return(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'order_line': [(0, 0, {
                'product_id': self.product_buy.id,
                'name': self.product_buy.name,
                'price_unit': 10.,
                'product_uom_qty': 10,
            })],
        })
        sale.action_confirm()
        self.assertTrue(sale.picking_ids)
        purchase_ids = sale.get_purchase_order_ids(sale)
        purchases = self.env['purchase.order'].browse(purchase_ids)
        self.assertEquals(len(purchases), 1)
        purchases.button_confirm()
        self.assertEquals(len(purchases.picking_ids), 1)
        picking = sale.picking_ids
        self.picking_transfer(picking, 10)
        self.assertEquals(picking.state, 'done')
        self.assertEquals(sale.order_line.qty_delivered, 10)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEquals(len(sale.picking_ids), 2)
        picking_ret = sale.picking_ids.filtered(
            lambda pick: pick.move_lines.product_uom_qty == 1)
        self.picking_transfer(picking_ret, 1)
        self.assertEquals(picking_ret.state, 'done')
        sale.action_recreate_picking()
        self.assertEquals(len(sale.picking_ids), 3)
        purchase_ids = sale.get_purchase_order_ids(sale)
        purchases = self.env['purchase.order'].browse(purchase_ids)
        self.assertEquals(len(purchases), 2)
        new_purchase = purchases.filtered(
            lambda po: po.order_line.product_uom_qty == 1)
        self.assertEquals(new_purchase.order_line.product_id, self.product_buy)
        self.assertEquals(new_purchase.order_line.product_uom_qty, 1)
        self.assertEquals(new_purchase.order_line.price_unit, 9)
        new_purchase.button_cancel()
        self.assertEquals(new_purchase.state, 'cancel')
        with self.assertRaises(UserError):
            sale.action_recreate_picking()
        pickings = sale.picking_ids.filtered(lambda pick: pick.state != 'done')
        pickings.action_cancel()
        sale.action_recreate_picking()
        purchase_ids = sale.get_purchase_order_ids(sale)
        purchases = self.env['purchase.order'].browse(purchase_ids)
        self.assertEquals(len(purchases), 3)

    def test_recreate_purchase_dropshipping_by_return(self):
        if not self.ref('stock_dropshipping.route_drop_shipping'):
            self.skipTest('No stock_dropshipping addon installed!')
            return
        sale = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'order_line': [(0, 0, {
                'product_id': self.product_dropshipping.id,
                'name': self.product_dropshipping.name,
                'price_unit': 10.,
                'product_uom_qty': 10,
            })],
        })
        sale.action_confirm()
        self.assertFalse(sale.picking_ids)
        purchase_ids = sale.get_purchase_order_ids(sale)
        purchases = self.env['purchase.order'].browse(purchase_ids)
        self.assertEquals(len(purchases), 1)
        purchases.button_confirm()
        self.assertEquals(len(purchases.picking_ids), 1)
        picking = sale.picking_ids
        self.assertTrue(picking)
        self.picking_transfer(picking, 10)
        self.assertEquals(picking.state, 'done')
        self.assertEquals(sale.order_line.qty_delivered, 10)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEquals(len(sale.picking_ids), 2)
        picking_ret = sale.picking_ids.filtered(
            lambda pick: pick.move_lines.product_uom_qty == 1)
        self.picking_transfer(picking_ret, 1)
        self.assertEquals(sale.order_line.qty_delivered, 9)
        self.assertEquals(picking_ret.state, 'done')
        sale.action_recreate_picking()
        purchase_ids = sale.get_purchase_order_ids(sale)
        purchases = self.env['purchase.order'].browse(purchase_ids)
        self.assertEquals(len(purchases), 2)
        new_purchase = purchases.filtered(
            lambda po: po.order_line.product_uom_qty == 1)
        self.assertEquals(
            new_purchase.order_line.product_id, self.product_dropshipping)
        self.assertEquals(new_purchase.order_line.product_uom_qty, 1)
        self.assertEquals(new_purchase.order_line.price_unit, 9)
        new_purchase.button_cancel()
        self.assertEquals(new_purchase.state, 'cancel')
        sale.action_recreate_picking()
        pickings = sale.picking_ids.filtered(lambda pick: pick.state != 'done')
        pickings.action_cancel()
        sale.action_recreate_picking()
        purchase_ids = sale.get_purchase_order_ids(sale)
        purchases = self.env['purchase.order'].browse(purchase_ids)
        self.assertEquals(len(purchases), 3)
