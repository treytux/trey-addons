# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common


class SaleWizardProcess(common.TransactionCase):

    def setUp(self):
        super(SaleWizardProcess, self).setUp()
        self.product_obj = self.env['product.product']
        self.lot_obj = self.env['stock.production.lot']
        self.partner = self.env['res.partner'].create({
            'name': 'Customer 01',
            'is_company': True,
            'customer': True,
            'email': 'customer_01@test.com'})
        self.product_uom_mm = self.env['product.uom'].create({
            'category_id': self.ref('product.uom_categ_length'),
            'name': 'mm',
            'uom_type': 'smaller',
            'factor': 1000})
        self.product_01 = self.product_obj.create({
            'name': 'Test stockable 01 (m2)',
            'type': 'product',
            'list_price': 10.50,
            'dimensional_uom_id': self.product_uom_mm.id,
            'height': 10000,
            'width': 2000})
        self.product_02 = self.product_obj.create({
            'name': 'Test stockable 02 (m3)',
            'type': 'product',
            'dimensional_uom_id': self.product_uom_mm.id,
            'list_price': 4.25,
            'length': 10000,
            'height': 20000,
            'width': 5000})
        self.product_03 = self.product_obj.create({
            'name': 'Test service 01',
            'type': 'service',
            'list_price': 5.99})
        self.product_04 = self.product_obj.create({
            'name': 'Test stockable 04 (m3)',
            'dimensional_uom_id': self.product_uom_mm.id,
            'type': 'product',
            'list_price': 33,
            'length': 1000,
            'height': 3000,
            'width': 5000})
        self.product_05 = self.product_obj.create({
            'name': 'Test stockable 05 (without measures)',
            'type': 'product',
            'list_price': 7,
            'length': 0,
            'height': 0,
            'width': 0})
        self.product_06 = self.product_obj.create({
            'name': 'Test consumable 06 (m2)',
            'type': 'consu',
            'list_price': 10.50,
            'dimensional_uom_id': self.product_uom_mm.id,
            'height': 10000,
            'width': 2000})
        self.product_07 = self.product_obj.create({
            'name': 'Test consumable 07 (m3)',
            'type': 'consu',
            'dimensional_uom_id': self.product_uom_mm.id,
            'list_price': 4.25,
            'length': 10000,
            'height': 20000,
            'width': 5000})
        self.product_08 = self.product_obj.create({
            'name': 'Test consumable 08 (m3)',
            'dimensional_uom_id': self.product_uom_mm.id,
            'type': 'consu',
            'list_price': 33,
            'length': 1000,
            'height': 3000,
            'width': 5000})
        self.product_09 = self.product_obj.create({
            'name': 'Test consumable 09 (without measures)',
            'type': 'consu',
            'list_price': 7,
            'length': 0,
            'height': 0,
            'width': 0})
        self.lot_01 = self.lot_obj.create({
            'name': 'LOT-000001',
            'product_id': self.product_01.id})
        self.lot_01_2 = self.lot_obj.create({
            'name': 'LOT-0000012',
            'product_id': self.product_01.id})
        self.lot_02 = self.lot_obj.create({
            'name': 'LOT-000002',
            'product_id': self.product_03.id})
        self.lot_03 = self.lot_obj.create({
            'name': 'LOT-000003',
            'product_id': self.product_03.id})
        self.lot_04 = self.lot_obj.create({
            'name': 'LOT-000004',
            'product_id': self.product_02.id})
        self.lot_04_2 = self.lot_obj.create({
            'name': 'LOT-0000042',
            'product_id': self.product_02.id})
        self.lot_06 = self.lot_obj.create({
            'name': 'LOT-000006',
            'product_id': self.product_06.id})
        self.lot_06_2 = self.lot_obj.create({
            'name': 'LOT-000062',
            'product_id': self.product_06.id})
        self.lot_07 = self.lot_obj.create({
            'name': 'LOT-000007',
            'product_id': self.product_07.id})
        self.lot_08 = self.lot_obj.create({
            'name': 'LOT-000008',
            'product_id': self.product_08.id})
        self.lot_09 = self.lot_obj.create({
            'name': 'LOT-000009',
            'product_id': self.product_09.id})

    def test_wizard_process_with_picking_stockable_m2(self):
        '''Create sale order with picking and invoice.'''
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id})
        line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'lot_id': self.lot_01.id,
            'qty_per_pallet': 250,
            'pallet_qty': 2})
        # Call onchange method of line and check uom qty of line
        line.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line.product_uom_qty, 500)
        self.assertEqual(line.m2, 10000)
        self.assertEqual(line.m3, 0)
        # Process order
        order.process_order()
        # Check that picking has been created.
        self.assertGreaterEqual(len(order.picking_ids), 1)
        # Check qty move and lot
        total_qty_pick = 0
        lots = []
        op_lots = []
        for picking in order.picking_ids:
            for move in picking.move_lines:
                total_qty_pick += move.product_uom_qty
                lots.append(move.lot_ids)
                for op in picking.pack_operation_ids:
                    op_lots.append(op.lot_id)
        self.assertEqual(total_qty_pick, 500)
        self.assertEqual(move.lot_ids, self.lot_01)
        self.assertEqual(move.product_uom_qty, 500)
        self.assertEqual(len(picking.pack_operation_ids), 1)
        self.assertEqual(op_lots, [self.lot_01])
        # Check picking state
        self.assertEqual(picking.invoice_state, 'invoiced')
        total_qty_inv = 0
        # Check qty invoice line
        for invoice in order.invoice_ids:
            for line in invoice.invoice_line:
                total_qty_inv += line.quantity
        # LessEqual because it can not all stock pickings have been generated
        # invoice.
        self.assertLessEqual(total_qty_inv, 500)

    def test_wizard_process_with_picking_consumable_m2(self):
        '''Create sale order with picking and invoice.'''
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id})
        line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_06.id,
            'lot_id': self.lot_06.id,
            'qty_per_pallet': 250,
            'pallet_qty': 2})
        # Call onchange method of line and check uom qty of line
        line.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line.product_uom_qty, 500)
        self.assertEqual(line.m2, 10000)
        self.assertEqual(line.m3, 0)
        # Process order
        order.process_order()
        # Check that picking has been created.
        self.assertGreaterEqual(len(order.picking_ids), 1)
        # Check qty move and lot
        total_qty_pick = 0
        lots = []
        op_lots = []
        for picking in order.picking_ids:
            for move in picking.move_lines:
                total_qty_pick += move.product_uom_qty
                lots.append(move.lot_ids)
                for op in picking.pack_operation_ids:
                    op_lots.append(op.lot_id)
        self.assertEqual(total_qty_pick, 500)
        self.assertEqual(move.lot_ids, self.lot_06)
        self.assertEqual(move.product_uom_qty, 500)
        self.assertEqual(len(picking.pack_operation_ids), 1)
        self.assertEqual(op_lots, [self.lot_06])
        # Check picking state
        self.assertEqual(picking.invoice_state, 'invoiced')
        total_qty_inv = 0
        # Check qty invoice line
        for invoice in order.invoice_ids:
            for line in invoice.invoice_line:
                total_qty_inv += line.quantity
        # LessEqual because it can not all stock pickings have been generated
        # invoice.
        self.assertLessEqual(total_qty_inv, 500)

    def test_wizard_process_with_picking_same_product_consumable_m2(self):
        '''Sale order with picking and invoice (same products, same lots).'''
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id})
        line_01 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_06.id,
            'lot_id': self.lot_06.id,
            'qty_per_pallet': 250,
            'pallet_qty': 2})
        line_02 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_06.id,
            'lot_id': self.lot_06_2.id,
            'qty_per_pallet': 2,
            'pallet_qty': 10})
        # Call onchange method of line and check uom qty of line
        line_01.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_01.product_uom_qty, 500)
        self.assertEqual(line_01.m2, 10000)
        self.assertEqual(line_01.m3, 0)
        line_02.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_02.product_uom_qty, 20)
        self.assertEqual(line_02.m2, 400)
        self.assertEqual(line_02.m3, 0)
        # Process order
        order.process_order()
        # Check that picking has been created.
        self.assertGreaterEqual(len(order.picking_ids), 1)
        # Check qty move and lot
        total_qty_pick = 0
        lots = []
        op_lots = []
        for picking in order.picking_ids:
            move1 = picking.move_lines[0]
            move2 = picking.move_lines[1]
            for move in picking.move_lines:
                total_qty_pick += move.product_uom_qty
                lots.append(move.lot_ids)
                for op in picking.pack_operation_ids:
                    op_lots.append(op.lot_id)
        # self.assertEqual(total_qty_pick, 900)
        self.assertEqual(total_qty_pick, 520)
        self.assertEqual(move1.lot_ids, self.lot_06)
        self.assertEqual(move2.lot_ids, self.lot_06_2)
        self.assertEqual(move1.product_uom_qty, 500)
        self.assertEqual(move2.product_uom_qty, 20)
        self.assertEqual(len(picking.pack_operation_ids), 2)
        self.assertEqual(
            list(set(op_lots)).sort(), [self.lot_06, self.lot_06_2].sort())
        # Check picking state
        self.assertEqual(picking.invoice_state, 'invoiced')
        total_qty_inv = 0
        # Check qty invoice line
        for invoice in order.invoice_ids:
            for line in invoice.invoice_line:
                total_qty_inv += line.quantity
        # LessEqual because it can not all stock pickings have been generated
        # invoice.
        # self.assertLessEqual(total_qty_inv, 900)
        self.assertLessEqual(total_qty_inv, 520)

    def test_wizard_process_with_picking_same_3product_stockable_m2(self):
        '''Order with picking and invoice (same products, different lots).'''
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id})
        line_01 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'lot_id': self.lot_01.id,
            'qty_per_pallet': 250,
            'pallet_qty': 2})
        line_02 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'lot_id': self.lot_01_2.id,
            'qty_per_pallet': 2,
            'pallet_qty': 10})
        line_03 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'lot_id': self.lot_01_2.id,
            'qty_per_pallet': 3,
            'pallet_qty': 15})
        # Call onchange method of line and check uom qty of line
        line_01.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_01.product_uom_qty, 500)
        self.assertEqual(line_01.m2, 10000)
        self.assertEqual(line_01.m3, 0)
        line_02.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_02.product_uom_qty, 20)
        self.assertEqual(line_02.m2, 400)
        self.assertEqual(line_02.m3, 0)
        line_03.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_03.product_uom_qty, 45)
        self.assertEqual(line_03.m2, 900)
        self.assertEqual(line_03.m3, 0)
        # Process order
        order.process_order()
        # Check that picking has been created.
        self.assertGreaterEqual(len(order.picking_ids), 1)
        # Check qty move and lot
        total_qty_pick = 0
        lots = []
        op_lots = []
        for picking in order.picking_ids:
            move1 = picking.move_lines[0]
            move2 = picking.move_lines[1]
            move3 = picking.move_lines[2]
            for move in picking.move_lines:
                total_qty_pick += move.product_uom_qty
                lots.append(move.lot_ids)
                for op in picking.pack_operation_ids:
                    op_lots.append(op.lot_id)
        self.assertEqual(total_qty_pick, 565)
        self.assertEqual(move1.lot_ids, self.lot_01)
        self.assertEqual(move2.lot_ids, self.lot_01_2)
        self.assertEqual(move3.lot_ids, self.lot_01_2)
        self.assertEqual(move1.product_uom_qty, 500)
        self.assertEqual(move2.product_uom_qty, 20)
        self.assertEqual(move3.product_uom_qty, 45)
        self.assertEqual(len(picking.pack_operation_ids), 3)
        self.assertEqual(
            list(set(op_lots)).sort(), [self.lot_01, self.lot_01_2].sort())
        # Check picking state
        self.assertEqual(picking.invoice_state, 'invoiced')
        total_qty_inv = 0
        # Check qty invoice line
        for invoice in order.invoice_ids:
            for line in invoice.invoice_line:
                total_qty_inv += line.quantity
        # LessEqual because it can not all stock pickings have been generated
        # invoice.
        self.assertLessEqual(total_qty_inv, 565)

    def test_wizard_process_with_picking_same_3_01_product_stockable_m2(self):
        '''Order with picking and invoice (same products, different lots).'''
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id})
        line_01 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'lot_id': self.lot_01.id,
            'qty_per_pallet': 250,
            'pallet_qty': 2})
        line_02 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'lot_id': self.lot_01_2.id,
            'qty_per_pallet': 2,
            'pallet_qty': 10})
        line_03 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_02.id,
            'lot_id': self.lot_02.id,
            'qty_per_pallet': 3,
            'pallet_qty': 7})
        line_04 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'lot_id': self.lot_01_2.id,
            'qty_per_pallet': 3,
            'pallet_qty': 15})
        # Call onchange method of line and check uom qty of line
        line_01.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_01.product_uom_qty, 500)
        self.assertEqual(line_01.m2, 10000)
        self.assertEqual(line_01.m3, 0)
        line_02.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_02.product_uom_qty, 20)
        self.assertEqual(line_02.m2, 400)
        self.assertEqual(line_02.m3, 0)
        line_03.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_03.product_uom_qty, 21)
        self.assertEqual(line_03.m2, 2100)
        self.assertEqual(line_03.m3, 21000)
        line_04.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_04.product_uom_qty, 45)
        self.assertEqual(line_04.m2, 900)
        self.assertEqual(line_04.m3, 0)
        # Process order
        order.process_order()
        # Check that picking has been created.
        self.assertGreaterEqual(len(order.picking_ids), 1)
        # Check qty move
        total_qty_pick = 0
        lots = []
        op_lots = []
        for picking in order.picking_ids:
            move1 = picking.move_lines[0]
            move2 = picking.move_lines[1]
            move3 = picking.move_lines[2]
            move4 = picking.move_lines[3]
            for move in picking.move_lines:
                total_qty_pick += move.product_uom_qty
                lots.append(move.lot_ids)
                for op in picking.pack_operation_ids:
                    op_lots.append(op.lot_id)
        self.assertEqual(total_qty_pick, 586)
        self.assertEqual(move1.lot_ids, self.lot_01)
        self.assertEqual(move2.lot_ids, self.lot_01_2)
        self.assertEqual(move3.lot_ids, self.lot_02)
        self.assertEqual(move4.lot_ids, self.lot_01_2)
        self.assertEqual(move1.product_uom_qty, 500)
        self.assertEqual(move2.product_uom_qty, 20)
        self.assertEqual(move3.product_uom_qty, 21)
        self.assertEqual(move4.product_uom_qty, 45)
        self.assertEqual(len(picking.pack_operation_ids), 4)
        self.assertEqual(
            list(set(op_lots)).sort(), [
                self.lot_01, self.lot_01_2, self.lot_02].sort())
        # Check picking state
        self.assertEqual(picking.invoice_state, 'invoiced')
        total_qty_inv = 0
        # Check qty invoice line
        for invoice in order.invoice_ids:
            for line in invoice.invoice_line:
                total_qty_inv += line.quantity
        # LessEqual because it can not all stock pickings have been generated
        # invoice.
        self.assertLessEqual(total_qty_inv, 586)

    def test_wizard_process_with_picking_same_3_02_product_stockable_m2(self):
        '''Order with picking and invoice (same products, different lots).'''
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id})
        line_01 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'lot_id': self.lot_01.id,
            'qty_per_pallet': 250,
            'pallet_qty': 2})
        line_02 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'lot_id': self.lot_01_2.id,
            'qty_per_pallet': 2,
            'pallet_qty': 10})
        line_03 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_02.id,
            'lot_id': self.lot_04.id,
            'qty_per_pallet': 3,
            'pallet_qty': 7})
        line_04 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'lot_id': self.lot_01_2.id,
            'qty_per_pallet': 3,
            'pallet_qty': 15})
        line_05 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_02.id,
            'lot_id': self.lot_04_2.id,
            'qty_per_pallet': 4,
            'pallet_qty': 8})
        # Call onchange method of line and check uom qty of line
        line_01.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_01.product_uom_qty, 500)
        self.assertEqual(line_01.m2, 10000)
        self.assertEqual(line_01.m3, 0)
        line_02.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_02.product_uom_qty, 20)
        self.assertEqual(line_02.m2, 400)
        self.assertEqual(line_02.m3, 0)
        line_03.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_03.product_uom_qty, 21)
        self.assertEqual(line_03.m2, 2100)
        self.assertEqual(line_03.m3, 21000)
        line_04.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_04.product_uom_qty, 45)
        self.assertEqual(line_04.m2, 900)
        self.assertEqual(line_04.m3, 0)
        line_05.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_05.product_uom_qty, 32)
        self.assertEqual(line_05.m2, 3200)
        self.assertEqual(line_05.m3, 32000)
        # Process order
        order.process_order()
        # Check that picking has been created.
        self.assertGreaterEqual(len(order.picking_ids), 1)
        # Check qty move and lot
        total_qty_pick = 0
        lots = []
        op_lots = []
        for picking in order.picking_ids:
            move1 = picking.move_lines[0]
            move2 = picking.move_lines[1]
            move3 = picking.move_lines[2]
            move4 = picking.move_lines[3]
            move5 = picking.move_lines[4]
            for move in picking.move_lines:
                total_qty_pick += move.product_uom_qty
                lots.append(move.lot_ids)
                for op in picking.pack_operation_ids:
                    op_lots.append(op.lot_id)
        self.assertEqual(total_qty_pick, 618)
        self.assertEqual(move1.lot_ids, self.lot_01)
        self.assertEqual(move2.lot_ids, self.lot_01_2)
        self.assertEqual(move3.lot_ids, self.lot_04)
        self.assertEqual(move4.lot_ids, self.lot_01_2)
        self.assertEqual(move5.lot_ids, self.lot_04_2)
        self.assertEqual(move1.product_uom_qty, 500)
        self.assertEqual(move2.product_uom_qty, 20)
        self.assertEqual(move3.product_uom_qty, 21)
        self.assertEqual(move4.product_uom_qty, 45)
        self.assertEqual(move5.product_uom_qty, 32)
        self.assertEqual(len(picking.pack_operation_ids), 5)
        self.assertEqual(
            list(set(op_lots)).sort(), [
                self.lot_01, self.lot_01_2, self.lot_04, self.lot_04_2].sort())
        # Check picking state
        self.assertEqual(picking.invoice_state, 'invoiced')
        total_qty_inv = 0
        # Check qty invoice line
        for invoice in order.invoice_ids:
            for line in invoice.invoice_line:
                total_qty_inv += line.quantity
        # LessEqual because it can not all stock pickings have been generated
        # invoice.
        self.assertLessEqual(total_qty_inv, 618)

    def test_wizard_process_with_picking_same_product_no_lots_01stockable_m2(
            self):
        '''Sale order with picking and invoice (same products without lots).'''
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id})
        line_01 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'qty_per_pallet': 250,
            'pallet_qty': 2})
        line_02 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'qty_per_pallet': 2,
            'pallet_qty': 10})
        # Call onchange method of line and check uom qty of line
        line_01.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_01.product_uom_qty, 500)
        self.assertEqual(line_01.m2, 10000)
        self.assertEqual(line_01.m3, 0)
        line_02.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_02.product_uom_qty, 20)
        self.assertEqual(line_02.m2, 400)
        self.assertEqual(line_02.m3, 0)
        # Process order
        order.process_order()
        # Check that picking has been created.
        self.assertGreaterEqual(len(order.picking_ids), 1)
        # Check qty move and lot
        total_qty_pick = 0
        for picking in order.picking_ids:
            move1 = picking.move_lines[0]
            move2 = picking.move_lines[1]
            for move in picking.move_lines:
                total_qty_pick += move.product_uom_qty
        # self.assertEqual(total_qty_pick, 900)
        self.assertEqual(total_qty_pick, 520)
        self.assertFalse(move1.lot_ids.exists())
        self.assertFalse(move2.lot_ids.exists())
        self.assertEqual(move1.product_uom_qty, 500)
        self.assertEqual(move2.product_uom_qty, 20)
        self.assertEqual(len(picking.pack_operation_ids), 2)
        # Check picking state
        self.assertEqual(picking.invoice_state, 'invoiced')
        total_qty_inv = 0
        # Check qty invoice line
        for invoice in order.invoice_ids:
            for line in invoice.invoice_line:
                total_qty_inv += line.quantity
        # LessEqual because it can not all stock pickings have been generated
        # invoice.
        # self.assertLessEqual(total_qty_inv, 900)
        self.assertLessEqual(total_qty_inv, 520)

    def test_wizard_process_with_picking_same_product_no_lots_02_stockable_m2(
            self):
        '''Sale order with picking and invoice (same products without lots).'''
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id})
        line_01 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'qty_per_pallet': 250,
            'pallet_qty': 2})
        line_02 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'qty_per_pallet': 2,
            'pallet_qty': 10})
        line_03 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_02.id,
            'qty_per_pallet': 3,
            'pallet_qty': 7})
        line_04 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'qty_per_pallet': 3,
            'pallet_qty': 15})
        # Call onchange method of line and check uom qty of line
        line_01.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_01.product_uom_qty, 500)
        self.assertEqual(line_01.m2, 10000)
        self.assertEqual(line_01.m3, 0)
        line_02.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_02.product_uom_qty, 20)
        self.assertEqual(line_02.m2, 400)
        self.assertEqual(line_02.m3, 0)
        line_03.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_03.product_uom_qty, 21)
        self.assertEqual(line_03.m2, 2100)
        self.assertEqual(line_03.m3, 21000)
        line_04.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_04.product_uom_qty, 45)
        self.assertEqual(line_04.m2, 900)
        self.assertEqual(line_04.m3, 0)
        # Process order
        order.process_order()
        # Check that picking has been created.
        self.assertGreaterEqual(len(order.picking_ids), 1)
        # Check qty move
        total_qty_pick = 0
        lots = []
        for picking in order.picking_ids:
            move1 = picking.move_lines[0]
            move2 = picking.move_lines[1]
            move3 = picking.move_lines[2]
            move4 = picking.move_lines[3]
            for move in picking.move_lines:
                total_qty_pick += move.product_uom_qty
                lots.append(move.lot_ids)
        self.assertFalse(move1.lot_ids.exists())
        self.assertFalse(move2.lot_ids.exists())
        self.assertFalse(move3.lot_ids.exists())
        self.assertFalse(move4.lot_ids.exists())
        self.assertEqual(move1.product_uom_qty, 500)
        self.assertEqual(move2.product_uom_qty, 20)
        self.assertEqual(move3.product_uom_qty, 21)
        self.assertEqual(move4.product_uom_qty, 45)
        self.assertEqual(len(picking.pack_operation_ids), 4)
        # Check picking state
        self.assertEqual(picking.invoice_state, 'invoiced')
        total_qty_inv = 0
        # Check qty invoice line
        for invoice in order.invoice_ids:
            for line in invoice.invoice_line:
                total_qty_inv += line.quantity
        # LessEqual because it can not all stock pickings have been generated
        # invoice.
        self.assertLessEqual(total_qty_inv, 586)

    def test_wizard_process_with_picking_same_product_no_lots_03_stockable_m2(
            self):
        '''Sale order with picking and invoice (same products without lots).'''
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id})
        line_01 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'qty_per_pallet': 250,
            'pallet_qty': 2})
        line_02 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'qty_per_pallet': 2,
            'pallet_qty': 10})
        line_03 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_02.id,
            'qty_per_pallet': 3,
            'pallet_qty': 7})
        line_04 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'qty_per_pallet': 3,
            'pallet_qty': 15})
        line_05 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_02.id,
            'qty_per_pallet': 2,
            'pallet_qty': 4})
        # Call onchange method of each line and check uom qty of line
        line_01.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_01.product_uom_qty, 500)
        self.assertEqual(line_01.m2, 10000)
        self.assertEqual(line_01.m3, 0)
        line_02.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_02.product_uom_qty, 20)
        self.assertEqual(line_02.m2, 400)
        self.assertEqual(line_02.m3, 0)
        line_03.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_03.product_uom_qty, 21)
        self.assertEqual(line_03.m2, 2100)
        self.assertEqual(line_03.m3, 21000)
        line_04.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_04.product_uom_qty, 45)
        self.assertEqual(line_04.m2, 900)
        self.assertEqual(line_04.m3, 0)
        line_05.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_05.product_uom_qty, 8)
        self.assertEqual(line_05.m2, 800)
        self.assertEqual(line_05.m3, 8000)
        # Process order
        order.process_order()
        # Check that picking has been created.
        self.assertGreaterEqual(len(order.picking_ids), 1)
        # Check qty move
        total_qty_pick = 0
        lots = []
        for picking in order.picking_ids:
            move1 = picking.move_lines[0]
            move2 = picking.move_lines[1]
            move3 = picking.move_lines[2]
            move4 = picking.move_lines[3]
            move5 = picking.move_lines[4]
            for move in picking.move_lines:
                total_qty_pick += move.product_uom_qty
                lots.append(move.lot_ids)
        self.assertFalse(move1.lot_ids.exists())
        self.assertFalse(move2.lot_ids.exists())
        self.assertFalse(move3.lot_ids.exists())
        self.assertFalse(move4.lot_ids.exists())
        self.assertFalse(move5.lot_ids.exists())
        self.assertEqual(move1.product_uom_qty, 500)
        self.assertEqual(move2.product_uom_qty, 20)
        self.assertEqual(move3.product_uom_qty, 21)
        self.assertEqual(move4.product_uom_qty, 45)
        self.assertEqual(move5.product_uom_qty, 8)
        self.assertEqual(len(picking.pack_operation_ids), 5)
        # Check picking state
        self.assertEqual(picking.invoice_state, 'invoiced')
        total_qty_inv = 0
        # Check qty invoice line
        for invoice in order.invoice_ids:
            for line in invoice.invoice_line:
                total_qty_inv += line.quantity
        # LessEqual because it can not all stock pickings have been generated
        # invoice.
        self.assertLessEqual(total_qty_inv, 594)

    def test_wizard_process_with_picking_same_product_same_lots_stockable_m2(
            self):
        '''Sale order with picking and invoice (same products with same lots).
        '''
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id})
        line_01 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'lot_id': self.lot_01.id,
            'qty_per_pallet': 250,
            'pallet_qty': 2})
        line_02 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'lot_id': self.lot_01.id,
            'qty_per_pallet': 2,
            'pallet_qty': 10})
        # Call onchange method of line and check uom qty of line
        line_01.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_01.product_uom_qty, 500)
        self.assertEqual(line_01.m2, 10000)
        self.assertEqual(line_01.m3, 0)
        line_02.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_02.product_uom_qty, 20)
        self.assertEqual(line_02.m2, 400)
        self.assertEqual(line_02.m3, 0)
        # Process order
        order.process_order()
        # Check that picking has been created.
        self.assertGreaterEqual(len(order.picking_ids), 1)
        # Check qty move and lot
        total_qty_pick = 0
        lots = []
        op_lots = []
        for picking in order.picking_ids:
            move1 = picking.move_lines[0]
            move2 = picking.move_lines[1]
            for move in picking.move_lines:
                total_qty_pick += move.product_uom_qty
                lots.append(move.lot_ids)
                for op in picking.pack_operation_ids:
                    op_lots.append(op.lot_id)
        # self.assertEqual(total_qty_pick, 900)
        self.assertEqual(total_qty_pick, 520)
        self.assertEqual(move1.lot_ids, self.lot_01)
        self.assertEqual(move2.lot_ids, self.lot_01)
        self.assertEqual(move1.product_uom_qty, 500)
        self.assertEqual(move2.product_uom_qty, 20)
        self.assertEqual(len(picking.pack_operation_ids), 2)
        self.assertEqual(list(set(op_lots)).sort(), [self.lot_01].sort())
        # Check picking state
        self.assertEqual(picking.invoice_state, 'invoiced')
        total_qty_inv = 0
        # Check qty invoice line
        for invoice in order.invoice_ids:
            for line in invoice.invoice_line:
                total_qty_inv += line.quantity
        # LessEqual because it can not all stock pickings have been generated
        # invoice.
        # self.assertLessEqual(total_qty_inv, 900)
        self.assertLessEqual(total_qty_inv, 520)

    def test_wizard_process_with_picking_stockable_m3(self):
        '''Create sale order with picking and invoice.'''
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id})
        line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_02.id,
            'lot_id': self.lot_02.id,
            'qty_per_pallet': 250,
            'pallet_qty': 2})
        # Call onchange method of line and check uom qty of line
        line.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line.product_uom_qty, 500)
        self.assertEqual(line.m2, 50000)
        self.assertEqual(line.m3, 500000)
        # Process order
        order.process_order()
        # Check that picking has been created.
        self.assertGreaterEqual(len(order.picking_ids), 1)
        # Check qty move and lot
        total_qty_pick = 0
        lots = []
        op_lots = []
        for picking in order.picking_ids:
            for move in picking.move_lines:
                total_qty_pick += move.product_uom_qty
                lots.append(move.lot_ids)
                for op in picking.pack_operation_ids:
                    op_lots.append(op.lot_id)
        self.assertEqual(total_qty_pick, 500)
        self.assertEqual(move.lot_ids, self.lot_02)
        self.assertEqual(move.product_uom_qty, 500)
        self.assertEqual(len(picking.pack_operation_ids), 1)
        self.assertEqual(op_lots, [self.lot_02])
        # Check picking state
        self.assertEqual(picking.invoice_state, 'invoiced')
        total_qty_inv = 0
        # Check qty invoice line
        for invoice in order.invoice_ids:
            for line in invoice.invoice_line:
                total_qty_inv += line.quantity
        # LessEqual because it can not all stock pickings have been generated
        # invoice.
        self.assertLessEqual(total_qty_inv, 500)

    def test_wizard_process_with_picking_consumable_m3(self):
        '''Create sale order with picking and invoice.'''
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id})
        line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_07.id,
            'lot_id': self.lot_07.id,
            'qty_per_pallet': 250,
            'pallet_qty': 2})
        # Call onchange method of line and check uom qty of line
        line.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line.product_uom_qty, 500)
        self.assertEqual(line.m2, 50000)
        self.assertEqual(line.m3, 500000)
        # Process order
        order.process_order()
        # Check that picking has been created.
        self.assertGreaterEqual(len(order.picking_ids), 1)
        # Check qty move and lot
        total_qty_pick = 0
        lots = []
        op_lots = []
        for picking in order.picking_ids:
            for move in picking.move_lines:
                total_qty_pick += move.product_uom_qty
                lots.append(move.lot_ids)
                for op in picking.pack_operation_ids:
                    op_lots.append(op.lot_id)
        self.assertEqual(total_qty_pick, 500)
        self.assertEqual(move.lot_ids, self.lot_07)
        self.assertEqual(move.product_uom_qty, 500)
        self.assertEqual(len(picking.pack_operation_ids), 1)
        self.assertEqual(op_lots, [self.lot_07])
        # Check picking state
        self.assertEqual(picking.invoice_state, 'invoiced')
        total_qty_inv = 0
        # Check qty invoice line
        for invoice in order.invoice_ids:
            for line in invoice.invoice_line:
                total_qty_inv += line.quantity
        # LessEqual because it can not all stock pickings have been generated
        # invoice.
        self.assertLessEqual(total_qty_inv, 500)

    def test_wizard_process_with_picking_stockable_without_measures(self):
        '''Create sale order with picking and invoice.'''
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id})
        line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_05.id,
            'lot_id': self.lot_02.id,
            'qty_per_pallet': 10,
            'pallet_qty': 5})
        # Call onchange method of line and check uom qty of line
        line.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line.product_uom_qty, 50)
        # Check raise m2 and m3 because has not asssigned dimensional_uom_id
        self.assertRaises(
            Exception,
            line._compute_m2_m3)
        self.assertRaises(
            Exception,
            line._compute_m2_m3)
        # Assign dimensional uom
        self.product_05.write({'dimensional_uom_id': self.product_uom_mm.id})
        self.assertEqual(line.m2, 0)
        self.assertEqual(line.m3, 0)
        # Process order
        order.process_order()
        # Check that picking has been created.
        self.assertGreaterEqual(len(order.picking_ids), 1)
        # Check qty move and lot
        total_qty_pick = 0
        lots = []
        op_lots = []
        for picking in order.picking_ids:
            for move in picking.move_lines:
                total_qty_pick += move.product_uom_qty
                lots.append(move.lot_ids)
                for op in picking.pack_operation_ids:
                    op_lots.append(op.lot_id)
        self.assertEqual(total_qty_pick, 50)
        self.assertEqual(move.lot_ids, self.lot_02)
        self.assertEqual(move.product_uom_qty, 50)
        self.assertEqual(len(picking.pack_operation_ids), 1)
        self.assertEqual(op_lots, [self.lot_02])
        # Check picking state
        self.assertEqual(picking.invoice_state, 'invoiced')
        total_qty_inv = 0
        # Check qty invoice line
        for invoice in order.invoice_ids:
            for line in invoice.invoice_line:
                total_qty_inv += line.quantity
        # LessEqual because it can not all stock pickings have been generated
        # invoice.
        self.assertLessEqual(total_qty_inv, 50)

    def test_wizard_process_with_picking_consumable_without_measures(self):
        '''Create sale order with picking and invoice.'''
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id})
        line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_09.id,
            'lot_id': self.lot_09.id,
            'qty_per_pallet': 10,
            'pallet_qty': 5})
        # Call onchange method of line and check uom qty of line
        line.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line.product_uom_qty, 50)
        # Check raise m2 and m3 because has not asssigned dimensional_uom_id
        self.assertRaises(
            Exception,
            line._compute_m2_m3)
        self.assertRaises(
            Exception,
            line._compute_m2_m3)
        # Assign dimensional uom
        self.product_09.write({'dimensional_uom_id': self.product_uom_mm.id})
        self.assertEqual(line.m2, 0)
        self.assertEqual(line.m3, 0)
        # Process order
        order.process_order()
        # Check that picking has been created.
        self.assertGreaterEqual(len(order.picking_ids), 1)
        # Check qty move and lot
        total_qty_pick = 0
        lots = []
        op_lots = []
        for picking in order.picking_ids:
            for move in picking.move_lines:
                total_qty_pick += move.product_uom_qty
                lots.append(move.lot_ids)
                for op in picking.pack_operation_ids:
                    op_lots.append(op.lot_id)
        self.assertEqual(total_qty_pick, 50)
        self.assertEqual(move.lot_ids, self.lot_09)
        self.assertEqual(move.product_uom_qty, 50)
        self.assertEqual(len(picking.pack_operation_ids), 1)
        self.assertEqual(op_lots, [self.lot_09])
        # Check picking state
        self.assertEqual(picking.invoice_state, 'invoiced')
        total_qty_inv = 0
        # Check qty invoice line
        for invoice in order.invoice_ids:
            for line in invoice.invoice_line:
                total_qty_inv += line.quantity
        # LessEqual because it can not all stock pickings have been generated
        # invoice.
        self.assertLessEqual(total_qty_inv, 50)

    def test_wizard_process_with_picking_stockable_several_moves_01(self):
        '''Create sale order with picking and invoice.'''
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id})
        line_01 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'lot_id': self.lot_01.id,
            'qty_per_pallet': 100,
            'pallet_qty': 3})
        line_02 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_02.id,
            'lot_id': self.lot_02.id,
            'qty_per_pallet': 250,
            'pallet_qty': 2})
        # Call onchange method of line_01 and check uom qty of line_02
        line_01.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_01.product_uom_qty, 300)
        self.assertEqual(line_01.m2, 6000)
        self.assertEqual(line_01.m3, 0)
        line_02.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_02.product_uom_qty, 500)
        self.assertEqual(line_02.m2, 50000)
        self.assertEqual(line_02.m3, 500000)
        # Process order
        order.process_order()
        # Check that picking has been created.
        self.assertEqual(len(order.picking_ids), 1)
        # Check qty move and lot
        total_qty_pick = 0
        lots = []
        op_lots = []
        for picking in order.picking_ids:
            move1 = picking.move_lines[0]
            move2 = picking.move_lines[1]
            for move in picking.move_lines:
                self.assertEqual(move1.product_qty, 300)
                self.assertEqual(move2.product_qty, 500)
                self.assertEqual(move1.lot_ids, self.lot_01)
                self.assertEqual(move2.lot_ids, self.lot_02)
                total_qty_pick += move.product_uom_qty
                lots.append(move.lot_ids)
                for op in picking.pack_operation_ids:
                    if op.lot_id not in op_lots:
                        op_lots.append(op.lot_id)
        self.assertEqual(total_qty_pick, 800)
        self.assertEqual(move1.product_qty, 300)
        self.assertEqual(move2.product_qty, 500)
        self.assertEqual(len(picking.pack_operation_ids), 2)
        self.assertEqual(op_lots, [self.lot_01, self.lot_02])
        # Check picking state
        self.assertEqual(picking.invoice_state, 'invoiced')
        total_qty_inv = 0
        # Check qty invoice line
        for invoice in order.invoice_ids:
            for line in invoice.invoice_line:
                total_qty_inv += line.quantity
        self.assertLessEqual(total_qty_inv, 800)

    def test_wizard_process_with_picking_consumable_several_moves_01(self):
        '''Create sale order with picking and invoice.'''
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id})
        line_01 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_06.id,
            'lot_id': self.lot_06.id,
            'qty_per_pallet': 100,
            'pallet_qty': 3})
        line_02 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_07.id,
            'lot_id': self.lot_07.id,
            'qty_per_pallet': 250,
            'pallet_qty': 2})
        # Call onchange method of line_01 and check uom qty of line_02
        line_01.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_01.product_uom_qty, 300)
        self.assertEqual(line_01.m2, 6000)
        self.assertEqual(line_01.m3, 0)
        line_02.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_02.product_uom_qty, 500)
        self.assertEqual(line_02.m2, 50000)
        self.assertEqual(line_02.m3, 500000)
        # Process order
        order.process_order()
        # Check that picking has been created.
        self.assertEqual(len(order.picking_ids), 1)
        # Check qty move and lot
        total_qty_pick = 0
        lots = []
        op_lots = []
        for picking in order.picking_ids:
            move1 = picking.move_lines[0]
            move2 = picking.move_lines[1]
            for move in picking.move_lines:
                self.assertEqual(move1.product_qty, 300)
                self.assertEqual(move2.product_qty, 500)
                self.assertEqual(move1.lot_ids, self.lot_06)
                self.assertEqual(move2.lot_ids, self.lot_07)
                total_qty_pick += move.product_uom_qty
                lots.append(move.lot_ids)
                for op in picking.pack_operation_ids:
                    if op.lot_id not in op_lots:
                        op_lots.append(op.lot_id)
        self.assertEqual(total_qty_pick, 800)
        self.assertEqual(len(picking.pack_operation_ids), 2)
        self.assertEqual(op_lots, [self.lot_06, self.lot_07])
        self.assertEqual(move1.product_qty, 300)
        self.assertEqual(move2.product_qty, 500)
        # Check picking state
        self.assertEqual(picking.invoice_state, 'invoiced')
        total_qty_inv = 0
        # Check qty invoice line
        for invoice in order.invoice_ids:
            for line in invoice.invoice_line:
                total_qty_inv += line.quantity
        self.assertLessEqual(total_qty_inv, 800)

    def test_wizard_process_with_picking_stockable_several_moves_02(self):
        '''Create sale order with picking and invoice.'''
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id})
        line_01 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_01.id,
            'lot_id': self.lot_01.id,
            'qty_per_pallet': 100,
            'pallet_qty': 3})
        line_02 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_02.id,
            'lot_id': self.lot_02.id,
            'qty_per_pallet': 250,
            'pallet_qty': 2})
        line_03 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_04.id,
            'lot_id': self.lot_02.id,
            'qty_per_pallet': 10,
            'pallet_qty': 4})
        # Call onchange method of line_01 and check uom qty of line_02
        line_01.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_01.product_uom_qty, 300)
        self.assertEqual(line_01.m2, 6000)
        self.assertEqual(line_01.m3, 0)
        line_02.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_02.product_uom_qty, 500)
        self.assertEqual(line_02.m2, 50000)
        self.assertEqual(line_02.m3, 500000)
        line_03.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_03.product_uom_qty, 40)
        self.assertEqual(line_03.m2, 600)
        self.assertEqual(line_03.m3, 600)
        # Process order
        order.process_order()
        # Check that picking has been created.
        self.assertEqual(len(order.picking_ids), 1)
        # Check qty move and lot
        total_qty_pick = 0
        lots = []
        op_lots = []
        for picking in order.picking_ids:
            move1 = picking.move_lines[0]
            move2 = picking.move_lines[1]
            move3 = picking.move_lines[2]
            for move in picking.move_lines:
                self.assertEqual(move1.product_qty, 300)
                self.assertEqual(move2.product_qty, 500)
                self.assertEqual(move3.product_qty, 40)
                self.assertEqual(move1.lot_ids, self.lot_01)
                self.assertEqual(move2.lot_ids, self.lot_02)
                self.assertEqual(move3.lot_ids, self.lot_02)
                total_qty_pick += move.product_uom_qty
                lots.append(move.lot_ids)
                for op in picking.pack_operation_ids:
                    if op.lot_id not in op_lots:
                        op_lots.append(op.lot_id)
        self.assertEqual(total_qty_pick, 840)
        self.assertEqual(move1.product_qty, 300)
        self.assertEqual(move2.product_qty, 500)
        self.assertEqual(move3.product_qty, 40)
        self.assertEqual(len(picking.pack_operation_ids), 3)
        self.assertEqual(op_lots, [self.lot_01, self.lot_02])
        # Check picking state
        self.assertEqual(picking.invoice_state, 'invoiced')
        total_qty_inv = 0
        # Check qty invoice line
        for invoice in order.invoice_ids:
            for line in invoice.invoice_line:
                total_qty_inv += line.quantity
        self.assertLessEqual(total_qty_inv, 840)

    def test_wizard_process_with_picking_consumable_several_moves_02(self):
        '''Create sale order with picking and invoice.'''
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id})
        line_01 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_06.id,
            'lot_id': self.lot_06.id,
            'qty_per_pallet': 100,
            'pallet_qty': 3})
        line_02 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_07.id,
            'lot_id': self.lot_07.id,
            'qty_per_pallet': 250,
            'pallet_qty': 2})
        line_03 = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_08.id,
            'lot_id': self.lot_07.id,
            'qty_per_pallet': 10,
            'pallet_qty': 4})
        # Call onchange method of line_01 and check uom qty of line_02
        line_01.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_01.product_uom_qty, 300)
        self.assertEqual(line_01.m2, 6000)
        self.assertEqual(line_01.m3, 0)
        line_02.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_02.product_uom_qty, 500)
        self.assertEqual(line_02.m2, 50000)
        self.assertEqual(line_02.m3, 500000)
        line_03.onchange_qty_per_pallet_pallet_qty()
        self.assertEqual(line_03.product_uom_qty, 40)
        self.assertEqual(line_03.m2, 600)
        self.assertEqual(line_03.m3, 600)
        # Process order
        order.process_order()
        # Check that picking has been created.
        self.assertEqual(len(order.picking_ids), 1)
        # Check qty move and lot
        total_qty_pick = 0
        lots = []
        op_lots = []
        for picking in order.picking_ids:
            move1 = picking.move_lines[0]
            move2 = picking.move_lines[1]
            move3 = picking.move_lines[2]
            for move in picking.move_lines:
                self.assertEqual(move1.product_qty, 300)
                self.assertEqual(move2.product_qty, 500)
                self.assertEqual(move3.product_qty, 40)
                self.assertEqual(move1.lot_ids, self.lot_06)
                self.assertEqual(move2.lot_ids, self.lot_07)
                self.assertEqual(move3.lot_ids, self.lot_07)
                total_qty_pick += move.product_uom_qty
                lots.append(move.lot_ids)
                for op in picking.pack_operation_ids:
                    if op.lot_id not in op_lots:
                        op_lots.append(op.lot_id)
        self.assertEqual(total_qty_pick, 840)
        self.assertEqual(move1.product_qty, 300)
        self.assertEqual(move2.product_qty, 500)
        self.assertEqual(move3.product_qty, 40)
        self.assertEqual(len(picking.pack_operation_ids), 3)
        self.assertEqual(op_lots, [self.lot_06, self.lot_07])
        # Check picking state
        self.assertEqual(picking.invoice_state, 'invoiced')
        total_qty_inv = 0
        # Check qty invoice line
        for invoice in order.invoice_ids:
            for line in invoice.invoice_line:
                total_qty_inv += line.quantity
        self.assertLessEqual(total_qty_inv, 840)

    def test_wizard_process_service_without_picking(self):
        '''Create sale order without picking but with invoice.'''
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id})
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product_03.id,
            'lot_id': self.lot_03.id,
            'product_uom_qty': 3})
        # Process order
        order.process_order()
        # Check sale order is confirmed
        self.assertNotEqual(order.state, 'draft')
        # Check if invoice has created
        self.assertEqual(len(order.invoice_ids), 1)
        # Check qty line
        line = order.invoice_ids[0].invoice_line[0]
        self.assertEqual(line.quantity, 3)
