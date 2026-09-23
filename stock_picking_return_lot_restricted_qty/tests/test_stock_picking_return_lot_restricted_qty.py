###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions, fields
from odoo.tests import common


class TestStockPickingReturnLotRestrictedQty(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': False,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': self.env.user.company_id.id,
            'name': 'Test product 1',
            'standard_price': 10,
            'list_price': 100,
            'tracking': 'lot',
            'sale_line_warn': 'no-message',
        })
        self.lot_01 = self.env['stock.production.lot'].create({
            'name': '123456789',
            'product_id': self.product.id,
        })
        self.lot_02 = self.env['stock.production.lot'].create({
            'name': '987654321',
            'product_id': self.product.id,
        })
        self.lot_03 = self.env['stock.production.lot'].create({
            'name': '147258369',
            'product_id': self.product.id,
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'product',
            'company_id': self.env.user.company_id.id,
            'name': 'Test product 2',
            'standard_price': 10,
            'list_price': 100,
            'tracking': 'lot',
            'sale_line_warn': 'no-message',
        })
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product, location, 2, lot_id=self.lot_01.id)
        self.create_inventory(self.product, location, 1, lot_id=self.lot_02.id)
        self.create_inventory(self.product, location, 1, lot_id=self.lot_03.id)
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

    def test_sale_return_lot_standard(self):
        self.check_modules_installed('sale')
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertEqual(len(self.sale.picking_ids), 1)
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(len(picking.move_line_ids), 2)
        self.assertEqual(picking.move_line_ids[0].product_id, self.product)
        self.assertEqual(picking.move_line_ids[1].product_id, self.product)
        self.assertEqual(picking.move_line_ids[0].product_uom_qty, 2)
        self.assertEqual(picking.move_line_ids[1].product_uom_qty, 1)
        self.assertEqual(picking.move_line_ids[0].lot_id, self.lot_01)
        self.assertEqual(picking.move_line_ids[1].lot_id, self.lot_02)
        for move in picking.move_line_ids:
            move.qty_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(picking.state, 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.write({
            'quantity': 3.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(self.sale.picking_ids), 2)
        picking_ret = max(self.sale.picking_ids, key=lambda p: p.id)
        self.assertEqual(len(picking_ret.move_lines), 1)
        self.assertEqual(len(picking_ret.move_line_ids), 1)
        self.assertEqual(picking_ret.move_line_ids[0].product_uom_qty, 3)
        self.assertFalse(picking_ret.move_line_ids[0].lot_id)
        move_line_qty_01 = picking.move_line_ids[0].product_uom_qty
        move_line_qty_02 = picking_ret.move_line_ids[0].product_uom_qty
        self.assertTrue(move_line_qty_01 < move_line_qty_02)
        picking_ret.move_line_ids[0].lot_id = self.lot_01.id
        self.assertEqual(picking_ret.move_line_ids[0].lot_id, self.lot_01)
        for move in picking_ret.move_line_ids:
            move.qty_done = move.product_uom_qty
        with self.assertRaises(exceptions.ValidationError) as result:
            picking_ret.action_done()
        self.assertIn('You cannot return', result.exception.name)

    def test_sale_partial_return_lot_01(self):
        self.check_modules_installed('sale')
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertEqual(len(self.sale.picking_ids), 1)
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(len(picking.move_line_ids), 2)
        self.assertEqual(picking.move_line_ids[0].product_id, self.product)
        self.assertEqual(picking.move_line_ids[1].product_id, self.product)
        self.assertEqual(picking.move_line_ids[0].product_uom_qty, 2)
        self.assertEqual(picking.move_line_ids[1].product_uom_qty, 1)
        self.assertEqual(picking.move_line_ids[0].lot_id, self.lot_01)
        self.assertEqual(picking.move_line_ids[1].lot_id, self.lot_02)
        for move in picking.move_line_ids:
            move.qty_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(picking.state, 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.write({
            'quantity': 2.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(self.sale.picking_ids), 2)
        picking_ret = max(self.sale.picking_ids, key=lambda p: p.id)
        self.assertEqual(len(picking_ret.move_lines), 1)
        self.assertEqual(len(picking_ret.move_line_ids), 1)
        self.assertEqual(picking_ret.move_line_ids[0].product_uom_qty, 2)
        self.assertFalse(picking_ret.move_line_ids[0].lot_id)
        picking_ret.move_line_ids[0].lot_id = self.lot_02.id
        self.assertEqual(picking_ret.move_line_ids[0].lot_id, self.lot_02)
        for move in picking_ret.move_line_ids:
            move.qty_done = move.product_uom_qty
        with self.assertRaises(exceptions.ValidationError) as result:
            picking_ret.action_done()
        self.assertIn('You cannot return', result.exception.name)
        picking_ret.move_line_ids[0].lot_id = self.lot_01.id
        self.assertEqual(picking_ret.move_line_ids[0].lot_id, self.lot_01)
        picking_ret.action_done()
        self.assertEqual(picking_ret.state, 'done')

    def test_sale_partial_return_lot_02(self):
        self.check_modules_installed('sale')
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertEqual(len(self.sale.picking_ids), 1)
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(len(picking.move_line_ids), 2)
        self.assertEqual(picking.move_line_ids[0].product_id, self.product)
        self.assertEqual(picking.move_line_ids[1].product_id, self.product)
        self.assertEqual(picking.move_line_ids[0].product_uom_qty, 2)
        self.assertEqual(picking.move_line_ids[1].product_uom_qty, 1)
        self.assertEqual(picking.move_line_ids[0].lot_id, self.lot_01)
        self.assertEqual(picking.move_line_ids[1].lot_id, self.lot_02)
        for move in picking.move_line_ids:
            move.qty_done = 1
        wizard = self.env['stock.backorder.confirmation'].create({
            'pick_ids': [(4, picking.id)],
        })
        wizard.process()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(len(self.sale.picking_ids), 2)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.write({
            'quantity': 2.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(self.sale.picking_ids), 3)
        picking_ret = max(self.sale.picking_ids, key=lambda p: p.id)
        self.assertEqual(len(picking_ret.move_lines), 1)
        self.assertEqual(len(picking_ret.move_line_ids), 1)
        self.assertEqual(picking_ret.move_line_ids[0].product_uom_qty, 2)
        self.assertFalse(picking_ret.move_line_ids[0].lot_id)
        picking_ret.move_line_ids[0].lot_id = self.lot_02.id
        self.assertEqual(picking_ret.move_line_ids[0].lot_id, self.lot_02)
        for move in picking_ret.move_line_ids:
            move.qty_done = move.product_uom_qty
        with self.assertRaises(exceptions.ValidationError) as result:
            picking_ret.action_done()
        self.assertIn('You cannot return', result.exception.name)
        picking_ret.move_line_ids[0].lot_id = self.lot_01.id
        self.assertEqual(picking_ret.move_line_ids[0].lot_id, self.lot_01)
        with self.assertRaises(exceptions.ValidationError) as result:
            picking_ret.action_done()
        self.assertIn('You cannot return', result.exception.name)

    def test_sale_partial_return_lot_03(self):
        self.check_modules_installed('sale')
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertEqual(len(self.sale.picking_ids), 1)
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(len(picking.move_line_ids), 2)
        self.assertEqual(picking.move_line_ids[0].product_id, self.product)
        self.assertEqual(picking.move_line_ids[1].product_id, self.product)
        self.assertEqual(picking.move_line_ids[0].product_uom_qty, 2)
        self.assertEqual(picking.move_line_ids[1].product_uom_qty, 1)
        self.assertEqual(picking.move_line_ids[0].lot_id, self.lot_01)
        self.assertEqual(picking.move_line_ids[1].lot_id, self.lot_02)
        for move in picking.move_line_ids:
            move.qty_done = 1
        wizard = self.env['stock.backorder.confirmation'].create({
            'pick_ids': [(4, picking.id)],
        })
        wizard.process()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(len(self.sale.picking_ids), 2)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.write({
            'quantity': 2.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(self.sale.picking_ids), 3)
        picking_ret = max(self.sale.picking_ids, key=lambda p: p.id)
        self.assertEqual(len(picking_ret.move_lines), 1)
        self.assertEqual(len(picking_ret.move_line_ids), 1)
        self.assertEqual(picking_ret.move_line_ids[0].product_uom_qty, 2)
        self.assertFalse(picking_ret.move_line_ids[0].lot_id)
        picking_ret.move_line_ids[0].lot_id = self.lot_03.id
        self.assertEqual(picking_ret.move_line_ids[0].lot_id, self.lot_03)
        for move in picking_ret.move_line_ids:
            move.qty_done = 1
        with self.assertRaises(exceptions.ValidationError) as result:
            picking_ret.action_done()
        self.assertIn(
            'You cannot return 1.0 units of lot %s when 0 have been' % (
                self.lot_03.name),
            result.exception.name)

    def test_sale_partial_return_lot_04(self):
        self.check_modules_installed('sale')
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertEqual(len(self.sale.picking_ids), 1)
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(len(picking.move_line_ids), 2)
        self.assertEqual(picking.move_line_ids[0].product_id, self.product)
        self.assertEqual(picking.move_line_ids[1].product_id, self.product)
        self.assertEqual(picking.move_line_ids[0].product_uom_qty, 2)
        self.assertEqual(picking.move_line_ids[1].product_uom_qty, 1)
        self.assertEqual(picking.move_line_ids[0].lot_id, self.lot_01)
        self.assertEqual(picking.move_line_ids[1].lot_id, self.lot_02)
        for move in picking.move_line_ids:
            move.qty_done = 1
        wizard = self.env['stock.backorder.confirmation'].create({
            'pick_ids': [(4, picking.id)],
        })
        wizard.process()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(len(self.sale.picking_ids), 2)
        backorder = self.sale.picking_ids.filtered(lambda p: p.state != 'done')
        self.assertEqual(len(backorder), 1)
        self.assertEqual(len(backorder.move_line_ids), 1)
        self.assertEqual(backorder.move_line_ids[0].product_uom_qty, 1)
        backorder.move_line_ids[0].lot_id = self.lot_03.id
        self.assertEqual(backorder.move_line_ids[0].lot_id, self.lot_03)
        for move in backorder.move_line_ids:
            move.qty_done = move.product_uom_qty
        backorder.action_done()
        self.assertEqual(backorder.state, 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=backorder.ids,
            active_id=backorder.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.write({
            'quantity': 1.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(self.sale.picking_ids), 3)
        picking_ret = max(self.sale.picking_ids, key=lambda p: p.id)
        self.assertEqual(len(picking_ret.move_lines), 1)
        self.assertEqual(len(picking_ret.move_line_ids), 1)
        self.assertEqual(picking_ret.move_line_ids[0].product_uom_qty, 1)
        self.assertFalse(picking_ret.move_line_ids[0].lot_id)
        for move in picking_ret.move_line_ids:
            move.qty_done = 1
        picking_ret.move_line_ids[0].lot_id = self.lot_01.id
        self.assertEqual(picking_ret.move_line_ids[0].lot_id, self.lot_01)
        with self.assertRaises(exceptions.ValidationError) as result:
            picking_ret.action_done()
        self.assertIn('You cannot return', result.exception.name)
        picking_ret.move_line_ids[0].lot_id = self.lot_02.id
        self.assertEqual(picking_ret.move_line_ids[0].lot_id, self.lot_02)
        with self.assertRaises(exceptions.ValidationError) as result:
            picking_ret.action_done()
        self.assertIn('You cannot return', result.exception.name)
        picking_ret.move_line_ids[0].lot_id = self.lot_03.id
        self.assertEqual(picking_ret.move_line_ids[0].lot_id, self.lot_03)
        picking_ret.action_done()
        self.assertEqual(picking_ret.state, 'done')

    def test_sale_multiple_return_lot(self):
        self.check_modules_installed('sale')
        location = self.env.ref('stock.stock_location_stock')
        self.create_inventory(self.product, location, 4, lot_id=self.lot_01.id)
        self.assertEqual(self.sale.state, 'draft')
        self.sale.order_line[0].product_uom_qty = 4
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        self.assertEqual(len(self.sale.picking_ids), 1)
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(len(picking.move_line_ids), 1)
        self.assertEqual(picking.move_line_ids[0].product_id, self.product)
        self.assertEqual(picking.move_line_ids[0].product_uom_qty, 4)
        self.assertEqual(picking.move_line_ids[0].lot_id, self.lot_01)
        for move in picking.move_line_ids:
            move.qty_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(picking.state, 'done')
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.write({
            'quantity': 3.0,
            'to_refund': True,
        })
        return_picking.create_returns()
        self.assertEqual(len(self.sale.picking_ids), 2)
        picking_ret = max(self.sale.picking_ids, key=lambda p: p.id)
        self.assertEqual(len(picking_ret.move_lines), 1)
        self.assertEqual(len(picking_ret.move_line_ids), 1)
        self.assertEqual(picking_ret.move_line_ids[0].product_uom_qty, 3)
        self.assertFalse(picking_ret.move_line_ids[0].lot_id)
        picking_ret.move_line_ids[0].lot_id = self.lot_01.id
        self.assertEqual(picking_ret.move_line_ids[0].lot_id, self.lot_01)
        for move in picking_ret.move_line_ids:
            move.qty_done = move.product_uom_qty
        picking_ret.action_done()
        self.assertEqual(picking_ret.state, 'done')
        return_picking_02 = self.env['stock.return.picking'].with_context(
            active_ids=picking.ids,
            active_id=picking.ids[0],
        )
        return_picking_02 = return_picking_02.create({})
        return_picking_02.product_return_moves.write({
            'quantity': 3.0,
            'to_refund': True,
        })
        return_picking_02.create_returns()
        self.assertEqual(len(self.sale.picking_ids), 3)
        picking_ret_02 = max(self.sale.picking_ids, key=lambda p: p.id)
        self.assertEqual(len(picking_ret_02.move_lines), 1)
        self.assertEqual(len(picking_ret_02.move_line_ids), 1)
        self.assertEqual(picking_ret_02.move_line_ids[0].product_uom_qty, 3)
        self.assertFalse(picking_ret_02.move_line_ids[0].lot_id)
        picking_ret_02.move_line_ids[0].lot_id = self.lot_01.id
        self.assertEqual(picking_ret_02.move_line_ids[0].lot_id, self.lot_01)
        for move in picking_ret_02.move_line_ids:
            move.qty_done = move.product_uom_qty
        with self.assertRaises(exceptions.ValidationError) as result:
            picking_ret_02.action_done()
        self.assertIn(
            'You cannot return 3.0 units of lot %s when 1.0 have been' % (
                self.lot_01.name), result.exception.name)

    def test_purchase_return_lot_standard(self):
        self.check_modules_installed('purchase')
        self.purchase = self.env['purchase.order'].create({
            'name': 'TESTPURCHASE',
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_02.id,
                    'name': self.product_02.name,
                    'date_planned': fields.Date.today(),
                    'product_qty': 1,
                    'product_uom': self.product_02.uom_id.id,
                    'price_unit': 100.0,
                })
            ],
        })
        self.purchase.button_confirm()
        self.assertEqual(self.purchase.state, 'purchase')
        purchase_lot_01 = self.env['stock.production.lot'].create({
            'name': 'Lot 001',
            'product_id': self.product_02.id,
        })
        self.assertEqual(len(self.purchase.picking_ids), 1)
        picking = self.purchase.picking_ids[0]
        picking.move_line_ids[0].lot_id = purchase_lot_01.id
        self.assertEqual(picking.move_line_ids[0].product_uom_qty, 1)
        self.assertEqual(picking.move_line_ids[0].lot_id, purchase_lot_01)
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(picking.state, 'done')
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
        self.assertEqual(len(self.purchase.picking_ids), 2)
        picking_ret = max(self.purchase.picking_ids, key=lambda p: p.id)
        self.assertEqual(picking_ret.state, 'assigned')
        self.assertEqual(len(picking_ret.move_lines), 1)
        self.assertEqual(len(picking_ret.move_line_ids), 1)
        move_line = picking_ret.move_line_ids[0]
        self.assertEqual(move_line.lot_id, purchase_lot_01)
        for move in picking_ret.move_line_ids:
            move.qty_done = move.product_uom_qty
        picking_ret.action_done()
        self.assertEqual(picking_ret.state, 'done')
