###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests import common


class TestStockPickingReturnLimitQty(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': self.env.user.company_id.id,
            'name': 'Product test 1',
            'standard_price': 10,
            'list_price': 100,
        })
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product, location, 5)
        module = self.env['ir.module.module'].search([
            ('name', '=', 'sale'),
            ('state', '=', 'installed'),
        ])
        if module:
            self.sale = self.env['sale.order'].create({
                'partner_id': self.partner.id,
                'order_line': [
                    (0, 0, {
                        'product_id': self.product.id,
                        'product_uom_qty': 3,
                        'price_unit': 20,
                    })
                ],
            })

    def create_inventory(self, product, location, qty, lot_id=False):
        inventory = self.env['stock.inventory'].create({
            'name': 'Add products for test',
            'filter': 'partial',
            'location_id': location.id,
            'exhausted': True,
        })
        inventory.action_start()
        inventory.line_ids.create({
            'inventory_id': inventory.id,
            'product_id': product.id,
            'product_qty': qty,
            'location_id': location.id,
            'prod_lot_id': lot_id,
        })
        inventory._action_done()

    def check_modules_installed(self, module):
        module = self.env['ir.module.module'].search([
            ('name', '=', module),
        ])
        if module.state != 'installed':
            self.skipTest('Module %s not installed, ignore test.' % module)

    def test_check_return_limit_qty_01(self):
        self.check_modules_installed('sale')
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertEqual(len(self.sale.picking_ids), 1)
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_line_ids[0].product_id, self.product)
        self.assertEqual(picking.move_line_ids[0].product_uom_qty, 3)
        for move in picking.move_line_ids:
            move.qty_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(picking.state, 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.ids[0],
        )
        return_picking = return_picking.create({})
        self.assertEqual(return_picking.product_return_moves[0].quantity, 3)
        return_picking.product_return_moves.write({
            'quantity': 5.0,
            'to_refund': True,
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            return_picking.create_returns()
        self.assertEqual(
            'Is not possible to return more quantity than delivered',
            result.exception.name)
        return_picking.product_return_moves.write({
            'quantity': 3.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(self.sale.picking_ids), 2)

    def test_check_return_limit_qty_02(self):
        self.check_modules_installed('sale')
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertEqual(len(self.sale.picking_ids), 1)
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_line_ids[0].product_id, self.product)
        self.assertEqual(picking.move_line_ids[0].product_uom_qty, 3)
        for move in picking.move_line_ids:
            move.qty_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(picking.state, 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.ids[0],
        )
        return_picking = return_picking.create({})
        self.assertEqual(return_picking.product_return_moves[0].quantity, 3)
        return_picking.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        picking_ret = max(self.sale.picking_ids, key=lambda p: p.id)
        for move in picking_ret.move_line_ids:
            move.qty_done = move.product_uom_qty
        picking_ret.action_done()
        self.assertEqual(picking_ret.state, 'done')
        self.assertEqual(self.sale.order_line[0].product_uom_qty, 3)
        self.assertEqual(self.sale.order_line[0].qty_delivered, 2)
        return_picking_02 = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.ids[0],
        )
        return_picking_02 = return_picking_02.create({})
        self.assertEqual(return_picking_02.product_return_moves[0].quantity, 2)
        return_picking_02.product_return_moves.write({
            'quantity': 3.0,
            'to_refund': True,
        })
        with self.assertRaises(exceptions.ValidationError) as result:
            return_picking_02.create_returns()
        self.assertEqual(
            'Is not possible to return more quantity than delivered',
            result.exception.name)
        return_picking_02.product_return_moves.write({
            'quantity': 2.0,
            'to_refund': True,
        })
        return_picking_02.create_returns()
        self.assertEqual(len(self.sale.picking_ids), 3)
