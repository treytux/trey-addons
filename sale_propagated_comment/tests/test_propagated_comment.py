###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestPurchasePropagatedComment(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Customer Partner #1',
            'customer': True,
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Purchase Product',
            'purchase_method': 'purchase',
            'type': 'product',
        })
        self.order_comment = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'sale_propagated_comment': 'Comment to propagated',
        })
        self.order_no_comment = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self.so_line_comment = self.env['sale.order.line'].create({
            'order_id': self.order_comment.id,
            'product_id': self.product.id,
            'name': 'Line 1',
            'product_uom_qty': 1.0,
            'product_uom': self.product.uom_id.id,
            'price_unit': 600.0,
        })
        self.so_line_no_comment = self.env['sale.order.line'].create({
            'order_id': self.order_no_comment.id,
            'product_id': self.product.id,
            'name': 'Line 1',
            'product_uom_qty': 1.0,
            'product_uom': self.product.uom_id.id,
            'price_unit': 600.0,
        })

    def picking_done(self, picking):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()

    def test_order_comment(self):
        self.order_comment.action_confirm()
        self.assertEquals(self.order_comment.state, 'sale')
        self.assertTrue(self.order_comment.picking_ids)
        self.assertTrue(
            self.order_comment.picking_ids[0].sale_propagated_comment)
        self.assertEquals(
            self.order_comment.picking_ids[0].sale_propagated_comment,
            'Comment to propagated')
        self.picking_done(self.order_comment.picking_ids[0])

    def test_order_no_comment(self):
        self.order_no_comment.action_confirm()
        self.assertEquals(self.order_no_comment.state, 'sale')
        self.assertTrue(self.order_no_comment.picking_ids)
        self.assertFalse(
            self.order_no_comment.picking_ids[0].sale_propagated_comment)
