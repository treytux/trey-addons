###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)


class TestSalePropagatedComment(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Customer Partner #1',
            'customer_rank': 1,
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Sale Product',
            'invoice_policy': 'order',
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
        for move in picking.move_ids:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()

    def test_comment_from_partner(self):
        self.partner.sale_propagated_comment = 'Partner comment'
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self.assertEqual(
            order.sale_propagated_comment, 'Partner comment')

    def test_order_comment(self):
        self.order_comment.action_confirm()
        self.assertEqual(self.order_comment.state, 'sale')
        self.assertTrue(self.order_comment.picking_ids)
        picking = self.order_comment.picking_ids[0]
        self.assertEqual(
            picking.sale_propagated_comment,
            self.order_comment.sale_propagated_comment)
        self.picking_done(picking)
        invoice = self.order_comment._create_invoices()
        self.assertTrue(invoice)
        self.assertEqual(
            invoice.sale_propagated_comment,
            self.order_comment.sale_propagated_comment)
        _log.info('Value of comment: %s' %
                  self.order_comment.sale_propagated_comment)

    def test_order_no_comment(self):
        self.order_no_comment.action_confirm()
        self.assertEqual(self.order_no_comment.state, 'sale')
        self.assertTrue(self.order_no_comment.picking_ids)
        picking = self.order_no_comment.picking_ids[0]
        self.assertFalse(picking.sale_propagated_comment)
        self.picking_done(picking)
        invoice = self.order_no_comment._create_invoices()
        self.assertTrue(invoice)
        self.assertFalse(invoice.sale_propagated_comment)
        _log.info('Value of comment: %s' %
                  self.order_no_comment.sale_propagated_comment)
