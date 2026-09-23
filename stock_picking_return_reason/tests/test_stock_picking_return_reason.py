###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests import common


class TestStockPickingReturnReason(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 25,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 2,
                    'price_unit': 25,
                }),
            ],
        })
        self.reason = self.env['stock.picking.return.reason'].create({
            'name': 'Return reason test',
            'description': 'Summary of return reason test',
        })

    def picking_transfer(self, picking, qty):
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = qty
        picking.action_done()

    def test_return_reason_with_duplicate_name(self):
        with self.assertRaises(ValidationError) as result:
            self.env['stock.picking.return.reason'].create({
                'name': 'Return reason test',
                'description': 'Summary test 2',
            })
        self.assertEqual(
            result.exception.name, 'The reason name must be unique!')

    def test_stock_return_with_reason(self):
        self.assertEqual(self.reason.pickings_count, 0)
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        self.assertFalse(picking.return_reason_id)
        self.picking_transfer(picking, 2)
        self.assertEqual(picking.state, 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.id,
        ).create({})
        self.assertFalse(return_picking.return_reason)
        self.assertTrue(return_picking.location_id)
        return_picking.return_reason = self.reason.id
        self.assertEqual(return_picking.return_reason, self.reason)
        return_picking.product_return_moves.write({
            'quantity': 2,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(self.sale.picking_ids), 2)
        picking_ret = self.sale.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(picking_ret), 1)
        self.assertEqual(picking.return_reason_id, self.reason)
        self.assertEqual(self.reason.pickings_count, 1)
        self.assertEqual(len(self.reason.picking_ids), 1)
        self.assertEqual(self.reason.picking_ids[0], picking)
        sale_02 = self.sale.copy()
        self.assertEqual(sale_02.state, 'draft')
        sale_02.action_confirm()
        picking_02 = sale_02.picking_ids[0]
        self.assertFalse(picking_02.return_reason_id)
        self.picking_transfer(picking_02, 2)
        self.assertEqual(picking_02.state, 'done')
        return_picking_02 = self.env['stock.return.picking'].with_context(
            active_ids=picking_02.ids,
            active_id=picking_02.id,
        ).create({})
        self.assertFalse(return_picking_02.return_reason)
        return_picking_02.return_reason = self.reason.id
        self.assertEqual(return_picking_02.return_reason, self.reason)
        return_picking_02.product_return_moves.write({
            'quantity': 2,
            'to_refund': True,
        })
        return_picking_02.create_returns()
        self.assertEqual(len(sale_02.picking_ids), 2)
        picking_ret_02 = sale_02.picking_ids.filtered(
            lambda p: p.state == 'assigned')
        self.assertEqual(len(picking_ret_02), 1)
        self.assertEqual(picking_02.return_reason_id, self.reason)
        self.assertEqual(self.reason.pickings_count, 2)
        self.assertEqual(len(self.reason.picking_ids), 2)
        picking_reason_01 = self.reason.picking_ids.filtered(
            lambda p: p.id == picking.id)
        self.assertEqual(len(picking_reason_01), 1)
        picking_reason_02 = self.reason.picking_ids.filtered(
            lambda p: p.id == picking_02.id)
        self.assertEqual(len(picking_reason_02), 1)
