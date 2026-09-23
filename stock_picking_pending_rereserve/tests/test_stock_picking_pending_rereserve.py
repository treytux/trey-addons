# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
import openerp.tests.common as common


class TestStockPickingPendingRereserve(common.TransactionCase):

    def setUp(self):
        super(TestStockPickingPendingRereserve, self).setUp()
        self.warehouse = self.env.ref('stock.warehouse0')
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.stock_location_2 = self.env['stock.location'].create({
            'name': 'Stock location 2',
            'usage': 'internal',
            'active': True,
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'product',
            'default_code': 'product-01',
            'company_id': False,
            'name': 'Product 01',
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'product',
            'default_code': 'product-02',
            'company_id': False,
            'name': 'Product 02',
        })
        self.lot_01 = self.env['stock.production.lot'].create({
            'name': 'LOT-000001',
            'product_id': self.product_01.id,
        })

    def create_picking(self):
        return self.env['stock.picking'].create({
            'picking_type_id': self.env.ref('stock.picking_type_internal').id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'name': self.product_01.name,
                    'product_uom': self.product_01.uom_id.id,
                    'product_uom_qty': 2,
                    'location_id': self.warehouse.lot_stock_id.id,
                    'location_dest_id': self.stock_location_2.id,
                }),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'name': self.product_02.name,
                    'product_uom': self.product_02.uom_id.id,
                    'product_uom_qty': 3,
                    'location_id': self.warehouse.lot_stock_id.id,
                    'location_dest_id': self.stock_location_2.id,
                }),
            ],
        })

    def update_stock(self, product, location, qty, lot=None):
        wiz = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'new_quantity': qty,
            'location_id': location.id,
            'lot_id': lot and lot.id or None,
        })
        wiz.change_product_qty()

    def get_real_stock(self, product, location, lot=None):
        context = {
            'location': location.id,
        }
        if lot:
            context.update({
                'lot_id': lot.id,
            })
        qty_product_dict = product.with_context(context)._product_available()
        return qty_product_dict[product.id]['qty_available']

    def test_picking_partially_available_old_button_hidden_rereserve_pick(
            self):
        self.update_stock(
            self.product_01, self.stock_location, 10, self.lot_01)
        self.update_stock(self.product_01, self.stock_location, 20)
        real_stock_product_01 = self.get_real_stock(
            self.product_01, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock_product_01, 30)
        real_stock_product_01_lot_01 = self.get_real_stock(
            self.product_01, self.warehouse.lot_stock_id, self.lot_01)
        self.assertEquals(real_stock_product_01_lot_01, 10)
        real_stock_product_02 = self.get_real_stock(
            self.product_02, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock_product_02, 0)
        picking = self.create_picking()
        picking.action_confirm()
        picking.action_assign()
        self.assertEquals(picking.state, 'partially_available')
        move_product_01 = picking.move_lines.filtered(
            lambda m: m.product_id == self.product_01)
        self.assertEquals(move_product_01.state, 'assigned')
        self.assertEquals(len(move_product_01.reserved_quant_ids), 1)
        self.assertEquals(move_product_01.reserved_quant_ids.qty, 2)
        self.assertEquals(
            move_product_01.reserved_quant_ids.lot_id, self.lot_01)
        move_product_02 = picking.move_lines.filtered(
            lambda m: m.product_id == self.product_02)
        self.assertEquals(move_product_02.state, 'confirmed')
        wizard = self.env['assign.manual.quants'].with_context(
            active_id=move_product_01.id).create({})
        self.assertEqual(len(wizard.quants_lines), 3)
        quant_selected = wizard.quants_lines.filtered('selected')
        self.assertEqual(len(quant_selected), 1)
        self.assertEqual(quant_selected.qty, 2)
        self.assertEqual(quant_selected.lot_id, self.lot_01)
        quant_selected.selected = False
        quant_without_lot = wizard.quants_lines.filtered(
            lambda ql: not ql.lot_id)
        self.assertEqual(len(quant_without_lot), 1)
        quant_without_lot.write({
            'selected': True,
            'qty': 2,
        })
        self.assertFalse(quant_without_lot.lot_id)
        self.assertEqual(quant_without_lot.qty, 2)
        wizard.assign_quants()
        self.assertEquals(move_product_01.state, 'assigned')
        self.assertEquals(len(move_product_01.reserved_quant_ids), 1)
        self.assertEquals(move_product_01.reserved_quant_ids.qty, 2)
        self.assertFalse(move_product_01.reserved_quant_ids.lot_id)
        picking.rereserve_pick()
        self.assertEquals(picking.state, 'partially_available')
        move_product_01 = picking.move_lines.filtered(
            lambda m: m.product_id == self.product_01)
        self.assertEquals(move_product_01.state, 'assigned')
        self.assertEquals(len(move_product_01.reserved_quant_ids), 1)
        self.assertEquals(move_product_01.reserved_quant_ids.qty, 2)
        self.assertEquals(
            move_product_01.reserved_quant_ids.lot_id, self.lot_01)
        move_product_02 = picking.move_lines.filtered(
            lambda m: m.product_id == self.product_02)
        self.assertEquals(move_product_02.state, 'confirmed')

    def test_picking_partially_available_pending_rereserve_pick_entire_qty(
            self):
        self.update_stock(
            self.product_01, self.stock_location, 10, self.lot_01)
        self.update_stock(self.product_01, self.stock_location, 20)
        real_stock_product_01 = self.get_real_stock(
            self.product_01, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock_product_01, 30)
        real_stock_product_01_lot_01 = self.get_real_stock(
            self.product_01, self.warehouse.lot_stock_id, self.lot_01)
        self.assertEquals(real_stock_product_01_lot_01, 10)
        real_stock_product_02 = self.get_real_stock(
            self.product_02, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock_product_02, 0)
        picking = self.create_picking()
        picking.action_confirm()
        picking.action_assign()
        self.assertEquals(picking.state, 'partially_available')
        move_product_01 = picking.move_lines.filtered(
            lambda m: m.product_id == self.product_01)
        self.assertEquals(move_product_01.state, 'assigned')
        self.assertEquals(len(move_product_01.reserved_quant_ids), 1)
        self.assertEquals(move_product_01.reserved_quant_ids.qty, 2)
        self.assertEquals(
            move_product_01.reserved_quant_ids.lot_id, self.lot_01)
        move_product_02 = picking.move_lines.filtered(
            lambda m: m.product_id == self.product_02)
        self.assertEquals(move_product_02.state, 'confirmed')
        wizard = self.env['assign.manual.quants'].with_context(
            active_id=move_product_01.id).create({})
        self.assertEqual(len(wizard.quants_lines), 3)
        quant_selected = wizard.quants_lines.filtered('selected')
        self.assertEqual(len(quant_selected), 1)
        self.assertEqual(quant_selected.qty, 2)
        self.assertEqual(quant_selected.lot_id, self.lot_01)
        quant_selected.selected = False
        quant_without_lot = wizard.quants_lines.filtered(
            lambda ql: not ql.lot_id)
        self.assertEqual(len(quant_without_lot), 1)
        quant_without_lot.write({
            'selected': True,
            'qty': 2,
        })
        self.assertFalse(quant_without_lot.lot_id)
        self.assertEqual(quant_without_lot.qty, 2)
        wizard.assign_quants()
        self.assertEquals(move_product_01.state, 'assigned')
        self.assertEquals(len(move_product_01.reserved_quant_ids), 1)
        self.assertEquals(move_product_01.reserved_quant_ids.qty, 2)
        self.assertFalse(move_product_01.reserved_quant_ids.lot_id)
        picking.pending_rereserve_pick()
        self.assertEquals(picking.state, 'partially_available')
        move_product_01 = picking.move_lines.filtered(
            lambda m: m.product_id == self.product_01)
        self.assertEquals(move_product_01.state, 'assigned')
        self.assertEquals(len(move_product_01.reserved_quant_ids), 1)
        self.assertEquals(move_product_01.reserved_quant_ids.qty, 2)
        self.assertFalse(move_product_01.reserved_quant_ids.lot_id)
        move_product_02 = picking.move_lines.filtered(
            lambda m: m.product_id == self.product_02)
        self.assertEquals(move_product_02.state, 'confirmed')

    def test_picking_partially_available_pending_rereserve_pick_partial_qty(
            self):
        self.update_stock(
            self.product_01, self.stock_location, 10, self.lot_01)
        self.update_stock(self.product_01, self.stock_location, 20)
        real_stock_product_01 = self.get_real_stock(
            self.product_01, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock_product_01, 30)
        real_stock_product_01_lot_01 = self.get_real_stock(
            self.product_01, self.warehouse.lot_stock_id, self.lot_01)
        self.assertEquals(real_stock_product_01_lot_01, 10)
        real_stock_product_02 = self.get_real_stock(
            self.product_02, self.warehouse.lot_stock_id)
        self.assertEquals(real_stock_product_02, 0)
        picking = self.create_picking()
        picking.action_confirm()
        picking.action_assign()
        self.assertEquals(picking.state, 'partially_available')
        move_product_01 = picking.move_lines.filtered(
            lambda m: m.product_id == self.product_01)
        self.assertEquals(move_product_01.state, 'assigned')
        self.assertEquals(len(move_product_01.reserved_quant_ids), 1)
        self.assertEquals(move_product_01.reserved_quant_ids.qty, 2)
        self.assertEquals(
            move_product_01.reserved_quant_ids.lot_id, self.lot_01)
        move_product_02 = picking.move_lines.filtered(
            lambda m: m.product_id == self.product_02)
        self.assertEquals(move_product_02.state, 'confirmed')
        wizard = self.env['assign.manual.quants'].with_context(
            active_id=move_product_01.id).create({})
        self.assertEqual(len(wizard.quants_lines), 3)
        quant_selected = wizard.quants_lines.filtered('selected')
        self.assertEqual(len(quant_selected), 1)
        self.assertEqual(quant_selected.qty, 2)
        self.assertEqual(quant_selected.lot_id, self.lot_01)
        quant_selected.selected = False
        quant_without_lot = wizard.quants_lines.filtered(
            lambda ql: not ql.lot_id)
        self.assertEqual(len(quant_without_lot), 1)
        quant_without_lot.write({
            'selected': True,
            'qty': 1,
        })
        self.assertFalse(quant_without_lot.lot_id)
        self.assertEqual(quant_without_lot.qty, 1)
        wizard.assign_quants()
        self.assertEquals(move_product_01.state, 'confirmed')
        self.assertEquals(len(move_product_01.reserved_quant_ids), 1)
        self.assertEquals(move_product_01.reserved_quant_ids.qty, 1)
        self.assertFalse(move_product_01.reserved_quant_ids.lot_id)
        picking.pending_rereserve_pick()
        self.assertEquals(picking.state, 'partially_available')
        move_product_01 = picking.move_lines.filtered(
            lambda m: m.product_id == self.product_01)
        self.assertEquals(move_product_01.state, 'assigned')
        self.assertEquals(len(move_product_01.reserved_quant_ids), 1)
        self.assertEquals(move_product_01.reserved_quant_ids.qty, 2)
        self.assertEquals(
            move_product_01.reserved_quant_ids.lot_id, self.lot_01)
        move_product_02 = picking.move_lines.filtered(
            lambda m: m.product_id == self.product_02)
        self.assertEquals(move_product_02.state, 'confirmed')
