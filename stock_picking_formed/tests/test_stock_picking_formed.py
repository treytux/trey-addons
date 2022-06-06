###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests import common


class TestStockPickingFormed(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': False,
        })
        self.product = self.env['product.product'].create({
            'type': 'consu',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 2,
                    'price_unit': 15,
                }),
            ],
        })

    def test_check_update_true_is_formed(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_assign()
        self.assertFalse(picking.is_formed)
        comments = len(picking.message_ids)
        picking.update_is_formed()
        self.assertTrue(picking.is_formed)
        self.assertEqual(comments + 1, len(picking.message_ids))
        self.assertIn(
            'Picking %s is formed' % picking.name,
            picking.message_ids[0].body)

    def test_check_update_false_is_formed(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_assign()
        self.assertFalse(picking.is_formed)
        comments = len(picking.message_ids)
        picking.update_is_formed()
        self.assertTrue(picking.is_formed)
        self.assertEqual(comments + 1, len(picking.message_ids))
        self.assertIn(
            'Picking %s is formed' % picking.name,
            picking.message_ids[0].body)
        picking.update_is_formed()
        self.assertFalse(picking.is_formed)
        self.assertIn(
            'Picking %s is not formed' % picking.name,
            picking.message_ids[0].body)

    def test_validate_picking_formed_01(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertFalse(picking.is_formed)
        comments = len(picking.message_ids)
        picking.update_is_formed()
        self.assertTrue(picking.is_formed)
        self.assertEqual(comments + 1, len(picking.message_ids))
        self.assertIn(
            'Picking %s is formed' % picking.name, picking.message_ids[0].body)
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(picking.state, 'done')

    def test_validate_picking_formed_02(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertFalse(picking.is_formed)
        comments = len(picking.message_ids)
        picking.update_is_formed()
        self.assertTrue(picking.is_formed)
        self.assertEqual(comments + 1, len(picking.message_ids))
        self.assertIn(
            'Picking %s is formed' % picking.name, picking.message_ids[0].body)
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()
        self.assertEqual(picking.state, 'done')

    def test_validate_picking_formed_03(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertFalse(picking.is_formed)
        comments = len(picking.message_ids)
        picking.update_is_formed()
        self.assertTrue(picking.is_formed)
        self.assertEqual(comments + 1, len(picking.message_ids))
        self.assertIn(
            'Picking %s is formed' % picking.name, picking.message_ids[0].body)
        result = picking.button_validate()
        wizard = self.env['stock.immediate.transfer'].browse(result['res_id'])
        self.assertEqual(len(wizard), 1)
        self.assertEqual(len(wizard.pick_ids), 1)
        wizard.process()
        self.assertEqual(picking.state, 'done')

    def test_validate_picking_formed_04(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertFalse(picking.is_formed)
        comments = len(picking.message_ids)
        picking.update_is_formed()
        self.assertTrue(picking.is_formed)
        self.assertEqual(comments + 1, len(picking.message_ids))
        self.assertIn(
            'Picking %s is formed' % picking.name, picking.message_ids[0].body)
        self.assertEqual(picking.move_lines[0].product_uom_qty, 2)
        picking.move_lines[0].quantity_done = 1
        self.assertEqual(picking.move_lines[0].quantity_done, 1)
        result = picking.button_validate()
        wizard = self.env['stock.backorder.confirmation'].browse(
            result['res_id'])
        self.assertEqual(len(wizard), 1)
        self.assertEqual(len(wizard.pick_ids), 1)
        wizard.process()
        self.assertEqual(picking.state, 'done')

    def test_validate_picking_formed_05(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertFalse(picking.is_formed)
        comments = len(picking.message_ids)
        picking.update_is_formed()
        self.assertTrue(picking.is_formed)
        self.assertEqual(comments + 1, len(picking.message_ids))
        self.assertIn(
            'Picking %s is formed' % picking.name, picking.message_ids[0].body)
        self.assertEqual(picking.move_lines[0].product_uom_qty, 2)
        picking.move_lines[0].quantity_done = 1
        self.assertEqual(picking.move_lines[0].quantity_done, 1)
        result = picking.button_validate()
        wizard = self.env['stock.backorder.confirmation'].browse(
            result['res_id'])
        self.assertEqual(len(wizard), 1)
        self.assertEqual(len(wizard.pick_ids), 1)
        wizard.process_cancel_backorder()
        self.assertEqual(picking.state, 'done')

    def test_validate_picking_without_be_formed_01(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertFalse(picking.is_formed)
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        with self.assertRaises(exceptions.ValidationError) as result:
            picking.action_done()
        self.assertEqual(
            result.exception.name,
            'Cannot validate picking %s without be formed' % picking.name)

    def test_validate_picking_without_be_formed_02(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertFalse(picking.is_formed)
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        with self.assertRaises(exceptions.ValidationError) as result:
            picking.button_validate()
        self.assertEqual(
            result.exception.name,
            'Cannot validate picking %s without be formed' % picking.name)

    def test_validate_picking_without_be_formed_03(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertFalse(picking.is_formed)
        result = picking.button_validate()
        wizard = self.env['stock.immediate.transfer'].browse(result['res_id'])
        self.assertEqual(len(wizard), 1)
        self.assertEqual(len(wizard.pick_ids), 1)
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.process()
        self.assertEqual(
            result.exception.name,
            'Cannot validate picking %s without be formed' % picking.name)

    def test_validate_picking_without_be_formed_04(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertFalse(picking.is_formed)
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines[0].product_uom_qty, 2)
        picking.move_lines[0].quantity_done = 1
        self.assertEqual(picking.move_lines[0].quantity_done, 1)
        result = picking.button_validate()
        wizard = self.env['stock.backorder.confirmation'].browse(
            result['res_id'])
        self.assertEqual(len(wizard), 1)
        self.assertEqual(len(wizard.pick_ids), 1)
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.process()
        self.assertEqual(
            result.exception.name,
            'Cannot validate picking %s without be formed' % picking.name)

    def test_validate_picking_without_be_formed_05(self):
        self.assertEqual(self.sale.state, 'draft')
        self.sale.action_confirm()
        self.assertEqual(self.sale.state, 'sale')
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        self.assertFalse(picking.is_formed)
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.move_lines[0].product_uom_qty, 2)
        picking.move_lines[0].quantity_done = 1
        self.assertEqual(picking.move_lines[0].quantity_done, 1)
        result = picking.button_validate()
        wizard = self.env['stock.backorder.confirmation'].browse(
            result['res_id'])
        self.assertEqual(len(wizard), 1)
        self.assertEqual(len(wizard.pick_ids), 1)
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.process_cancel_backorder()
        self.assertEqual(
            result.exception.name,
            'Cannot validate picking %s without be formed' % picking.name)
