###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleOrderRecreatePicking(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_18 = self.env.ref('base.res_partner_18')
        self.product_4 = self.env.ref('product.product_product_4')
        self.product_uom_kgm = self.env.ref('uom.product_uom_kgm')
        self.customer = self.env['res.partner'].create({
            'name': 'Customer test',
        })
        self.product_buy = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Physical product',
            'standard_price': 10,
            'list_price': 100,
            'invoice_policy': 'delivery',
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_18.id,
            'partner_invoice_id': self.partner_18.id,
            'partner_shipping_id': self.partner_18.id,
            'order_line': [(0, 0, {
                'name': 'POP Doctor Simon',
                'product_id': self.product_4.id,
                'product_uom_qty': 1,
                'product_uom': self.product_4.uom_id.id,
                'price_unit': 750.00,
            })],
        })

    def picking_transfer(self, picking, qty):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = qty
        picking.action_done()
        self.assertEquals(picking.state, 'done')

    def test_return_and_recreate_picking(self):
        self.sale_order.action_confirm()
        self.assertTrue(self.sale_order.picking_ids)
        picking = self.sale_order.picking_ids
        picking.move_lines.write({
            'quantity_done': 1,
        })
        self.assertTrue(picking.action_confirm())
        self.assertTrue(picking.action_assign())
        self.assertTrue(picking.action_done())
        qty_delivery_lines = self.sale_order.mapped('order_line').filtered(
            lambda l: l.qty_delivered != l.product_uom_qty)
        self.assertFalse(qty_delivery_lines)
        picking_wizard = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids, active_id=picking.id).create({})
        picking_wizard.product_return_moves.quantity = 1.0
        picking_wizard.product_return_moves.to_refund = True
        picking_return_action = picking_wizard.create_returns()
        picking_return = self.env['stock.picking'].browse(
            picking_return_action['res_id'])
        picking_return.move_lines[0].move_line_ids[0].qty_done = 1.0
        self.assertTrue(picking_return.action_done())
        self.assertEquals(self.sale_order.state, 'sale')
        self.assertIsNone(self.sale_order.action_recreate_picking())
        self.assertEquals(len(self.sale_order.picking_ids), 3)
        last_picking = self.sale_order.picking_ids[2]
        self.assertEquals(last_picking.move_lines[0].product_uom_qty, 1)
        self.assertTrue(last_picking.partner_id)
        last_picking.move_lines.write({
            'quantity_done': 1,
        })
        self.assertTrue(last_picking.action_done())
        self.assertEquals(last_picking.state, 'done')

    def test_recreate_with_return(self):
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
        picking = sale.picking_ids
        self.picking_transfer(picking, 10)
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
        picking2 = sale.picking_ids - picking
        self.picking_transfer(picking2, 1)
        self.assertEquals(sale.order_line.qty_delivered, 9)
        self.assertEquals(len(sale.picking_ids), 2)
        sale.action_recreate_picking()
        self.assertEquals(len(sale.picking_ids), 3)
