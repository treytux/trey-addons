###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)


class TestPurchasePropagatedComment(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Supplier Partner #1',
            'supplier': True,
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Purchase Product',
            'purchase_method': 'purchase',
            'type': 'product',
        })
        self.order_comment = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'purchase_propagated_comment': 'Comment to propagated'
        })
        self.order_no_comment = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        self.po_line_comment = self.env['purchase.order.line'].create({
            'order_id': self.order_comment.id,
            'product_id': self.product.id,
            'date_planned': '2020-07-19 00:00:00',
            'name': 'Line 1',
            'product_qty': 1.0,
            'product_uom': self.product.uom_id.id,
            'price_unit': 600.0,
        })
        self.po_line_no_comment = self.env['purchase.order.line'].create({
            'order_id': self.order_no_comment.id,
            'product_id': self.product.id,
            'date_planned': '2020-07-19 00:00:00',
            'name': 'Line 1',
            'product_qty': 1.0,
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
        self.order_comment.button_confirm()
        self.assertEquals(self.order_comment.state, 'purchase')
        self.assertTrue(self.order_comment.picking_ids)
        self.assertTrue(
            self.order_comment.picking_ids[0].purchase_propagated_comment)
        self.picking_done(self.order_comment.picking_ids[0])
        _log.info('Value of comment: %s' %
                  self.order_comment.purchase_propagated_comment)

    def test_order_no_comment(self):
        self.order_no_comment.button_confirm()
        self.assertEquals(self.order_no_comment.state, 'purchase')
        self.assertTrue(self.order_no_comment.picking_ids)
        self.assertFalse(
            self.order_no_comment.picking_ids[0].purchase_propagated_comment)
        _log.info('Value of comment: %s' %
                  self.order_no_comment.purchase_propagated_comment)
