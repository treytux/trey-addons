# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests.common import TransactionCase


class MrpductionCase(TransactionCase):
    '''Test mrp wizard.'''

    def setUp(self):
        super(MrpductionCase, self).setUp()
        product_obj = self.env['product.product']
        move_obj = self.env['stock.move']
        stock_loc_id = self.ref('stock.stock_location_stock')
        inv_loss_loc_id = self.ref('stock.location_inventory')
        mrp_route = self.env.ref('mrp.route_warehouse0_manufacture')
        self.product_mp1 = product_obj.create({'name': 'Product mp1'})
        move = move_obj.create({
            'name': self.product_mp1.name,
            'product_id': self.product_mp1.id,
            'product_uom_qty': 1000,
            'product_uom': self.product_mp1.uom_id.id,
            'location_id': inv_loss_loc_id,
            'location_dest_id': stock_loc_id})
        move.action_done()
        self.product_mp2 = product_obj.create({'name': 'Product mp2'})
        move = move_obj.create({
            'name': self.product_mp2.name,
            'product_id': self.product_mp2.id,
            'product_uom_qty': 1000,
            'product_uom': self.product_mp2.uom_id.id,
            'location_id': inv_loss_loc_id,
            'location_dest_id': stock_loc_id})
        move.action_done()
        self.product_fab1 = product_obj.create({
            'name': 'Product fab 1',
            'route_ids': [(6, 0, [mrp_route.id])]})
        self.bom1 = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_fab1.product_tmpl_id.id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {'product_id': self.product_mp1.id, 'product_qty': 10}),
                (0, 0, {
                    'product_id': self.product_mp2.id, 'product_qty': 20})]})
        self.product_fab2 = product_obj.create({
            'name': 'Product fab 2',
            'route_ids': [(6, 0, [mrp_route.id])]})
        self.bom2 = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_fab2.product_tmpl_id.id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {'product_id': self.product_fab2.id, 'product_qty': 2}),
                (0, 0, {'product_id': self.product_mp1.id, 'product_qty': 10}),
                (0, 0, {
                    'product_id': self.product_mp2.id, 'product_qty': 20})]})

    def get_lot_name(self, name, count):
        return '%s-%s' % (name, str(count).zfill(6))

    def test_mrp_production_total_without_lot(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 5,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        self.assertEqual(len(mrp.bom_id.bom_line_ids), 2)
        self.assertEqual(mrp.bom_id.bom_line_ids[0].product_qty, 10)
        self.assertEqual(mrp.bom_id.bom_line_ids[1].product_qty, 20)
        mrp.action_confirm()
        self.assertEqual(len(mrp.move_lines), 2)
        self.assertEqual(mrp.state, 'confirmed')
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': mrp.product_qty})
        lines = wiz.on_change_qty(mrp.product_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 50)
        self.assertEqual(wiz.consume_lines[1].product_qty, 100)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 50)
        self.assertEqual(mrp.move_lines2[1].product_qty, 100)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 1)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 5)
        self.assertEqual(mrp.move_created_ids2[0].state, 'done')
        self.assertFalse(mrp.move_created_ids2[0].restrict_lot_id, None)

    def test_mrp_production_total_with_production_lot(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 5,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        lot = self.env['stock.production.lot'].create({
            'name': 'test',
            'product_id': self.product_fab1.id})
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': mrp.product_qty,
                'lot_id': lot.id})
        lines = wiz.on_change_qty(mrp.product_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 50)
        self.assertEqual(wiz.consume_lines[1].product_qty, 100)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 50)
        self.assertEqual(mrp.move_lines2[1].product_qty, 100)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 5)
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.product_qty, 1)
            self.assertEqual(move.state, 'done')
            self.assertEqual(
                move.restrict_lot_id.name, self.get_lot_name('test', count))

    def test_mrp_production_partial_without_lot(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 5,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        partial_qty = 3
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': partial_qty})
        lines = wiz.on_change_qty(partial_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 30)
        self.assertEqual(wiz.consume_lines[1].product_qty, 60)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 2)
        self.assertEqual(mrp.move_lines[0].product_qty, 20)
        self.assertEqual(mrp.move_lines[1].product_qty, 40)
        self.assertFalse(mrp.move_lines[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 30)
        self.assertEqual(mrp.move_lines2[1].product_qty, 60)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 1)
        self.assertEqual(mrp.move_created_ids[0].product_qty, 2)
        self.assertEqual(mrp.move_created_ids[0].state, 'assigned')
        self.assertFalse(mrp.move_created_ids[0].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids2), 1)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 3)
        self.assertEqual(mrp.move_created_ids2[0].state, 'done')
        self.assertFalse(mrp.move_created_ids2[0].restrict_lot_id, None)
        rest_qty = 2
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': rest_qty})
        lines = wiz.on_change_qty(rest_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 20)
        self.assertEqual(wiz.consume_lines[1].product_qty, 40)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 4)
        self.assertEqual(mrp.move_lines2[0].product_qty, 30)
        self.assertEqual(mrp.move_lines2[1].product_qty, 60)
        self.assertEqual(mrp.move_lines2[2].product_qty, 20)
        self.assertEqual(mrp.move_lines2[3].product_qty, 40)
        for move in mrp.move_lines2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 2)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 3)
        self.assertEqual(mrp.move_created_ids2[1].product_qty, 2)
        for move in mrp.move_created_ids2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)

    def test_mrp_production_partial_with_production_lot(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 5,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        lot = self.env['stock.production.lot'].create({
            'name': 'test',
            'product_id': self.product_fab1.id})
        partial_qty = 3
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': partial_qty,
                'lot_id': lot.id})
        lines = wiz.on_change_qty(partial_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 30)
        self.assertEqual(wiz.consume_lines[1].product_qty, 60)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 2)
        self.assertEqual(mrp.move_lines[0].product_qty, 20)
        self.assertEqual(mrp.move_lines[1].product_qty, 40)
        self.assertFalse(mrp.move_lines[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 30)
        self.assertEqual(mrp.move_lines2[1].product_qty, 60)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 1)
        self.assertEqual(len(mrp.move_created_ids2), 3)
        self.assertEqual(mrp.move_created_ids.product_qty, 2)
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.product_qty, 1)
            self.assertEqual(move.state, 'done')
            self.assertEqual(
                move.restrict_lot_id.name, self.get_lot_name('test', count))
        rest_qty = 2
        lot2 = self.env['stock.production.lot'].create({
            'name': 'test2',
            'product_id': self.product_fab1.id})
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': rest_qty,
                'lot_id': lot2.id})
        lines = wiz.on_change_qty(rest_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 20)
        self.assertEqual(wiz.consume_lines[1].product_qty, 40)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 4)
        self.assertEqual(mrp.move_lines2[0].product_qty, 30)
        self.assertEqual(mrp.move_lines2[1].product_qty, 60)
        self.assertEqual(mrp.move_lines2[2].product_qty, 20)
        self.assertEqual(mrp.move_lines2[3].product_qty, 40)
        for move in mrp.move_lines2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 5)
        for move in mrp.move_created_ids2:
            self.assertEqual(move.product_qty, 1)
        all_lot_names = [
            self.get_lot_name('test', 1), self.get_lot_name('test', 2),
            self.get_lot_name('test', 3), self.get_lot_name('test2', 1),
            self.get_lot_name('test2', 2)]
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.product_qty, 1)
            self.assertEqual(move.state, 'done')
            self.assertIn(
                move.restrict_lot_id.name, all_lot_names, 'Lot errors')
            all_lot_names.remove(move.restrict_lot_id.name)

    def test_mrp_production_total_decimal_without_lot(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 5.12,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': mrp.product_qty})
        lines = wiz.on_change_qty(mrp.product_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 51.2)
        self.assertEqual(wiz.consume_lines[1].product_qty, 102.4)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 51.2)
        self.assertEqual(mrp.move_lines2[1].product_qty, 102.4)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 1)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 5.12)
        self.assertEqual(mrp.move_created_ids2[0].state, 'done')
        self.assertFalse(mrp.move_created_ids2[0].restrict_lot_id, None)

    def test_mrp_production_total_decimal_with_production_lot(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 5.12,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        lot = self.env['stock.production.lot'].create({
            'name': 'test',
            'product_id': self.product_fab1.id})
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': mrp.product_qty,
                'lot_id': lot.id})
        lines = wiz.on_change_qty(mrp.product_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 51.20)
        self.assertEqual(wiz.consume_lines[1].product_qty, 102.4)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 51.20)
        self.assertEqual(mrp.move_lines2[1].product_qty, 102.4)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 6)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[1].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[2].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[3].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[4].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[5].product_qty, 0.12)
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.state, 'done')
            self.assertEqual(
                move.restrict_lot_id.name, self.get_lot_name('test', count))

    def test_mrp_production_partial_decimal_without_lot(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 5.12,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        partial_qty = 3
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': partial_qty})
        lines = wiz.on_change_qty(partial_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 30)
        self.assertEqual(wiz.consume_lines[1].product_qty, 60)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 2)
        self.assertEqual(mrp.move_lines[0].product_qty, 21.2)
        self.assertEqual(mrp.move_lines[1].product_qty, 42.4)
        self.assertFalse(mrp.move_lines[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 30)
        self.assertEqual(mrp.move_lines2[1].product_qty, 60)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 1)
        self.assertEqual(mrp.move_created_ids[0].product_qty, 2.12)
        self.assertEqual(mrp.move_created_ids[0].state, 'assigned')
        self.assertFalse(mrp.move_created_ids[0].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids2), 1)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 3)
        self.assertEqual(mrp.move_created_ids2[0].state, 'done')
        self.assertFalse(mrp.move_created_ids2[0].restrict_lot_id, None)
        rest_qty = 2.12
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': rest_qty})
        lines = wiz.on_change_qty(rest_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 21.2)
        self.assertEqual(wiz.consume_lines[1].product_qty, 42.4)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 4)
        self.assertEqual(mrp.move_lines2[0].product_qty, 30)
        self.assertEqual(mrp.move_lines2[1].product_qty, 60)
        self.assertEqual(mrp.move_lines2[2].product_qty, 21.2)
        self.assertEqual(mrp.move_lines2[3].product_qty, 42.4)
        for move in mrp.move_lines2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 2)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 3)
        self.assertEqual(mrp.move_created_ids2[1].product_qty, 2.12)
        for move in mrp.move_created_ids2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)

    def test_mrp_production_partial_decimal_with_production_lot(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 5.12,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        lot = self.env['stock.production.lot'].create({
            'name': 'test',
            'product_id': self.product_fab1.id})
        partial_qty = 3
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': partial_qty,
                'lot_id': lot.id})
        lines = wiz.on_change_qty(partial_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 30)
        self.assertEqual(wiz.consume_lines[1].product_qty, 60)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 2)
        self.assertEqual(mrp.move_lines[0].product_qty, 21.2)
        self.assertEqual(mrp.move_lines[1].product_qty, 42.4)
        self.assertFalse(mrp.move_lines[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 30)
        self.assertEqual(mrp.move_lines2[1].product_qty, 60)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 1)
        self.assertEqual(len(mrp.move_created_ids2), 3)
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.product_qty, 1)
            self.assertEqual(move.state, 'done')
            self.assertEqual(
                move.restrict_lot_id.name, self.get_lot_name('test', count))
        rest_qty = 2.12
        lot2 = self.env['stock.production.lot'].create({
            'name': 'test2',
            'product_id': self.product_fab1.id})
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': rest_qty,
                'lot_id': lot2.id})
        lines = wiz.on_change_qty(rest_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 21.2)
        self.assertEqual(wiz.consume_lines[1].product_qty, 42.4)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 4)
        self.assertEqual(mrp.move_lines2[0].product_qty, 30)
        self.assertEqual(mrp.move_lines2[1].product_qty, 60)
        self.assertEqual(mrp.move_lines2[2].product_qty, 21.2)
        self.assertEqual(mrp.move_lines2[3].product_qty, 42.4)
        for move in mrp.move_lines2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 6)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[1].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[2].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[3].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[4].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[5].product_qty, 0.12)
        all_lot_names = [
            self.get_lot_name('test', 1), self.get_lot_name('test', 2),
            self.get_lot_name('test', 3), self.get_lot_name('test2', 1),
            self.get_lot_name('test2', 2), self.get_lot_name('test2', 3)]
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.state, 'done')
            self.assertIn(
                move.restrict_lot_id.name, all_lot_names, 'Lot errors')
            all_lot_names.remove(move.restrict_lot_id.name)

    def test_mrp_production_of_production_total_without_lot(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab2.id,
            'product_qty': 5,
            'product_uom': self.product_fab2.uom_id.id,
            'bom_id': self.bom2.id})
        mrp.action_confirm()
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': mrp.product_qty})
        lines = wiz.on_change_qty(mrp.product_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 3)
        self.assertEqual(wiz.consume_lines[0].product_qty, 10)
        self.assertEqual(wiz.consume_lines[1].product_qty, 50)
        self.assertEqual(wiz.consume_lines[2].product_qty, 100)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        self.assertFalse(wiz.consume_lines[2].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 3)
        self.assertEqual(mrp.move_lines2[0].product_qty, 10)
        self.assertEqual(mrp.move_lines2[1].product_qty, 50)
        self.assertEqual(mrp.move_lines2[2].product_qty, 100)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[2].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 1)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 5)
        self.assertEqual(mrp.move_created_ids2[0].state, 'done')
        self.assertFalse(mrp.move_created_ids2[0].restrict_lot_id, None)

    def test_mrp_production_of_production_total_with_production_lot(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab2.id,
            'product_qty': 5,
            'product_uom': self.product_fab2.uom_id.id,
            'bom_id': self.bom2.id})
        mrp.action_confirm()
        lot = self.env['stock.production.lot'].create({
            'name': 'test',
            'product_id': self.product_fab2.id})
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': mrp.product_qty,
                'lot_id': lot.id})
        lines = wiz.on_change_qty(mrp.product_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 3)
        self.assertEqual(wiz.consume_lines[0].product_qty, 10)
        self.assertEqual(wiz.consume_lines[1].product_qty, 50)
        self.assertEqual(wiz.consume_lines[2].product_qty, 100)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        self.assertFalse(wiz.consume_lines[2].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 3)
        self.assertEqual(mrp.move_lines2[0].product_qty, 10)
        self.assertEqual(mrp.move_lines2[1].product_qty, 50)
        self.assertEqual(mrp.move_lines2[2].product_qty, 100)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[2].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 5)
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.product_qty, 1)
            self.assertEqual(move.state, 'done')
            self.assertEqual(
                move.restrict_lot_id.name, self.get_lot_name('test', count))

    def test_mrp_production_of_production_partial_without_lot(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab2.id,
            'product_qty': 5,
            'product_uom': self.product_fab2.uom_id.id,
            'bom_id': self.bom2.id})
        mrp.action_confirm()
        partial_qty = 3
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': partial_qty})
        lines = wiz.on_change_qty(partial_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 3)
        self.assertEqual(wiz.consume_lines[0].product_qty, 6)
        self.assertEqual(wiz.consume_lines[1].product_qty, 30)
        self.assertEqual(wiz.consume_lines[2].product_qty, 60)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 3)
        self.assertEqual(mrp.move_lines[0].product_qty, 4)
        self.assertEqual(mrp.move_lines[1].product_qty, 20)
        self.assertEqual(mrp.move_lines[2].product_qty, 40)
        self.assertFalse(mrp.move_lines[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines[1].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines[2].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_lines2), 3)
        self.assertEqual(mrp.move_lines2[0].product_qty, 6)
        self.assertEqual(mrp.move_lines2[1].product_qty, 30)
        self.assertEqual(mrp.move_lines2[2].product_qty, 60)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[2].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 1)
        self.assertEqual(mrp.move_created_ids[0].product_qty, 2)
        self.assertEqual(mrp.move_created_ids[0].state, 'assigned')
        self.assertFalse(mrp.move_created_ids[0].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids2), 1)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 3)
        self.assertEqual(mrp.move_created_ids2[0].state, 'done')
        self.assertFalse(mrp.move_created_ids2[0].restrict_lot_id, None)
        rest_qty = 2
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': rest_qty})
        lines = wiz.on_change_qty(rest_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 3)
        self.assertEqual(wiz.consume_lines[0].product_qty, 4)
        self.assertEqual(wiz.consume_lines[1].product_qty, 20)
        self.assertEqual(wiz.consume_lines[2].product_qty, 40)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        self.assertFalse(wiz.consume_lines[2].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 6)
        self.assertEqual(mrp.move_lines2[0].product_qty, 6)
        self.assertEqual(mrp.move_lines2[1].product_qty, 30)
        self.assertEqual(mrp.move_lines2[2].product_qty, 60)
        self.assertEqual(mrp.move_lines2[3].product_qty, 4)
        self.assertEqual(mrp.move_lines2[4].product_qty, 20)
        self.assertEqual(mrp.move_lines2[5].product_qty, 40)
        for move in mrp.move_lines2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 2)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 3)
        self.assertEqual(mrp.move_created_ids2[1].product_qty, 2)
        for move in mrp.move_created_ids2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)

    def test_mrp_production_of_production_partial_with_production_lot(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab2.id,
            'product_qty': 5,
            'product_uom': self.product_fab2.uom_id.id,
            'bom_id': self.bom2.id})
        mrp.action_confirm()
        lot = self.env['stock.production.lot'].create({
            'name': 'test',
            'product_id': self.product_fab2.id})
        partial_qty = 3
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': partial_qty,
                'lot_id': lot.id})
        lines = wiz.on_change_qty(partial_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 3)
        self.assertEqual(wiz.consume_lines[0].product_qty, 6)
        self.assertEqual(wiz.consume_lines[1].product_qty, 30)
        self.assertEqual(wiz.consume_lines[2].product_qty, 60)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        self.assertFalse(wiz.consume_lines[2].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 3)
        self.assertEqual(mrp.move_lines[0].product_qty, 4)
        self.assertEqual(mrp.move_lines[1].product_qty, 20)
        self.assertEqual(mrp.move_lines[2].product_qty, 40)
        self.assertFalse(mrp.move_lines[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines[1].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines[2].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_lines2), 3)
        self.assertEqual(mrp.move_lines2[0].product_qty, 6)
        self.assertEqual(mrp.move_lines2[1].product_qty, 30)
        self.assertEqual(mrp.move_lines2[2].product_qty, 60)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[2].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 1)
        self.assertEqual(len(mrp.move_created_ids2), 3)
        self.assertEqual(mrp.move_created_ids.product_qty, 2)
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.product_qty, 1)
            self.assertEqual(move.state, 'done')
            self.assertEqual(
                move.restrict_lot_id.name, self.get_lot_name('test', count))
        rest_qty = 2
        lot2 = self.env['stock.production.lot'].create({
            'name': 'test2',
            'product_id': self.product_fab2.id})
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': rest_qty,
                'lot_id': lot2.id})
        lines = wiz.on_change_qty(rest_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 3)
        self.assertEqual(wiz.consume_lines[0].product_qty, 4)
        self.assertEqual(wiz.consume_lines[1].product_qty, 20)
        self.assertEqual(wiz.consume_lines[2].product_qty, 40)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        self.assertFalse(wiz.consume_lines[2].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 6)
        self.assertEqual(mrp.move_lines2[0].product_qty, 6)
        self.assertEqual(mrp.move_lines2[1].product_qty, 30)
        self.assertEqual(mrp.move_lines2[2].product_qty, 60)
        self.assertEqual(mrp.move_lines2[3].product_qty, 4)
        self.assertEqual(mrp.move_lines2[4].product_qty, 20)
        self.assertEqual(mrp.move_lines2[5].product_qty, 40)
        for move in mrp.move_lines2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 5)
        for move in mrp.move_created_ids2:
            self.assertEqual(move.product_qty, 1)
        all_lot_names = [
            self.get_lot_name('test', 1), self.get_lot_name('test', 2),
            self.get_lot_name('test', 3), self.get_lot_name('test2', 1),
            self.get_lot_name('test2', 2)]
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.product_qty, 1)
            self.assertEqual(move.state, 'done')
            self.assertIn(
                move.restrict_lot_id.name, all_lot_names, 'Lot errors')
            all_lot_names.remove(move.restrict_lot_id.name)

    def test_mrp_production_of_production_total_decimal_without_lot(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab2.id,
            'product_qty': 5.12,
            'product_uom': self.product_fab2.uom_id.id,
            'bom_id': self.bom2.id})
        mrp.action_confirm()
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': mrp.product_qty})
        lines = wiz.on_change_qty(mrp.product_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 3)
        self.assertEqual(wiz.consume_lines[0].product_qty, 10.24)
        self.assertEqual(wiz.consume_lines[1].product_qty, 51.2)
        self.assertEqual(wiz.consume_lines[2].product_qty, 102.4)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        self.assertFalse(wiz.consume_lines[2].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 3)
        self.assertEqual(mrp.move_lines2[0].product_qty, 10.24)
        self.assertEqual(mrp.move_lines2[1].product_qty, 51.2)
        self.assertEqual(mrp.move_lines2[2].product_qty, 102.4)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[2].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 1)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 5.12)
        self.assertEqual(mrp.move_created_ids2[0].state, 'done')
        self.assertFalse(mrp.move_created_ids2[0].restrict_lot_id, None)

    def test_mrp_production_of_production_total_decimal_with_production_lot(
            self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab2.id,
            'product_qty': 5.12,
            'product_uom': self.product_fab2.uom_id.id,
            'bom_id': self.bom2.id})
        mrp.action_confirm()
        lot = self.env['stock.production.lot'].create({
            'name': 'test',
            'product_id': self.product_fab2.id})
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': mrp.product_qty,
                'lot_id': lot.id})
        lines = wiz.on_change_qty(mrp.product_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 3)
        self.assertEqual(wiz.consume_lines[0].product_qty, 10.24)
        self.assertEqual(wiz.consume_lines[1].product_qty, 51.20)
        self.assertEqual(wiz.consume_lines[2].product_qty, 102.4)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        self.assertFalse(wiz.consume_lines[2].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 3)
        self.assertEqual(mrp.move_lines2[0].product_qty, 10.24)
        self.assertEqual(mrp.move_lines2[1].product_qty, 51.20)
        self.assertEqual(mrp.move_lines2[2].product_qty, 102.4)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[2].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 6)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[1].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[2].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[3].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[4].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[5].product_qty, 0.12)
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.state, 'done')
            self.assertEqual(
                move.restrict_lot_id.name, self.get_lot_name('test', count))

    def test_mrp_production_of_production_partial_decimal_without_lot(
            self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab2.id,
            'product_qty': 5.12,
            'product_uom': self.product_fab2.uom_id.id,
            'bom_id': self.bom2.id})
        mrp.action_confirm()
        partial_qty = 3
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': partial_qty})
        lines = wiz.on_change_qty(partial_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 3)
        self.assertEqual(wiz.consume_lines[0].product_qty, 6)
        self.assertEqual(wiz.consume_lines[1].product_qty, 30)
        self.assertEqual(wiz.consume_lines[2].product_qty, 60)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        self.assertFalse(wiz.consume_lines[2].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 3)
        self.assertEqual(mrp.move_lines[0].product_qty, 4.24)
        self.assertEqual(mrp.move_lines[1].product_qty, 21.2)
        self.assertEqual(mrp.move_lines[2].product_qty, 42.4)
        self.assertFalse(mrp.move_lines[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines[1].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines[2].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_lines2), 3)
        self.assertEqual(mrp.move_lines2[0].product_qty, 6)
        self.assertEqual(mrp.move_lines2[1].product_qty, 30)
        self.assertEqual(mrp.move_lines2[2].product_qty, 60)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[2].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 1)
        self.assertEqual(mrp.move_created_ids[0].product_qty, 2.12)
        self.assertEqual(mrp.move_created_ids[0].state, 'assigned')
        self.assertFalse(mrp.move_created_ids[0].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids2), 1)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 3)
        self.assertEqual(mrp.move_created_ids2[0].state, 'done')
        self.assertFalse(mrp.move_created_ids2[0].restrict_lot_id, None)
        rest_qty = 2.12
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': rest_qty})
        lines = wiz.on_change_qty(rest_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 3)
        self.assertEqual(wiz.consume_lines[0].product_qty, 4.24)
        self.assertEqual(wiz.consume_lines[1].product_qty, 21.2)
        self.assertEqual(wiz.consume_lines[2].product_qty, 42.4)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        self.assertFalse(wiz.consume_lines[2].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 6)
        self.assertEqual(mrp.move_lines2[0].product_qty, 6)
        self.assertEqual(mrp.move_lines2[1].product_qty, 30)
        self.assertEqual(mrp.move_lines2[2].product_qty, 60)
        self.assertEqual(mrp.move_lines2[3].product_qty, 4.24)
        self.assertEqual(mrp.move_lines2[4].product_qty, 21.2)
        self.assertEqual(mrp.move_lines2[5].product_qty, 42.4)
        for move in mrp.move_lines2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 2)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 3)
        self.assertEqual(mrp.move_created_ids2[1].product_qty, 2.12)
        for move in mrp.move_created_ids2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)

    def test_mrp_production_of_production_partial_decimal_with_production_lot(
            self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab2.id,
            'product_qty': 5.12,
            'product_uom': self.product_fab2.uom_id.id,
            'bom_id': self.bom2.id})
        mrp.action_confirm()
        lot = self.env['stock.production.lot'].create({
            'name': 'test',
            'product_id': self.product_fab2.id})
        partial_qty = 3
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': partial_qty,
                'lot_id': lot.id})
        lines = wiz.on_change_qty(partial_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 3)
        self.assertEqual(wiz.consume_lines[0].product_qty, 6)
        self.assertEqual(wiz.consume_lines[1].product_qty, 30)
        self.assertEqual(wiz.consume_lines[2].product_qty, 60)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        self.assertFalse(wiz.consume_lines[2].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 3)
        self.assertEqual(mrp.move_lines[0].product_qty, 4.24)
        self.assertEqual(mrp.move_lines[1].product_qty, 21.2)
        self.assertEqual(mrp.move_lines[2].product_qty, 42.4)
        self.assertFalse(mrp.move_lines[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines[1].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines[2].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_lines2), 3)
        self.assertEqual(mrp.move_lines2[0].product_qty, 6)
        self.assertEqual(mrp.move_lines2[1].product_qty, 30)
        self.assertEqual(mrp.move_lines2[2].product_qty, 60)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[2].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 1)
        self.assertEqual(len(mrp.move_created_ids2), 3)
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.product_qty, 1)
            self.assertEqual(move.state, 'done')
            self.assertEqual(
                move.restrict_lot_id.name, self.get_lot_name('test', count))
        rest_qty = 2.12
        lot2 = self.env['stock.production.lot'].create({
            'name': 'test2',
            'product_id': self.product_fab2.id})
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': rest_qty,
                'lot_id': lot2.id})
        lines = wiz.on_change_qty(rest_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 3)
        self.assertEqual(wiz.consume_lines[0].product_qty, 4.24)
        self.assertEqual(wiz.consume_lines[1].product_qty, 21.2)
        self.assertEqual(wiz.consume_lines[2].product_qty, 42.4)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        self.assertFalse(wiz.consume_lines[2].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 6)
        self.assertEqual(mrp.move_lines2[0].product_qty, 6)
        self.assertEqual(mrp.move_lines2[1].product_qty, 30)
        self.assertEqual(mrp.move_lines2[2].product_qty, 60)
        self.assertEqual(mrp.move_lines2[3].product_qty, 4.24)
        self.assertEqual(mrp.move_lines2[4].product_qty, 21.2)
        self.assertEqual(mrp.move_lines2[5].product_qty, 42.4)
        for move in mrp.move_lines2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 6)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[1].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[2].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[3].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[4].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[5].product_qty, 0.12)
        all_lot_names = [
            self.get_lot_name('test', 1), self.get_lot_name('test', 2),
            self.get_lot_name('test', 3), self.get_lot_name('test2', 1),
            self.get_lot_name('test2', 2), self.get_lot_name('test2', 3)]
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.state, 'done')
            self.assertIn(
                move.restrict_lot_id.name, all_lot_names, 'Lot errors')
            all_lot_names.remove(move.restrict_lot_id.name)

    def test_mrp_production_total_without_lot_mp_lots(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 5,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': mrp.product_qty})
        lines = wiz.on_change_qty(mrp.product_qty, [])
        wiz.write(lines['value'])
        lot_mp1 = self.env['stock.production.lot'].create({
            'product_id': self.product_mp1.id})
        lot_mp2 = self.env['stock.production.lot'].create({
            'product_id': self.product_mp2.id})
        wiz.consume_lines[0].lot_id = lot_mp1.id
        wiz.consume_lines[1].lot_id = lot_mp2.id
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 50)
        self.assertEqual(wiz.consume_lines[1].product_qty, 100)
        self.assertEqual(wiz.consume_lines[0].lot_id.id, lot_mp1.id)
        self.assertEqual(wiz.consume_lines[1].lot_id.id, lot_mp2.id)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 50)
        self.assertEqual(mrp.move_lines2[1].product_qty, 100)
        self.assertEqual(mrp.move_lines2[0].restrict_lot_id.id, lot_mp1.id)
        self.assertEqual(mrp.move_lines2[1].restrict_lot_id.id, lot_mp2.id)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 1)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 5)
        self.assertEqual(mrp.move_created_ids2[0].state, 'done')
        self.assertFalse(mrp.move_created_ids2[0].restrict_lot_id, None)

    def test_mrp_production_total_with_production_lot_mp_lots(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 5,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        lot = self.env['stock.production.lot'].create({
            'name': 'test',
            'product_id': self.product_fab1.id})
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': mrp.product_qty,
                'lot_id': lot.id})
        lines = wiz.on_change_qty(mrp.product_qty, [])
        wiz.write(lines['value'])
        lot_mp1 = self.env['stock.production.lot'].create({
            'product_id': self.product_mp1.id})
        lot_mp2 = self.env['stock.production.lot'].create({
            'product_id': self.product_mp2.id})
        wiz.consume_lines[0].lot_id = lot_mp1.id
        wiz.consume_lines[1].lot_id = lot_mp2.id
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 50)
        self.assertEqual(wiz.consume_lines[1].product_qty, 100)
        self.assertEqual(wiz.consume_lines[0].lot_id.id, lot_mp1.id)
        self.assertEqual(wiz.consume_lines[1].lot_id.id, lot_mp2.id)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 50)
        self.assertEqual(mrp.move_lines2[1].product_qty, 100)
        self.assertEqual(mrp.move_lines2[0].restrict_lot_id.id, lot_mp1.id)
        self.assertEqual(mrp.move_lines2[1].restrict_lot_id.id, lot_mp2.id)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 5)
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.product_qty, 1)
            self.assertEqual(move.state, 'done')
            self.assertEqual(
                move.restrict_lot_id.name, self.get_lot_name('test', count))

    def test_mrp_production_partial_without_lot_mp_lots(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 5,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        partial_qty = 3
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': partial_qty})
        lines = wiz.on_change_qty(partial_qty, [])
        wiz.write(lines['value'])
        lot_mp1 = self.env['stock.production.lot'].create({
            'product_id': self.product_mp1.id})
        lot_mp2 = self.env['stock.production.lot'].create({
            'product_id': self.product_mp2.id})
        wiz.consume_lines[0].lot_id = lot_mp1.id
        wiz.consume_lines[1].lot_id = lot_mp2.id
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 30)
        self.assertEqual(wiz.consume_lines[1].product_qty, 60)
        self.assertEqual(wiz.consume_lines[0].lot_id, lot_mp1)
        self.assertEqual(wiz.consume_lines[1].lot_id, lot_mp2)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 2)
        self.assertEqual(mrp.move_lines[0].product_qty, 20)
        self.assertEqual(mrp.move_lines[1].product_qty, 40)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 30)
        self.assertEqual(mrp.move_lines2[1].product_qty, 60)
        self.assertEqual(mrp.move_lines2[0].restrict_lot_id, lot_mp1)
        self.assertEqual(mrp.move_lines2[1].restrict_lot_id, lot_mp2)
        self.assertEqual(len(mrp.move_created_ids), 1)
        self.assertEqual(mrp.move_created_ids[0].product_qty, 2)
        self.assertEqual(mrp.move_created_ids[0].state, 'assigned')
        self.assertFalse(mrp.move_created_ids[0].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids2), 1)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 3)
        self.assertEqual(mrp.move_created_ids2[0].state, 'done')
        self.assertFalse(mrp.move_created_ids2[0].restrict_lot_id, None)
        rest_qty = 2
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': rest_qty})
        lines = wiz.on_change_qty(rest_qty, [])
        wiz.write(lines['value'])
        lot_mp3 = self.env['stock.production.lot'].create({
            'product_id': self.product_mp1.id})
        lot_mp4 = self.env['stock.production.lot'].create({
            'product_id': self.product_mp2.id})
        wiz.consume_lines[0].lot_id = lot_mp3.id
        wiz.consume_lines[1].lot_id = lot_mp4.id
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 20)
        self.assertEqual(wiz.consume_lines[1].product_qty, 40)
        self.assertEqual(wiz.consume_lines[0].lot_id, lot_mp3)
        self.assertEqual(wiz.consume_lines[1].lot_id, lot_mp4)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 4)
        self.assertEqual(mrp.move_lines2[0].product_qty, 30)
        self.assertEqual(mrp.move_lines2[1].product_qty, 60)
        self.assertEqual(mrp.move_lines2[2].product_qty, 20)
        self.assertEqual(mrp.move_lines2[3].product_qty, 40)
        self.assertEqual(mrp.move_lines2[0].restrict_lot_id, lot_mp1)
        self.assertEqual(mrp.move_lines2[1].restrict_lot_id, lot_mp2)
        self.assertEqual(mrp.move_lines2[2].restrict_lot_id, lot_mp3)
        self.assertEqual(mrp.move_lines2[3].restrict_lot_id, lot_mp4)
        for move in mrp.move_lines2:
            self.assertEqual(move.state, 'done')
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 2)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 3)
        self.assertEqual(mrp.move_created_ids2[1].product_qty, 2)
        for move in mrp.move_created_ids2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)

    def test_mrp_production_partial_with_production_lot_mp_lots(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 5,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        lot = self.env['stock.production.lot'].create({
            'name': 'test',
            'product_id': self.product_fab1.id})
        partial_qty = 3
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': partial_qty,
                'lot_id': lot.id})
        lines = wiz.on_change_qty(partial_qty, [])
        wiz.write(lines['value'])
        lot_mp1 = self.env['stock.production.lot'].create({
            'name': 'test-mp1',
            'product_id': self.product_mp1.id})
        lot_mp2 = self.env['stock.production.lot'].create({
            'name': 'test-mp2',
            'product_id': self.product_mp2.id})
        wiz.consume_lines[0].lot_id = lot_mp1.id
        wiz.consume_lines[1].lot_id = lot_mp2.id
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 30)
        self.assertEqual(wiz.consume_lines[1].product_qty, 60)
        self.assertEqual(wiz.consume_lines[0].lot_id, lot_mp1)
        self.assertEqual(wiz.consume_lines[1].lot_id, lot_mp2)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 2)
        self.assertEqual(mrp.move_lines[0].product_qty, 20)
        self.assertEqual(mrp.move_lines[1].product_qty, 40)
        self.assertFalse(mrp.move_lines[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 30)
        self.assertEqual(mrp.move_lines2[1].product_qty, 60)
        self.assertEqual(mrp.move_lines2[0].restrict_lot_id, lot_mp1)
        self.assertEqual(mrp.move_lines2[1].restrict_lot_id, lot_mp2)
        self.assertEqual(len(mrp.move_created_ids), 1)
        self.assertEqual(len(mrp.move_created_ids2), 3)
        self.assertEqual(mrp.move_created_ids.product_qty, 2)
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.product_qty, 1)
            self.assertEqual(move.state, 'done')
            self.assertEqual(
                move.restrict_lot_id.name, self.get_lot_name('test', count))
        rest_qty = 2
        lot2 = self.env['stock.production.lot'].create({
            'name': 'test2',
            'product_id': self.product_fab1.id})
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': rest_qty,
                'lot_id': lot2.id})
        lines = wiz.on_change_qty(rest_qty, [])
        wiz.write(lines['value'])
        lot_mp3 = self.env['stock.production.lot'].create({
            'name': 'test2-mp1',
            'product_id': self.product_mp1.id})
        lot_mp4 = self.env['stock.production.lot'].create({
            'name': 'test2-mp2',
            'product_id': self.product_mp2.id})
        wiz.consume_lines[0].lot_id = lot_mp3.id
        wiz.consume_lines[1].lot_id = lot_mp4.id
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 20)
        self.assertEqual(wiz.consume_lines[1].product_qty, 40)
        self.assertEqual(wiz.consume_lines[0].lot_id, lot_mp3)
        self.assertEqual(wiz.consume_lines[1].lot_id, lot_mp4)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 4)
        self.assertEqual(mrp.move_lines2[0].product_qty, 30)
        self.assertEqual(mrp.move_lines2[1].product_qty, 60)
        self.assertEqual(mrp.move_lines2[2].product_qty, 20)
        self.assertEqual(mrp.move_lines2[3].product_qty, 40)
        self.assertEqual(mrp.move_lines2[0].restrict_lot_id, lot_mp1)
        self.assertEqual(mrp.move_lines2[1].restrict_lot_id, lot_mp2)
        self.assertEqual(mrp.move_lines2[2].restrict_lot_id, lot_mp3)
        self.assertEqual(mrp.move_lines2[3].restrict_lot_id, lot_mp4)
        for move in mrp.move_lines2:
            self.assertEqual(move.state, 'done')
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 5)
        all_lot_names = [
            self.get_lot_name('test', 1), self.get_lot_name('test', 2),
            self.get_lot_name('test', 3), self.get_lot_name('test2', 1),
            self.get_lot_name('test2', 2)]
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.product_qty, 1)
            self.assertEqual(move.state, 'done')
            self.assertIn(
                move.restrict_lot_id.name, all_lot_names, 'Lot errors')
            all_lot_names.remove(move.restrict_lot_id.name)

    def test_mrp_production_total_decimal_without_lot_mp_lots(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 5.12,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': mrp.product_qty})
        lines = wiz.on_change_qty(mrp.product_qty, [])
        wiz.write(lines['value'])
        lot_mp1 = self.env['stock.production.lot'].create({
            'name': 'test-mp1',
            'product_id': self.product_mp1.id})
        lot_mp2 = self.env['stock.production.lot'].create({
            'name': 'test-mp2',
            'product_id': self.product_mp2.id})
        wiz.consume_lines[0].lot_id = lot_mp1.id
        wiz.consume_lines[1].lot_id = lot_mp2.id
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 51.2)
        self.assertEqual(wiz.consume_lines[1].product_qty, 102.4)
        self.assertEqual(wiz.consume_lines[0].lot_id, lot_mp1)
        self.assertEqual(wiz.consume_lines[1].lot_id, lot_mp2)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 51.2)
        self.assertEqual(mrp.move_lines2[1].product_qty, 102.4)
        self.assertEqual(mrp.move_lines2[0].restrict_lot_id, lot_mp1)
        self.assertEqual(mrp.move_lines2[1].restrict_lot_id, lot_mp2)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 1)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 5.12)
        self.assertEqual(mrp.move_created_ids2[0].state, 'done')
        self.assertFalse(mrp.move_created_ids2[0].restrict_lot_id, None)

    def test_mrp_production_total_decimal_with_production_lot_mp_lots(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 5.12,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        lot = self.env['stock.production.lot'].create({
            'name': 'test',
            'product_id': self.product_fab1.id})
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': mrp.product_qty,
                'lot_id': lot.id})
        lines = wiz.on_change_qty(mrp.product_qty, [])
        wiz.write(lines['value'])
        lot_mp1 = self.env['stock.production.lot'].create({
            'name': 'test-mp1',
            'product_id': self.product_mp1.id})
        lot_mp2 = self.env['stock.production.lot'].create({
            'name': 'test-mp2',
            'product_id': self.product_mp2.id})
        wiz.consume_lines[0].lot_id = lot_mp1.id
        wiz.consume_lines[1].lot_id = lot_mp2.id
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 51.20)
        self.assertEqual(wiz.consume_lines[1].product_qty, 102.4)
        self.assertEqual(wiz.consume_lines[0].lot_id, lot_mp1)
        self.assertEqual(wiz.consume_lines[1].lot_id, lot_mp2)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 51.20)
        self.assertEqual(mrp.move_lines2[1].product_qty, 102.4)
        self.assertEqual(mrp.move_lines2[0].restrict_lot_id, lot_mp1)
        self.assertEqual(mrp.move_lines2[1].restrict_lot_id, lot_mp2)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 6)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[1].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[2].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[3].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[4].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[5].product_qty, 0.12)
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.state, 'done')
            self.assertEqual(
                move.restrict_lot_id.name, self.get_lot_name('test', count))

    def test_mrp_production_partial_decimal_without_lot_mp_lots(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 5.12,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        partial_qty = 3
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': partial_qty})
        lines = wiz.on_change_qty(partial_qty, [])
        wiz.write(lines['value'])
        lot_mp1 = self.env['stock.production.lot'].create({
            'name': 'test-mp1',
            'product_id': self.product_mp1.id})
        lot_mp2 = self.env['stock.production.lot'].create({
            'name': 'test-mp2',
            'product_id': self.product_mp2.id})
        wiz.consume_lines[0].lot_id = lot_mp1.id
        wiz.consume_lines[1].lot_id = lot_mp2.id
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 30)
        self.assertEqual(wiz.consume_lines[1].product_qty, 60)
        self.assertEqual(wiz.consume_lines[0].lot_id, lot_mp1)
        self.assertEqual(wiz.consume_lines[1].lot_id, lot_mp2)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 2)
        self.assertEqual(mrp.move_lines[0].product_qty, 21.2)
        self.assertEqual(mrp.move_lines[1].product_qty, 42.4)
        self.assertFalse(mrp.move_lines[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 30)
        self.assertEqual(mrp.move_lines2[1].product_qty, 60)
        self.assertEqual(mrp.move_lines2[0].restrict_lot_id, lot_mp1)
        self.assertEqual(mrp.move_lines2[1].restrict_lot_id, lot_mp2)
        self.assertEqual(len(mrp.move_created_ids), 1)
        self.assertEqual(mrp.move_created_ids[0].product_qty, 2.12)
        self.assertEqual(mrp.move_created_ids[0].state, 'assigned')
        self.assertFalse(mrp.move_created_ids[0].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids2), 1)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 3)
        self.assertEqual(mrp.move_created_ids2[0].state, 'done')
        self.assertFalse(mrp.move_created_ids2[0].restrict_lot_id, None)
        rest_qty = 2.12
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': rest_qty})
        lines = wiz.on_change_qty(rest_qty, [])
        wiz.write(lines['value'])
        lot_mp3 = self.env['stock.production.lot'].create({
            'name': 'test2-mp1',
            'product_id': self.product_mp1.id})
        lot_mp4 = self.env['stock.production.lot'].create({
            'name': 'test2-mp2',
            'product_id': self.product_mp2.id})
        wiz.consume_lines[0].lot_id = lot_mp3.id
        wiz.consume_lines[1].lot_id = lot_mp4.id
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 21.2)
        self.assertEqual(wiz.consume_lines[1].product_qty, 42.4)
        self.assertEqual(wiz.consume_lines[0].lot_id, lot_mp3)
        self.assertEqual(wiz.consume_lines[1].lot_id, lot_mp4)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 4)
        self.assertEqual(mrp.move_lines2[0].product_qty, 30)
        self.assertEqual(mrp.move_lines2[1].product_qty, 60)
        self.assertEqual(mrp.move_lines2[2].product_qty, 21.2)
        self.assertEqual(mrp.move_lines2[3].product_qty, 42.4)
        self.assertEqual(mrp.move_lines2[0].restrict_lot_id, lot_mp1)
        self.assertEqual(mrp.move_lines2[1].restrict_lot_id, lot_mp2)
        self.assertEqual(mrp.move_lines2[2].restrict_lot_id, lot_mp3)
        self.assertEqual(mrp.move_lines2[3].restrict_lot_id, lot_mp4)
        for move in mrp.move_lines2:
            self.assertEqual(move.state, 'done')
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 2)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 3)
        self.assertEqual(mrp.move_created_ids2[1].product_qty, 2.12)
        for move in mrp.move_created_ids2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)

    def test_mrp_production_total_one_without_lot(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 1,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': mrp.product_qty})
        lines = wiz.on_change_qty(mrp.product_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 10)
        self.assertEqual(wiz.consume_lines[1].product_qty, 20)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 10)
        self.assertEqual(mrp.move_lines2[1].product_qty, 20)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 1)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[0].state, 'done')
        self.assertFalse(mrp.move_created_ids2[0].restrict_lot_id, None)

    def test_mrp_production_total_one_with_production_lot(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 1,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        lot = self.env['stock.production.lot'].create({
            'name': 'test',
            'product_id': self.product_fab1.id})
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': mrp.product_qty,
                'lot_id': lot.id})
        lines = wiz.on_change_qty(mrp.product_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 10)
        self.assertEqual(wiz.consume_lines[1].product_qty, 20)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 10)
        self.assertEqual(mrp.move_lines2[1].product_qty, 20)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 1)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[0].state, 'done')
        self.assertEqual(mrp.move_created_ids2[0].restrict_lot_id.name, 'test')

    def test_mrp_production_partial_one_without_lot(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 5,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        partial_qty = 4
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': partial_qty})
        lines = wiz.on_change_qty(partial_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 40)
        self.assertEqual(wiz.consume_lines[1].product_qty, 80)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 2)
        self.assertEqual(mrp.move_lines[0].product_qty, 10)
        self.assertEqual(mrp.move_lines[1].product_qty, 20)
        self.assertFalse(mrp.move_lines[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 40)
        self.assertEqual(mrp.move_lines2[1].product_qty, 80)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 1)
        self.assertEqual(mrp.move_created_ids[0].product_qty, 1)
        self.assertEqual(mrp.move_created_ids[0].state, 'assigned')
        self.assertFalse(mrp.move_created_ids[0].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids2), 1)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 4)
        self.assertEqual(mrp.move_created_ids2[0].state, 'done')
        self.assertFalse(mrp.move_created_ids2[0].restrict_lot_id, None)
        rest_qty = 1
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': rest_qty})
        lines = wiz.on_change_qty(rest_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 10)
        self.assertEqual(wiz.consume_lines[1].product_qty, 20)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 4)
        self.assertEqual(mrp.move_lines2[0].product_qty, 40)
        self.assertEqual(mrp.move_lines2[1].product_qty, 80)
        self.assertEqual(mrp.move_lines2[2].product_qty, 10)
        self.assertEqual(mrp.move_lines2[3].product_qty, 20)
        for move in mrp.move_lines2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 2)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 4)
        self.assertEqual(mrp.move_created_ids2[1].product_qty, 1)
        for move in mrp.move_created_ids2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)

    def test_mrp_production_partial_one_with_production_lot(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 5,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        lot = self.env['stock.production.lot'].create({
            'name': 'test',
            'product_id': self.product_fab1.id})
        partial_qty = 4
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': partial_qty,
                'lot_id': lot.id})
        lines = wiz.on_change_qty(partial_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 40)
        self.assertEqual(wiz.consume_lines[1].product_qty, 80)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 2)
        self.assertEqual(mrp.move_lines[0].product_qty, 10)
        self.assertEqual(mrp.move_lines[1].product_qty, 20)
        self.assertFalse(mrp.move_lines[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 40)
        self.assertEqual(mrp.move_lines2[1].product_qty, 80)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 1)
        self.assertEqual(len(mrp.move_created_ids2), 4)
        self.assertEqual(mrp.move_created_ids.product_qty, 1)
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.product_qty, 1)
            self.assertEqual(move.state, 'done')
            self.assertEqual(
                move.restrict_lot_id.name, self.get_lot_name('test', count))
        rest_qty = 1
        lot2 = self.env['stock.production.lot'].create({
            'name': 'test2',
            'product_id': self.product_fab1.id})
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': rest_qty,
                'lot_id': lot2.id})
        lines = wiz.on_change_qty(rest_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 10)
        self.assertEqual(wiz.consume_lines[1].product_qty, 20)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 4)
        self.assertEqual(mrp.move_lines2[0].product_qty, 40)
        self.assertEqual(mrp.move_lines2[1].product_qty, 80)
        self.assertEqual(mrp.move_lines2[2].product_qty, 10)
        self.assertEqual(mrp.move_lines2[3].product_qty, 20)
        for move in mrp.move_lines2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 5)
        for move in mrp.move_created_ids2:
            self.assertEqual(move.product_qty, 1)
        all_lot_names = [
            self.get_lot_name('test', 1), self.get_lot_name('test', 2),
            self.get_lot_name('test', 3), self.get_lot_name('test', 4),
            'test2']
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.product_qty, 1)
            self.assertEqual(move.state, 'done')
            self.assertIn(
                move.restrict_lot_id.name, all_lot_names, 'Lot errors')
            all_lot_names.remove(move.restrict_lot_id.name)

    def test_mrp_production_partial_decimal_one_without_lot(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 5.12,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        partial_qty = 4.12
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': partial_qty})
        lines = wiz.on_change_qty(partial_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 41.2)
        self.assertEqual(wiz.consume_lines[1].product_qty, 82.4)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 2)
        self.assertEqual(mrp.move_lines[0].product_qty, 10)
        self.assertEqual(mrp.move_lines[1].product_qty, 20)
        self.assertFalse(mrp.move_lines[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 41.2)
        self.assertEqual(mrp.move_lines2[1].product_qty, 82.4)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 1)
        self.assertEqual(mrp.move_created_ids[0].product_qty, 1)
        self.assertEqual(mrp.move_created_ids[0].state, 'assigned')
        self.assertFalse(mrp.move_created_ids[0].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids2), 1)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 4.12)
        self.assertEqual(mrp.move_created_ids2[0].state, 'done')
        self.assertFalse(mrp.move_created_ids2[0].restrict_lot_id, None)
        rest_qty = 1
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': rest_qty})
        lines = wiz.on_change_qty(rest_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 10)
        self.assertEqual(wiz.consume_lines[1].product_qty, 20)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 4)
        self.assertEqual(mrp.move_lines2[0].product_qty, 41.2)
        self.assertEqual(mrp.move_lines2[1].product_qty, 82.4)
        self.assertEqual(mrp.move_lines2[2].product_qty, 10)
        self.assertEqual(mrp.move_lines2[3].product_qty, 20)
        for move in mrp.move_lines2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 2)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 4.12)
        self.assertEqual(mrp.move_created_ids2[1].product_qty, 1)
        for move in mrp.move_created_ids2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)

    def test_mrp_production_partial_decimal_one_with_production_lot(self):
        mrp = self.env['mrp.production'].create({
            'product_id': self.product_fab1.id,
            'product_qty': 5.12,
            'product_uom': self.product_fab1.uom_id.id,
            'bom_id': self.bom1.id})
        mrp.action_confirm()
        lot = self.env['stock.production.lot'].create({
            'name': 'test',
            'product_id': self.product_fab1.id})
        partial_qty = 4.12
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': partial_qty,
                'lot_id': lot.id})
        lines = wiz.on_change_qty(partial_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 41.2)
        self.assertEqual(wiz.consume_lines[1].product_qty, 82.4)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 2)
        self.assertEqual(mrp.move_lines[0].product_qty, 10)
        self.assertEqual(mrp.move_lines[1].product_qty, 20)
        self.assertFalse(mrp.move_lines[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_lines2), 2)
        self.assertEqual(mrp.move_lines2[0].product_qty, 41.2)
        self.assertEqual(mrp.move_lines2[1].product_qty, 82.4)
        self.assertFalse(mrp.move_lines2[0].restrict_lot_id, None)
        self.assertFalse(mrp.move_lines2[1].restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 1)
        self.assertEqual(len(mrp.move_created_ids2), 5)
        self.assertEqual(mrp.move_created_ids2[0].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[1].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[2].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[3].product_qty, 1)
        self.assertEqual(mrp.move_created_ids2[4].product_qty, 0.12)
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.state, 'done')
            self.assertEqual(
                move.restrict_lot_id.name, self.get_lot_name('test', count))
        rest_qty = 1
        lot2 = self.env['stock.production.lot'].create({
            'name': 'test2',
            'product_id': self.product_fab1.id})
        wiz = self.env['mrp.product.produce'].with_context({
            'active_ids': [mrp.id],
            'active_model': 'mrp.production',
            'active_id': mrp.id}).create({
                'mode': 'consume_produce',
                'product_qty': rest_qty,
                'lot_id': lot2.id})
        lines = wiz.on_change_qty(rest_qty, [])
        wiz.write(lines['value'])
        self.assertEqual(len(wiz.consume_lines), 2)
        self.assertEqual(wiz.consume_lines[0].product_qty, 10)
        self.assertEqual(wiz.consume_lines[1].product_qty, 20)
        self.assertFalse(wiz.consume_lines[0].lot_id, None)
        self.assertFalse(wiz.consume_lines[1].lot_id, None)
        wiz.do_produce()
        self.assertEqual(len(mrp.move_lines), 0)
        self.assertEqual(len(mrp.move_lines2), 4)
        self.assertEqual(mrp.move_lines2[0].product_qty, 41.2)
        self.assertEqual(mrp.move_lines2[1].product_qty, 82.4)
        self.assertEqual(mrp.move_lines2[2].product_qty, 10)
        self.assertEqual(mrp.move_lines2[3].product_qty, 20)
        for move in mrp.move_lines2:
            self.assertEqual(move.state, 'done')
            self.assertFalse(move.restrict_lot_id, None)
        self.assertEqual(len(mrp.move_created_ids), 0)
        self.assertEqual(len(mrp.move_created_ids2), 6)
        all_lot_names = [
            self.get_lot_name('test', 1), self.get_lot_name('test', 2),
            self.get_lot_name('test', 3), self.get_lot_name('test', 4),
            self.get_lot_name('test', 5), 'test2']
        for count, move in enumerate(mrp.move_created_ids2, 1):
            self.assertEqual(move.state, 'done')
            self.assertIn(
                move.restrict_lot_id.name, all_lot_names, 'Lot errors')
            all_lot_names.remove(move.restrict_lot_id.name)
