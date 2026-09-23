###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import time

from odoo.tests.common import TransactionCase


class TestMoveLineRelation(TransactionCase):

    def setUp(self):
        super().setUp()
        self.supplier = self._create_record(
            model_name='res.partner',
            vals={
                'name': 'Supplier test',
                'supplier': True,
                'delivery_slip_type': 'valued',
            },
        )
        self.customer = self._create_record(
            model_name='res.partner',
            vals={
                'name': 'customer test',
                'customer': True,
            },
        )
        self.product_tracking_lot = self._create_record(
            model_name='product.product',
            vals={
                'name': 'Product with lot',
                'type': 'product',
                'default_code': 'PRODUCT-LOT',
                'standard_price': -1,
                'tracking': 'lot',
            },
        )
        self.product_no_tracking = self._create_record(
            model_name='product.product',
            vals={
                'name': 'Product',
                'type': 'product',
                'default_code': 'PRODUCT',
                'standard_price': -1,
            },
        )
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.internal_location = self.env['stock.location'].create({
            'name': 'Internal location',
            'usage': 'internal',
        })

    def _create_record(self, model_name, vals):
        record = self._create_vals(model_name, vals)
        return record.create(record._convert_to_write(record._cache))

    def _create_vals(self, model_name, vals):
        model = self.env[model_name]
        data = model.default_get(list(model.fields_get()))
        data.update(vals)
        return model.new(data)

    def _create_picking(
            self, picking_type, product, qty, price_unit, lot=None,
            src_internal_location=None, dst_internal_location=None):
        if picking_type == 'in':
            location_src = self.env.ref('stock.stock_location_suppliers')
            location_dst = self.env.ref('stock.stock_location_stock')
        elif picking_type == 'out':
            location_src = self.env.ref('stock.stock_location_stock')
            location_dst = self.env.ref('stock.stock_location_customers')
        elif picking_type == 'internal':
            location_src = src_internal_location
            location_dst = dst_internal_location
        picking_type = self.env.ref(f'stock.picking_type_{picking_type}')
        data_move_lines = {
            'product_id': product.id,
            'name': product.name,
            'product_uom': product.uom_id.id,
            'product_uom_qty': qty,
            'procure_method': 'make_to_stock',
            'price_unit': price_unit,
            'value': qty * price_unit,
            # @TODO En el mrp_cost_price puede estar mal, esto no
            # se reseteaba a draft, y si no lo está, el método
            # product_price_update_before_done no hace nada de
            # actualizar el precio de coste
            # addons/stock_account/models/stock.py:435
            'state': 'draft',
        }
        if lot:
            data_move_lines.update({
                'lot_id': lot.id,
            })
        new_picking = self._create_vals(
            model_name='stock.picking',
            vals={
                'location_id': location_src.id,
                'location_dest_id': location_dst.id,
                'picking_type_id': picking_type.id,
                'move_lines': [
                    (0, 0, data_move_lines),
                ],
            },
        )
        if picking_type.code != 'internal':
            new_picking.onchange_picking_type()
        new_picking.move_lines.onchange_product_id()
        picking = new_picking.create(
            new_picking._convert_to_write(new_picking._cache))
        picking.action_confirm()
        picking.action_assign()
        for move_line in picking.move_line_ids:
            if lot:
                move_line.lot_id = lot.id
            move_line.qty_done = move_line.product_uom_qty
        picking.action_done()
        time.sleep(1)
        return picking

    def _create_inventory(self, location, product, qty, lot=None):
        inventory = self.env['stock.inventory'].create({
            'name': 'Add products for tests',
            'filter': 'partial',
            'location_id': location.id,
            'exhausted': True,
        })
        inventory.action_start()
        line_data = {
            'inventory_id': inventory.id,
            'product_id': product.id,
            'product_qty': qty,
            'location_id': location.id,
        }
        if lot:
            line_data.update({
                'prod_lot_id': lot.id,
            })
        inventory.line_ids.create(line_data)
        inventory._action_done()
        time.sleep(1)
        return inventory

    # @TODO A falta de revisar con flujo standard
    def TODOtest_stock_ml_rel_product_tracking_lot_standard_basic(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'standard'
        self.product_tracking_lot.standard_price = 10
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=5, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=1, price_unit=100)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 100)
        self.assertEqual(self.product_tracking_lot.standard_price, 10)

    # @TODO A falta de revisar con flujo average
    def TODOtest_stock_ml_rel_product_tracking_lot_average_basic(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'average'
        self.assertEqual(self.product_tracking_lot.standard_price, -1.0)
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=5, price_unit=100,
            lot=lot_001)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=1, price_unit=100)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 100)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=5, price_unit=200,
            lot=lot_001)
        self.assertEqual(self.product_tracking_lot.standard_price, 155.56)

    def test_stock_ml_rel_product_tracking_lot_fifo_basic(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=5, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=1, price_unit=100)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 100)

    def test_stock_ml_rel_product_tracking_lot_fifo_01(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.assertEqual(self.product_tracking_lot.standard_price, -1.0)
        # IN001 qty=2; price_unit=100€; lot=001
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=2, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # IN002 qty=4; price_unit=200€; lot=001
        picking_in_02 = self._create_picking(
            'in', self.product_tracking_lot, qty=4, price_unit=200,
            lot=lot_001)
        move_line_in_02 = picking_in_02.move_line_ids
        self.assertFalse(move_line_in_02.move_line_relation_ids)
        # OUT001 qty=3; price_unit=888€
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=3, price_unit=888)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 100)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_02)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 200)

    def test_stock_ml_rel_product_tracking_lot_fifo_02(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.assertEqual(self.product_tracking_lot.standard_price, -1.0)
        # IN001 qty=2; price_unit=150€; lot001
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=2, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # IN002 qty=4; price_unit=100€; lot002
        lot_002 = self.env['stock.production.lot'].create({
            'name': '002',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_02 = self._create_picking(
            'in', self.product_tracking_lot, qty=4, price_unit=200,
            lot=lot_002)
        move_line_in_02 = picking_in_02.move_line_ids
        self.assertFalse(move_line_in_02.move_line_relation_ids)
        # OUT001 qty=3; price_unit=888€
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=3, price_unit=888)
        # OUT002 qty=1; price_unit=777€
        picking_out_02 = self._create_picking(
            'out', self.product_tracking_lot, qty=1, price_unit=777)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01), 2)
        move_line_out_01_01 = move_lines_out_01.filtered(
            lambda ml: ml.qty_done == 2 and ml.lot_id == lot_001)
        self.assertEquals(len(move_line_out_01_01), 1)
        self.assertEquals(len(move_line_out_01_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(
            move_line_out_01_01.move_line_relation_ids.quantity, 2)
        self.assertEquals(
            move_line_out_01_01.move_line_relation_ids.price_unit, 100)
        move_line_out_01_02 = move_lines_out_01.filtered(
            lambda ml: ml.qty_done == 1 and ml.lot_id == lot_002)
        self.assertEquals(len(move_line_out_01_02), 1)
        self.assertEquals(len(move_line_out_01_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01_02.move_line_relation_ids.move_line_id,
            move_line_in_02)
        self.assertEquals(
            move_line_out_01_02.move_line_relation_ids.quantity, 1)
        move_line_out_02 = picking_out_02.move_line_ids
        self.assertEquals(len(move_line_out_02), 1)
        self.assertEquals(len(move_line_out_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.move_line_id,
            move_line_in_02)
        self.assertEquals(move_line_out_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.price_unit, 200)

    def test_stock_ml_rel_product_tracking_lot_fifo_03(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.assertEqual(self.product_tracking_lot.standard_price, -1.0)
        # IN001 qty=2; price_unit=100€
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=2, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # IN002 qty=4; price_unit=200€
        lot_002 = self.env['stock.production.lot'].create({
            'name': '002',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_02 = self._create_picking(
            'in', self.product_tracking_lot, qty=4, price_unit=200,
            lot=lot_002)
        move_line_in_02 = picking_in_02.move_line_ids
        self.assertFalse(move_line_in_02.move_line_relation_ids)
        # IN003 qty=10; price_unit=200€
        picking_in_03 = self._create_picking(
            'in', self.product_tracking_lot, qty=10, price_unit=200,
            lot=lot_001)
        move_line_in_03 = picking_in_03.move_line_ids
        self.assertFalse(move_line_in_03.move_line_relation_ids)
        # OUT001 qty=3; price_unit=888€
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=3, price_unit=888)
        # OUT002 qty=1; price_unit=777€
        picking_out_02 = self._create_picking(
            'out', self.product_tracking_lot, qty=1, price_unit=777)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 100)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_03)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 200)
        move_line_out_02 = picking_out_02.move_line_ids
        self.assertEquals(len(move_line_out_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.move_line_id,
            move_line_in_03)
        self.assertEquals(move_line_out_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.price_unit, 200)

    def test_stock_ml_rel_product_tracking_lot_fifo_04(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.assertEqual(self.product_tracking_lot.standard_price, -1.0)
        # IN001 qty=2; price_unit=150€; lot=001
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=2, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # IN002 qty=4; price_unit=200€; lot=002
        lot_002 = self.env['stock.production.lot'].create({
            'name': '002',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_02 = self._create_picking(
            'in', self.product_tracking_lot, qty=4, price_unit=200,
            lot=lot_002)
        move_line_in_02 = picking_in_02.move_line_ids
        self.assertFalse(move_line_in_02.move_line_relation_ids)
        # IN003 qty=10; price_unit=200€; lot=001
        picking_in_03 = self._create_picking(
            'in', self.product_tracking_lot, qty=10, price_unit=200,
            lot=lot_001)
        move_line_in_03 = picking_in_03.move_line_ids
        self.assertFalse(move_line_in_03.move_line_relation_ids)
        # OUT001 qty=3; price_unit=888€
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=3, price_unit=888)
        # OUT002 qty=1; price_unit=777€
        picking_out_02 = self._create_picking(
            'out', self.product_tracking_lot, qty=1, price_unit=777)
        # OUT003 qty=9; price_unit=666€
        picking_out_03 = self._create_picking(
            'out', self.product_tracking_lot, qty=9, price_unit=666)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 100)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_03)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 200)
        move_line_out_02 = picking_out_02.move_line_ids
        self.assertEquals(len(move_line_out_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.move_line_id,
            move_line_in_03)
        self.assertEquals(move_line_out_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.price_unit, 200)
        move_lines_out_03 = picking_out_03.move_line_ids
        self.assertEquals(len(move_lines_out_03), 2)
        move_line_out_03_01 = move_lines_out_03.filtered(
            lambda ml: ml.qty_done == 8 and ml.lot_id == lot_001)
        self.assertEquals(len(move_line_out_03_01), 1)
        self.assertEquals(len(move_line_out_03_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_03_01.move_line_relation_ids.move_line_id,
            move_line_in_03)
        self.assertEquals(
            move_line_out_03_01.move_line_relation_ids.quantity, 8)
        self.assertEquals(
            move_line_out_03_01.move_line_relation_ids.price_unit, 200)
        move_line_out_03_02 = move_lines_out_03.filtered(
            lambda ml: ml.qty_done == 1 and ml.lot_id == lot_002)
        self.assertEquals(len(move_line_out_03_02), 1)
        self.assertEquals(len(move_line_out_03_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_03_02.move_line_relation_ids.move_line_id,
            move_line_in_02)
        self.assertEquals(
            move_line_out_03_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_03_02.move_line_relation_ids.price_unit, 200)

    def test_stock_ml_rel_product_tracking_lot_fifo_05(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.assertEqual(self.product_tracking_lot.standard_price, -1.0)
        # IN001: qty=5 (2uds lot1; 3uds lot2); ; price_unit=100€
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        lot_002 = self.env['stock.production.lot'].create({
            'name': '002',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_01 = self.env['stock.picking'].create({
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': self.env.ref('stock.stock_location_stock').id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product_tracking_lot.id,
                    'name': self.product_tracking_lot.name,
                    'product_uom': self.product_tracking_lot.uom_id.id,
                    'product_uom_qty': 5,
                    'procure_method': 'make_to_stock',
                    'price_unit': 100,
                    'value': 5 * 100,
                    'state': 'draft',
                }),
            ],
        })
        picking_in_01.move_lines.onchange_product_id()
        picking_in_01.action_confirm()
        picking_in_01.action_assign()
        picking_in_01.move_line_ids[0].qty_done = 2
        picking_in_01.move_line_ids[0].lot_id = lot_001.id
        self.env['stock.move.line'].create({
            'move_id': picking_in_01.move_lines[0].id,
            'picking_id': picking_in_01.id,
            'product_id': self.product_tracking_lot.id,
            'product_uom_id': self.product_tracking_lot.uom_id.id,
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': self.env.ref('stock.stock_location_stock').id,
            'qty_done': 3,
            'lot_id': lot_002.id,
        })
        picking_in_01.action_done()
        self.assertEqual(len(picking_in_01.move_line_ids), 2)
        self.assertEqual(picking_in_01.state, 'done')
        time.sleep(1)
        move_line_in_lot_001 = picking_in_01.move_line_ids.filtered(
            lambda ml: ml.lot_id == lot_001)
        self.assertEqual(len(move_line_in_lot_001), 1)
        move_line_in_lot_002 = picking_in_01.move_line_ids.filtered(
            lambda ml: ml.lot_id == lot_002)
        self.assertEqual(len(move_line_in_lot_002), 1)
        self.assertFalse(move_line_in_lot_001.move_line_relation_ids)
        self.assertFalse(move_line_in_lot_002.move_line_relation_ids)
        # OUT001: 1uds (lot1)
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=1, price_unit=888,
            lot=lot_001)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_lot_001)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 100)
        # OUT2: 2uds (1 lot1, 1 lot2)
        picking_out_02 = self.env['stock.picking'].create({
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': (
                self.env.ref('stock.stock_location_customers').id),
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product_tracking_lot.id,
                    'name': self.product_tracking_lot.name,
                    'product_uom': self.product_tracking_lot.uom_id.id,
                    'product_uom_qty': 2,
                    'procure_method': 'make_to_stock',
                    'price_unit': 100,
                    'value': 2 * 100,
                    'state': 'draft',
                }),
            ],
        })
        picking_out_02.move_lines.onchange_product_id()
        picking_out_02.action_confirm()
        picking_out_02.action_assign()
        self.assertEqual(len(picking_out_02.move_line_ids), 2)
        move_line_out_02_lot_001 = picking_out_02.move_line_ids.filtered(
            lambda ml: ml.lot_id == lot_001)
        self.assertEqual(len(move_line_out_02_lot_001), 1)
        move_line_out_02_lot_001.qty_done = 1
        move_line_out_02_lot_002 = picking_out_02.move_line_ids.filtered(
            lambda ml: ml.lot_id == lot_002)
        self.assertEqual(len(move_line_out_02_lot_002), 1)
        move_line_out_02_lot_002.qty_done = 1
        picking_out_02.action_done()
        self.assertEqual(picking_out_02.state, 'done')
        time.sleep(1)
        self.assertEqual(
            move_line_out_02_lot_001.move_line_relation_ids.move_line_id,
            move_line_in_lot_001)
        self.assertEquals(
            move_line_out_02_lot_001.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02_lot_001.move_line_relation_ids.price_unit, 100)

        self.assertEqual(
            move_line_out_02_lot_002.move_line_relation_ids.move_line_id,
            move_line_in_lot_002)
        self.assertEquals(
            move_line_out_02_lot_002.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02_lot_002.move_line_relation_ids.price_unit, 100)

    def test_stock_ml_rel_product_no_tracking_fifo_basic(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        picking_in_01 = self._create_picking(
            'in', self.product_no_tracking, qty=5, price_unit=100)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=1, price_unit=100)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 100)

    def test_stock_ml_rel_product_no_tracking_fifo_01(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.assertEqual(self.product_no_tracking.standard_price, -1.0)
        # IN001 qty=2; price_unit=100€
        picking_in_01 = self._create_picking(
            'in', self.product_no_tracking, qty=2, price_unit=100)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # IN002 qty=4; price_unit=200€
        picking_in_02 = self._create_picking(
            'in', self.product_no_tracking, qty=4, price_unit=200)
        move_line_in_02 = picking_in_02.move_line_ids
        self.assertFalse(move_line_in_02.move_line_relation_ids)
        # OUT001 qty=3; price_unit=888€
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=3, price_unit=888)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 100)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_02)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 200)

    def test_stock_ml_rel_product_no_tracking_fifo_02(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.assertEqual(self.product_no_tracking.standard_price, -1.0)
        # IN001 qty=2; price_unit=150€
        picking_in_01 = self._create_picking(
            'in', self.product_no_tracking, qty=2, price_unit=100)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # IN002 qty=4; price_unit=100€
        picking_in_02 = self._create_picking(
            'in', self.product_no_tracking, qty=4, price_unit=200)
        move_line_in_02 = picking_in_02.move_line_ids
        self.assertFalse(move_line_in_02.move_line_relation_ids)
        # OUT001 qty=3; price_unit=888€
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=3, price_unit=888)
        # OUT002 qty=1; price_unit=777€
        picking_out_02 = self._create_picking(
            'out', self.product_no_tracking, qty=1, price_unit=777)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01), 1)
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_line_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 100)
        move_line_out_relation_01_02 = (
            move_line_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_02)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 200)
        move_line_out_02 = picking_out_02.move_line_ids
        self.assertEquals(len(move_line_out_02), 1)
        self.assertEquals(len(move_line_out_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.move_line_id,
            move_line_in_02)
        self.assertEquals(move_line_out_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.price_unit, 200)

    def test_stock_ml_rel_product_no_tracking_fifo_03(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.assertEqual(self.product_no_tracking.standard_price, -1.0)
        # IN001 qty=2; price_unit=100€
        picking_in_01 = self._create_picking(
            'in', self.product_no_tracking, qty=2, price_unit=100)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # IN002 qty=4; price_unit=200€
        picking_in_02 = self._create_picking(
            'in', self.product_no_tracking, qty=4, price_unit=200)
        move_line_in_02 = picking_in_02.move_line_ids
        self.assertFalse(move_line_in_02.move_line_relation_ids)
        # IN003 qty=10; price_unit=200€
        picking_in_03 = self._create_picking(
            'in', self.product_no_tracking, qty=10, price_unit=200)
        move_line_in_03 = picking_in_03.move_line_ids
        self.assertFalse(move_line_in_03.move_line_relation_ids)
        # OUT001 qty=3; price_unit=888€
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=3, price_unit=888)
        # OUT002 qty=1; price_unit=777€
        picking_out_02 = self._create_picking(
            'out', self.product_no_tracking, qty=1, price_unit=777)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 100)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_02)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 200)
        move_line_out_02 = picking_out_02.move_line_ids
        self.assertEquals(len(move_line_out_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.move_line_id,
            move_line_in_02)
        self.assertEquals(move_line_out_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.price_unit, 200)

    def test_stock_ml_rel_product_no_tracking_fifo_04(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.assertEqual(self.product_no_tracking.standard_price, -1.0)
        # IN001 qty=2; price_unit=100€
        picking_in_01 = self._create_picking(
            'in', self.product_no_tracking, qty=2, price_unit=100)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # IN002 qty=4; price_unit=200€
        picking_in_02 = self._create_picking(
            'in', self.product_no_tracking, qty=4, price_unit=200)
        move_line_in_02 = picking_in_02.move_line_ids
        self.assertFalse(move_line_in_02.move_line_relation_ids)
        # IN003 qty=10; price_unit=200€
        picking_in_03 = self._create_picking(
            'in', self.product_no_tracking, qty=10, price_unit=200)
        move_line_in_03 = picking_in_03.move_line_ids
        self.assertFalse(move_line_in_03.move_line_relation_ids)
        # OUT001 qty=3; price_unit=888€
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=3, price_unit=888)
        # OUT002 qty=1; price_unit=777€
        picking_out_02 = self._create_picking(
            'out', self.product_no_tracking, qty=1, price_unit=777)
        # OUT003 qty=9; price_unit=666€
        picking_out_03 = self._create_picking(
            'out', self.product_no_tracking, qty=9, price_unit=666)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 100)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_02)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 200)
        move_line_out_02 = picking_out_02.move_line_ids
        self.assertEquals(len(move_line_out_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.move_line_id,
            move_line_in_02)
        self.assertEquals(move_line_out_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.price_unit, 200)
        move_lines_out_03 = picking_out_03.move_line_ids
        self.assertEquals(len(move_lines_out_03), 1)
        self.assertEquals(len(move_lines_out_03.move_line_relation_ids), 2)
        move_line_out_relation_03_01 = (
            move_lines_out_03.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_03_01), 1)
        self.assertEquals(
            move_line_out_relation_03_01.move_line_id, move_line_in_02)
        self.assertEquals(move_line_out_relation_03_01.price_unit, 200)
        move_line_out_relation_03_02 = (
            move_lines_out_03.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 7))
        self.assertEquals(len(move_line_out_relation_03_02), 1)
        self.assertEquals(
            move_line_out_relation_03_02.move_line_id, move_line_in_03)
        self.assertEquals(move_line_out_relation_03_02.price_unit, 200)

    def test_stock_ml_rel_product_no_tracking_fifo_receipt_before_05(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.assertEqual(self.product_no_tracking.standard_price, -1.0)
        # IN002 qty=200; price_unit=200€ It is created but received later
        picking_in_02 = self.env['stock.picking'].create({
            'location_id': self.env.ref('stock.stock_location_suppliers').id,
            'location_dest_id': self.env.ref('stock.stock_location_stock').id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product_no_tracking.id,
                    'name': self.product_no_tracking.name,
                    'product_uom': self.product_no_tracking.uom_id.id,
                    'product_uom_qty': 200,
                    'procure_method': 'make_to_stock',
                    'price_unit': 200,
                    'value': 200 * 200,
                    'state': 'draft',
                }),
            ],
        })
        # IN001 qty=100; price_unit=100€
        picking_in_01 = self._create_picking(
            'in', self.product_no_tracking, qty=100, price_unit=100)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # OUT001 qty=10; price_unit=100€
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=10, price_unit=100)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_lines_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(
            move_lines_out_01.move_line_relation_ids.price_unit, 100)
        # OUT002 qty=80; price_unit=100€
        picking_out_02 = self._create_picking(
            'out', self.product_no_tracking, qty=80, price_unit=100)
        move_lines_out_01 = picking_out_02.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_lines_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(
            move_lines_out_01.move_line_relation_ids.price_unit, 100)
        # IN002 qty=200; price_unit=200€ received
        picking_in_02.action_confirm()
        picking_in_02.action_assign()
        for move_line in picking_in_02.move_line_ids:
            move_line.qty_done = move_line.product_uom_qty
        picking_in_02.action_done()
        time.sleep(1)
        move_line_in_02 = picking_in_02.move_line_ids
        self.assertFalse(move_line_in_02.move_line_relation_ids)
        # OUT003 qty=205; price_unit=195.12valoración
        picking_out_03 = self._create_picking(
            'out', self.product_no_tracking, qty=205, price_unit=195.12)
        move_lines_out_03 = picking_out_03.move_line_ids
        self.assertEquals(len(move_lines_out_03.move_line_relation_ids), 2)
        move_line_out_relation_03_01 = (
            move_lines_out_03.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 10))
        self.assertEquals(len(move_line_out_relation_03_01), 1)
        self.assertEquals(
            move_line_out_relation_03_01.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_03_01.price_unit, 100)
        move_line_out_relation_03_02 = (
            move_lines_out_03.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 195))
        self.assertEquals(len(move_line_out_relation_03_02), 1)
        self.assertEquals(
            move_line_out_relation_03_02.move_line_id, move_line_in_02)
        self.assertEquals(move_line_out_relation_03_02.price_unit, 200)

    def test_stock_ml_rel_product_tracking_lot_fifo_inventory_01(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.assertEqual(self.product_tracking_lot.standard_price, -1.0)
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        # Inventory adjustment qty=1; lot=001
        inventory = self._create_inventory(
            self.stock_location, self.product_tracking_lot, 1, lot_001)
        move_line_inventory_01 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_01), 1)
        self.assertEqual(self.product_tracking_lot.stock_value, -1.0)
        self.assertEqual(self.product_tracking_lot.standard_price, -1.0)
        # IN001 qty=5; price_unit=100€; lot=001
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=5, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # OUT001 qty=1
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=1, price_unit=100)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_inventory_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, -1)

    def test_stock_ml_rel_product_tracking_lot_fifo_inventory_02(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.assertEqual(self.product_tracking_lot.standard_price, -1.0)
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        # Inventory adjustment qty=1; lot=001
        inventory = self._create_inventory(
            self.stock_location, self.product_tracking_lot, 1, lot_001)
        move_line_inventory_01 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_01), 1)
        self.assertEqual(self.product_tracking_lot.stock_value, -1.0)
        self.assertEqual(self.product_tracking_lot.standard_price, -1.0)
        # IN001 qty=5; price_unit=100€; lot=001
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=5, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # OUT001 qty=3
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=3, price_unit=100)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 2)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_inventory_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, -1)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 100)

    def test_stock_ml_rel_product_tracking_lot_fifo_inventory_03(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.assertEqual(self.product_tracking_lot.standard_price, -1.0)
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        # Inventory adjustment 1 qty=1; lot=001
        inventory = self._create_inventory(
            self.stock_location, self.product_tracking_lot, 1, lot_001)
        move_line_inventory_01 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_01), 1)
        self.assertEqual(self.product_tracking_lot.stock_value, -1.0)
        self.assertEqual(self.product_tracking_lot.standard_price, -1.0)
        # IN001 qty=5; price_unit=100€; lot=001
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=5, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # OUT001 qty=3
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=3, price_unit=100)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 2)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_inventory_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, -1)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 100)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        # Inventory adjustment 2 qty=10; lot=001
        inventory = self._create_inventory(
            self.stock_location, self.product_tracking_lot, 10, lot_001)
        move_line_inventory_02 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_02), 1)
        self.assertEqual(move_line_inventory_02.qty_done, 7)
        self.assertEquals(self.product_tracking_lot.with_context(
            location=self.stock_location.id).qty_available, 10)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEqual(self.product_tracking_lot.stock_value, 1000)
        # OUT002 qty=4
        picking_out_02 = self._create_picking(
            'out', self.product_tracking_lot, qty=4, price_unit=100)
        move_lines_out_01 = picking_out_02.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 3))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 100)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_inventory_02)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 100)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)

    def test_stock_ml_rel_product_tracking_lot_fifo_inventory_04(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.assertEqual(self.product_tracking_lot.standard_price, -1.0)
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        # Inventory adjustment 1 qty=1; lot=001
        inventory = self._create_inventory(
            self.stock_location, self.product_tracking_lot, 1, lot_001)
        move_line_inventory_01 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_01), 1)
        self.assertEqual(self.product_tracking_lot.stock_value, -1.0)
        self.assertEqual(self.product_tracking_lot.standard_price, -1.0)
        # IN001 qty=5; price_unit=100€; lot=001
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=5, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # IN002 qty=4; price_unit=200€; lot=002
        lot_002 = self.env['stock.production.lot'].create({
            'name': '002',
            'product_id': self.product_tracking_lot.id,
        })
        picking_in_02 = self._create_picking(
            'in', self.product_tracking_lot, qty=4, price_unit=200,
            lot=lot_002)
        move_line_in_02 = picking_in_02.move_line_ids
        self.assertFalse(move_line_in_02.move_line_relation_ids)
        # OUT001 qty=3
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=3, price_unit=100)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 2)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_inventory_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, -1)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 100)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        # Inventory adjustment 2 qty=10; lot=001
        inventory = self._create_inventory(
            self.stock_location, self.product_tracking_lot, 10, lot_001)
        move_line_inventory_02 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_02), 1)
        self.assertEqual(move_line_inventory_02.qty_done, 7)
        self.assertEquals(self.product_tracking_lot.with_context(
            location=self.stock_location.id, lot_id=lot_001.id).qty_available,
            10)
        self.assertEquals(self.product_tracking_lot.with_context(
            location=self.stock_location.id, lot_id=lot_002.id).qty_available,
            4)
        self.assertEqual(self.product_tracking_lot.standard_price, 100)
        self.assertEqual(self.product_tracking_lot.stock_value, 1800)
        # OUT002 qty=4
        picking_out_02 = self._create_picking(
            'out', self.product_tracking_lot, qty=4, price_unit=100)
        move_lines_out_01 = picking_out_02.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 3))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 100)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_inventory_02)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 100)
        self.assertEqual(self.product_tracking_lot.standard_price, 200)

    def test_stock_ml_rel_product_no_tracking_fifo_inventory_01(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.assertEqual(self.product_no_tracking.standard_price, -1.0)
        # Inventory adjustment qty=1
        inventory = self._create_inventory(
            self.stock_location, self.product_no_tracking, 1)
        move_line_inventory_01 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_01), 1)
        self.assertEqual(self.product_no_tracking.stock_value, -1.0)
        self.assertEqual(self.product_no_tracking.standard_price, -1.0)
        # IN001 qty=5; price_unit=100€
        picking_in_01 = self._create_picking(
            'in', self.product_no_tracking, qty=5, price_unit=100)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # OUT001 qty=1
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=1, price_unit=100)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_inventory_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, -1)

    def test_stock_ml_rel_product_no_tracking_fifo_inventory_02(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.assertEqual(self.product_no_tracking.standard_price, -1.0)
        # Inventory adjustment qty=1
        inventory = self._create_inventory(
            self.stock_location, self.product_no_tracking, 1)
        move_line_inventory_01 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_01), 1)
        self.assertEqual(self.product_no_tracking.stock_value, -1.0)
        self.assertEqual(self.product_no_tracking.standard_price, -1.0)
        # IN001 qty=5; price_unit=100€
        picking_in_01 = self._create_picking(
            'in', self.product_no_tracking, qty=5, price_unit=100)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # OUT001 qty=3
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=3, price_unit=100)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 2)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_inventory_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, -1)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 100)

    def test_stock_ml_rel_product_no_tracking_fifo_inventory_03(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.assertEqual(self.product_no_tracking.standard_price, -1.0)
        # Inventory adjustment 1 qty=1
        inventory = self._create_inventory(
            self.stock_location, self.product_no_tracking, 1)
        move_line_inventory_01 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_01), 1)
        self.assertEqual(self.product_no_tracking.stock_value, -1.0)
        self.assertEqual(self.product_no_tracking.standard_price, -1.0)
        # IN001 qty=5; price_unit=100€
        picking_in_01 = self._create_picking(
            'in', self.product_no_tracking, qty=5, price_unit=100)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # OUT001 qty=3
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=3, price_unit=100)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_inventory_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, -1)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 100)
        self.assertEqual(self.product_no_tracking.standard_price, 100)
        # Inventory adjustment 2 qty=10
        inventory = self._create_inventory(
            self.stock_location, self.product_no_tracking, 10)
        move_line_inventory_02 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_02), 1)
        self.assertEqual(move_line_inventory_02.qty_done, 7)
        self.assertEquals(self.product_no_tracking.with_context(
            location=self.stock_location.id).qty_available, 10)
        self.assertEqual(self.product_no_tracking.standard_price, 100)
        self.assertEqual(self.product_no_tracking.stock_value, 1000)
        # OUT002 qty=4
        picking_out_02 = self._create_picking(
            'out', self.product_no_tracking, qty=4, price_unit=100)
        move_lines_out_01 = picking_out_02.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 3))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 100)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_inventory_02)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 100)
        self.assertEqual(self.product_no_tracking.standard_price, 100)

    def test_stock_ml_rel_product_no_tracking_fifo_inventory_04(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        self.assertEqual(self.product_no_tracking.standard_price, -1.0)
        # Inventory adjustment 1 qty=1
        inventory = self._create_inventory(
            self.stock_location, self.product_no_tracking, 1)
        move_line_inventory_01 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_01), 1)
        self.assertEqual(self.product_no_tracking.stock_value, -1.0)
        self.assertEqual(self.product_no_tracking.standard_price, -1.0)
        # IN001 qty=5; price_unit=100€
        picking_in_01 = self._create_picking(
            'in', self.product_no_tracking, qty=5, price_unit=100)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # IN002 qty=4; price_unit=200€
        picking_in_02 = self._create_picking(
            'in', self.product_no_tracking, qty=4, price_unit=200)
        move_line_in_02 = picking_in_02.move_line_ids
        self.assertFalse(move_line_in_02.move_line_relation_ids)
        # OUT001 qty=3
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=3, price_unit=100)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 2)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_inventory_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, -1)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 100)
        self.assertEqual(self.product_no_tracking.standard_price, 100)
        # Inventory adjustment 2 qty=10
        inventory = self._create_inventory(
            self.stock_location, self.product_no_tracking, 10)
        move_line_inventory_02 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_02), 1)
        self.assertEqual(move_line_inventory_02.qty_done, 3)
        self.assertEquals(self.product_no_tracking.with_context(
            location=self.stock_location.id).qty_available, 10)
        self.assertEqual(self.product_no_tracking.standard_price, 100)
        self.assertEqual(self.product_no_tracking.stock_value, 1400)
        # OUT002 qty=4
        picking_out_02 = self._create_picking(
            'out', self.product_no_tracking, qty=4, price_unit=100)
        move_lines_out_01 = picking_out_02.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 3))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 100)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_02)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 200)
        self.assertEqual(self.product_no_tracking.standard_price, 200)

    def test_stock_ml_rel_product_tracking_lot_fifo_partn_return(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        # Inventory adjustment qty=1; lot=001
        inventory = self._create_inventory(
            self.stock_location, self.product_tracking_lot, 1, lot_001)
        move_line_inventory_01 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_01), 1)
        self.assertEqual(self.product_tracking_lot.stock_value, -1.0)
        self.assertEqual(self.product_tracking_lot.standard_price, -1.0)
        # OUT001 qty=1
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=1, price_unit=100)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_inventory_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, -1)
        # Return OUT001 qty=1 (IN)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_out_01.ids,
            active_id=picking_out_01.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.quantity = 1
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.quantity_done = 1
        return_pick.move_lines.to_refund = True
        return_pick.move_line_ids.lot_id = lot_001.id
        return_pick.action_done()
        time.sleep(1)
        move_line_return_01 = return_pick.move_line_ids
        self.assertEquals(len(move_line_return_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.move_line_id,
            move_line_inventory_01)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.price_unit, -1)
        # OUT002 qty=1
        picking_out_02 = self._create_picking(
            'out', self.product_tracking_lot, qty=1, price_unit=100)
        move_line_out_02 = picking_out_02.move_line_ids
        self.assertEquals(len(move_line_out_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.move_line_id,
            move_line_return_01)
        self.assertEquals(move_line_out_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_02.move_line_relation_ids.price_unit, -1)

    def test_stock_ml_rel_product_tracking_lot_fifo_internal(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        self.assertEqual(self.product_tracking_lot.standard_price, -1.0)
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        # Inventory adjustment qty=1; lot=001
        inventory = self._create_inventory(
            self.stock_location, self.product_tracking_lot, 1, lot_001)
        move_line_inventory_01 = inventory.mapped('move_ids.move_line_ids')
        self.assertEqual(len(move_line_inventory_01), 1)
        self.assertEqual(self.product_tracking_lot.stock_value, -1.0)
        self.assertEqual(self.product_tracking_lot.standard_price, -1.0)
        # IN001 qty=5; price_unit=100€; lot=001
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=5, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # OUT001 qty=1
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=1, price_unit=100)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_inventory_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, -1)
        # INT001 qty=2 Stock=>Ubic interna
        picking_int_01 = self._create_picking(
            'internal', self.product_tracking_lot, qty=2, price_unit=100,
            src_internal_location=self.stock_location,
            dst_internal_location=self.internal_location)
        move_line_int_01 = picking_int_01.move_line_ids
        self.assertEquals(len(move_line_int_01.move_line_relation_ids), 0)
        # INT002 qty=1 Ubic interna=>Stock
        picking_int_02 = self._create_picking(
            'internal', self.product_tracking_lot, qty=1, price_unit=100,
            src_internal_location=self.internal_location,
            dst_internal_location=self.stock_location)
        move_line_int_02 = picking_int_02.move_line_ids
        self.assertEquals(len(move_line_int_02.move_line_relation_ids), 0)

    def test_stock_ml_rel_product_tracking_lot_fifo_return_picking(self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        # IN001 qty=5 lot001
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=5, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # OUT001 qty=1 lot001
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=1, price_unit=100)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 100)
        # Return OUT001 qty=1 (IN)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_out_01.ids,
            active_id=picking_out_01.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.quantity = 1
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.quantity_done = 1
        return_pick.move_lines.to_refund = True
        return_pick.move_line_ids.lot_id = lot_001.id
        return_pick.action_done()
        move_line_return_01 = return_pick.move_line_ids
        self.assertEquals(len(move_line_return_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.price_unit, 100)

    def test_stock_ml_rel_product_no_tracking_fifo_return_picking(self):
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        # IN001 qty=5 lot001
        picking_in_01 = self._create_picking(
            'in', self.product_no_tracking, qty=5, price_unit=100)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # OUT001 qty=1 lot001
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=1, price_unit=100)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 100)
        # Return OUT001 qty=1 (IN)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_out_01.ids,
            active_id=picking_out_01.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.quantity = 1
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.quantity_done = 1
        return_pick.move_lines.to_refund = True
        return_pick.action_done()
        move_line_return_01 = return_pick.move_line_ids
        self.assertEquals(len(move_line_return_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.price_unit, 100)

    def test_stock_ml_rel_product_tracking_lot_fifo_sale_return_one_ml(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'sale_return'),
        ])
        if module.state != 'installed':
            self.skipTest('sale_return module not installed, ignore test')
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        # IN001 qty=5 lot001
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=5, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # OUT001 qty=1 lot001
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=1, price_unit=100)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 100)
        # Return OUT001 qty=1 (IN) with sale_return module
        sale_return = self.env['sale.order'].create({
            'is_return': True,
            'partner_id': self.customer.id,
            'order_line': [(0, 0, {
                'product_id': self.product_tracking_lot.id,
                'product_uom_qty': 1,
            })]
        })
        sale_return.action_confirm()
        self.assertEqual(len(sale_return.picking_ids), 1)
        picking_return = sale_return.picking_ids
        self.assertEqual(
            picking_return.location_id,
            self.env.ref('stock.stock_location_customers'))
        self.assertEqual(
            picking_return.location_dest_id,
            self.env.ref('stock.stock_location_stock'))
        picking_return.action_confirm()
        picking_return.action_assign()
        for move_line in picking_return.move_line_ids:
            move_line.qty_done = move_line.product_uom_qty
            move_line.lot_id = lot_001.id
        picking_return.action_done()
        self.assertEqual(picking_return.state, 'done')
        move_line_return_01 = picking_return.move_line_ids
        self.assertEquals(
            len(move_line_return_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.price_unit, 100)

    def test_stock_ml_rel_product_no_tracking_fifo_sale_return_one_ml(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'sale_return'),
        ])
        if module.state != 'installed':
            self.skipTest('sale_return module not installed, ignore test')
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        # IN001 qty=5
        picking_in_01 = self._create_picking(
            'in', self.product_no_tracking, qty=5, price_unit=100)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # OUT001 qty=1
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=1, price_unit=100)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 100)
        # Return OUT001 qty=1 (IN) with sale_return module
        sale_return = self.env['sale.order'].create({
            'is_return': True,
            'partner_id': self.customer.id,
            'order_line': [(0, 0, {
                'product_id': self.product_no_tracking.id,
                'product_uom_qty': 1,
            })]
        })
        sale_return.action_confirm()
        self.assertEqual(len(sale_return.picking_ids), 1)
        picking_return = sale_return.picking_ids
        self.assertEqual(
            picking_return.location_id,
            self.env.ref('stock.stock_location_customers'))
        self.assertEqual(
            picking_return.location_dest_id,
            self.env.ref('stock.stock_location_stock'))
        picking_return.action_confirm()
        picking_return.action_assign()
        for move_line in picking_return.move_line_ids:
            move_line.qty_done = move_line.product_uom_qty
        picking_return.action_done()
        self.assertEqual(picking_return.state, 'done')
        move_line_return_01 = picking_return.move_line_ids
        self.assertEquals(
            len(move_line_return_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.price_unit, 100)

    def test_stock_ml_rel_product_tracking_lot_fifo_sale_return_several_mls(
            self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'sale_return'),
        ])
        if module.state != 'installed':
            self.skipTest('sale_return module not installed, ignore test')
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        # IN001 qty=1 lot001 price=100
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=1, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # IN002 qty=5 lot001 price=500
        picking_in_02 = self._create_picking(
            'in', self.product_tracking_lot, qty=5, price_unit=500,
            lot=lot_001)
        move_line_in_02 = picking_in_02.move_line_ids
        self.assertFalse(move_line_in_02.move_line_relation_ids)
        # OUT001 qty=3 lot001
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=3, price_unit=100)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 100)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_02)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 500)
        # Return OUT001 qty=1 (IN) with sale_return module
        sale_return = self.env['sale.order'].create({
            'is_return': True,
            'partner_id': self.customer.id,
            'order_line': [(0, 0, {
                'product_id': self.product_tracking_lot.id,
                'product_uom_qty': 1,
            })]
        })
        sale_return.action_confirm()
        self.assertEqual(len(sale_return.picking_ids), 1)
        picking_return = sale_return.picking_ids
        self.assertEqual(
            picking_return.location_id,
            self.env.ref('stock.stock_location_customers'))
        self.assertEqual(
            picking_return.location_dest_id,
            self.env.ref('stock.stock_location_stock'))
        picking_return.action_confirm()
        picking_return.action_assign()
        for move_line in picking_return.move_line_ids:
            move_line.qty_done = move_line.product_uom_qty
            move_line.lot_id = lot_001.id
        picking_return.action_done()
        self.assertEqual(picking_return.state, 'done')
        move_line_return_01 = picking_return.move_line_ids
        self.assertEquals(
            len(move_line_return_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.move_line_id,
            move_line_in_02)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.price_unit, 500)

    def test_stock_ml_rel_product_tracking_lot_fifo_sale_return_multi_price(
            self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'sale_return'),
        ])
        if module.state != 'installed':
            self.skipTest('sale_return module not installed, ignore test')
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        # IN001 qty=1 lot001 price=100
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=1, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # IN002 qty=5 lot001 price=500
        picking_in_02 = self._create_picking(
            'in', self.product_tracking_lot, qty=5, price_unit=500,
            lot=lot_001)
        move_line_in_02 = picking_in_02.move_line_ids
        self.assertFalse(move_line_in_02.move_line_relation_ids)
        # OUT001 qty=3 lot001
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=3, price_unit=100)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 100)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_02)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 500)
        # Return OUT001 qty=2 (IN) with sale_return module
        sale_return = self.env['sale.order'].create({
            'is_return': True,
            'partner_id': self.customer.id,
            'order_line': [(0, 0, {
                'product_id': self.product_tracking_lot.id,
                'product_uom_qty': 2,
            })]
        })
        sale_return.action_confirm()
        self.assertEqual(len(sale_return.picking_ids), 1)
        picking_return = sale_return.picking_ids
        self.assertEqual(
            picking_return.location_id,
            self.env.ref('stock.stock_location_customers'))
        self.assertEqual(
            picking_return.location_dest_id,
            self.env.ref('stock.stock_location_stock'))
        picking_return.action_confirm()
        picking_return.action_assign()
        for move_line in picking_return.move_line_ids:
            move_line.qty_done = move_line.product_uom_qty
            move_line.lot_id = lot_001.id
        picking_return.action_done()
        self.assertEqual(picking_return.state, 'done')
        move_line_return_01 = picking_return.move_line_ids
        relations = move_line_return_01.move_line_relation_ids
        self.assertEquals(len(relations), 1)
        self.assertIn(move_line_in_02, relations.move_line_id)
        self.assertEquals(relations.quantity, 2)
        self.assertEquals(relations.price_unit, 500)

    def test_stock_ml_rel_product_no_tracking_fifo_sale_return_several_mls(
            self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'sale_return'),
        ])
        if module.state != 'installed':
            self.skipTest('sale_return module not installed, ignore test')
        self.product_no_tracking.categ_id.property_cost_method = 'fifo'
        # IN001 qty=1 price=100
        picking_in_01 = self._create_picking(
            'in', self.product_no_tracking, qty=1, price_unit=100)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # IN002 qty=5 price=500
        picking_in_02 = self._create_picking(
            'in', self.product_no_tracking, qty=5, price_unit=500)
        move_line_in_02 = picking_in_02.move_line_ids
        self.assertFalse(move_line_in_02.move_line_relation_ids)
        # OUT001 qty=3
        picking_out_01 = self._create_picking(
            'out', self.product_no_tracking, qty=3, price_unit=100)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01.move_line_relation_ids), 2)
        move_line_out_relation_01_01 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 1))
        self.assertEquals(len(move_line_out_relation_01_01), 1)
        self.assertEquals(
            move_line_out_relation_01_01.move_line_id, move_line_in_01)
        self.assertEquals(move_line_out_relation_01_01.price_unit, 100)
        move_line_out_relation_01_02 = (
            move_lines_out_01.move_line_relation_ids.filtered(
                lambda ml: ml.quantity == 2))
        self.assertEquals(len(move_line_out_relation_01_02), 1)
        self.assertEquals(
            move_line_out_relation_01_02.move_line_id, move_line_in_02)
        self.assertEquals(move_line_out_relation_01_02.price_unit, 500)
        # Return OUT001 qty=1 (IN) with sale_return module
        sale_return = self.env['sale.order'].create({
            'is_return': True,
            'partner_id': self.customer.id,
            'order_line': [(0, 0, {
                'product_id': self.product_no_tracking.id,
                'product_uom_qty': 1,
            })]
        })
        sale_return.action_confirm()
        self.assertEqual(len(sale_return.picking_ids), 1)
        picking_return = sale_return.picking_ids
        self.assertEqual(
            picking_return.location_id,
            self.env.ref('stock.stock_location_customers'))
        self.assertEqual(
            picking_return.location_dest_id,
            self.env.ref('stock.stock_location_stock'))
        picking_return.action_confirm()
        picking_return.action_assign()
        for move_line in picking_return.move_line_ids:
            move_line.qty_done = move_line.product_uom_qty
        picking_return.action_done()
        self.assertEqual(picking_return.state, 'done')
        move_line_return_01 = picking_return.move_line_ids
        self.assertEquals(
            len(move_line_return_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.move_line_id,
            move_line_in_02)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.price_unit, 500)

    def test_stock_ml_rel_product_tracking_lot_fifo_return_pick_several_lots(
            self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        lot_002 = self.env['stock.production.lot'].create({
            'name': '002',
            'product_id': self.product_tracking_lot.id,
        })
        # IN001
        # qty=1 lot001
        # qty=1 lot002
        picking_in_01 = self.env['stock.picking'].create({
            'location_id': self.ref('stock.stock_location_suppliers'),
            'location_dest_id': self.ref('stock.stock_location_stock'),
            'picking_type_id': self.ref('stock.picking_type_in'),
            'move_lines': [
                (0, 0, {
                    'product_id': self.product_tracking_lot.id,
                    'name': self.product_tracking_lot.name,
                    'product_uom': self.product_tracking_lot.uom_id.id,
                    'product_uom_qty': 1,
                    'procure_method': 'make_to_stock',
                    'price_unit': 100,
                    'value': 1 * 100,
                    'state': 'draft',
                }),
                (0, 0, {
                    'product_id': self.product_tracking_lot.id,
                    'name': self.product_tracking_lot.name,
                    'product_uom': self.product_tracking_lot.uom_id.id,
                    'product_uom_qty': 1,
                    'procure_method': 'make_to_stock',
                    'price_unit': 200,
                    'value': 1 * 200,
                    'state': 'draft',
                }),
            ],
        })
        picking_in_01.onchange_picking_type()
        for ml in picking_in_01.move_lines:
            ml.onchange_product_id()
        picking_in_01.action_confirm()
        picking_in_01.action_assign()
        picking_in_01.move_line_ids[0].write({
            'lot_id': lot_001.id,
            'qty_done': 1,
        })
        picking_in_01.move_line_ids[1].write({
            'lot_id': lot_002.id,
            'qty_done': 1,
        })
        picking_in_01.action_done()
        time.sleep(1)
        move_lines_in_01 = picking_in_01.move_line_ids
        self.assertEquals(len(move_lines_in_01), 2)
        move_line_in_01_lot_1 = move_lines_in_01.filtered(
            lambda ml: ml.lot_id == lot_001)
        self.assertEquals(len(move_line_in_01_lot_1), 1)
        move_line_in_01_lot_2 = move_lines_in_01.filtered(
            lambda ml: ml.lot_id == lot_002)
        self.assertEquals(len(move_line_in_01_lot_2), 1)
        self.assertFalse(move_line_in_01_lot_1.move_line_relation_ids)
        self.assertFalse(move_line_in_01_lot_2.move_line_relation_ids)
        # OUT1
        #     qty=1 lot001 => REL con IN1: ml1
        #     qty=1 lot002 => REL con IN1: ml2
        picking_out_01 = self.env['stock.picking'].create({
            'location_id': self.ref('stock.stock_location_stock'),
            'location_dest_id': self.ref('stock.stock_location_customers'),
            'picking_type_id': self.ref('stock.picking_type_out'),
            'move_lines': [
                (0, 0, {
                    'product_id': self.product_tracking_lot.id,
                    'name': self.product_tracking_lot.name,
                    'product_uom': self.product_tracking_lot.uom_id.id,
                    'product_uom_qty': 1,
                    'procure_method': 'make_to_stock',
                    'price_unit': 100,
                    'value': 1 * 100,
                    'state': 'draft',
                }),
                (0, 0, {
                    'product_id': self.product_tracking_lot.id,
                    'name': self.product_tracking_lot.name,
                    'product_uom': self.product_tracking_lot.uom_id.id,
                    'product_uom_qty': 1,
                    'procure_method': 'make_to_stock',
                    'price_unit': 200,
                    'value': 1 * 200,
                    'state': 'draft',
                }),
            ],
        })
        picking_out_01.onchange_picking_type()
        for ml in picking_out_01.move_lines:
            ml.onchange_product_id()
        picking_out_01.action_confirm()
        picking_out_01.action_assign()
        for move_line in picking_out_01.move_line_ids:
            move_line.lot_id = move_line.lot_id.id
            move_line.qty_done = move_line.product_uom_qty
        picking_out_01.action_done()
        time.sleep(1)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01), 2)
        move_line_out_01_lot_1 = move_lines_out_01.filtered(
            lambda ml: ml.lot_id == lot_001)
        self.assertEquals(len(move_line_out_01_lot_1), 1)
        move_line_out_01_lot_2 = move_lines_out_01.filtered(
            lambda ml: ml.lot_id == lot_002)
        self.assertEquals(len(move_line_out_01_lot_2), 1)
        self.assertEquals(
            len(move_line_out_01_lot_1.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01_lot_1.move_line_relation_ids.move_line_id,
            move_line_in_01_lot_1)
        self.assertEquals(
            move_line_out_01_lot_1.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01_lot_1.move_line_relation_ids.price_unit, 100)
        self.assertEquals(
            len(move_line_out_01_lot_2.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01_lot_2.move_line_relation_ids.move_line_id,
            move_line_in_01_lot_2)
        self.assertEquals(
            move_line_out_01_lot_2.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01_lot_2.move_line_relation_ids.price_unit, 200)
        # Return OUT001 qty=1 lot=1 (IN)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_out_01.ids,
            active_id=picking_out_01.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves[0].quantity = 1
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines[0].quantity_done = 1
        return_pick.move_lines[0].to_refund = True
        return_pick.move_line_ids[0].lot_id = lot_001.id
        return_pick.action_done()
        move_line_return_01 = return_pick.move_line_ids[0]
        self.assertEquals(len(move_line_return_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.move_line_id,
            move_line_in_01_lot_1)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.price_unit, 100)

    def test_stock_ml_rel_product_tracking_lot_fifo_return_picking_other_lot(
            self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        # IN001 qty=1 lot001
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=1, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        lot_002 = self.env['stock.production.lot'].create({
            'name': '002',
            'product_id': self.product_tracking_lot.id,
        })
        # IN002 qty=1 lot002
        picking_in_02 = self._create_picking(
            'in', self.product_tracking_lot, qty=1, price_unit=500,
            lot=lot_002)
        move_line_in_02 = picking_in_02.move_line_ids
        self.assertFalse(move_line_in_02.move_line_relation_ids)
        # OUT001 qty=1 lot001
        picking_out_01 = self._create_picking(
            'out', self.product_tracking_lot, qty=1, price_unit=100,
            lot=lot_001)
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEqual(picking_out_01.move_line_ids.lot_id, lot_001)
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 100)
        # Force to simulate without relation (error case picking 2409AS0497
        move_line_out_01.move_line_relation_ids = [(6, 0, [])]
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 0)
        # Return OUT001 qty=1 lot=002 (IN)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_out_01.ids,
            active_id=picking_out_01.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves.quantity = 1
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines.quantity_done = 1
        return_pick.move_lines.to_refund = True
        return_pick.move_line_ids.lot_id = lot_002.id
        return_pick.action_done()
        move_line_return_01 = return_pick.move_line_ids
        self.assertEqual(move_line_return_01.lot_id, lot_002)
        self.assertEquals(len(move_line_return_01.move_line_relation_ids), 0)

    def test_stock_ml_rel_product_tracking_lot_fifo_return_picking_other_lot2(
            self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        # IN001 qty=1 lot001
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=1, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)

        lot_002 = self.env['stock.production.lot'].create({
            'name': '002',
            'product_id': self.product_tracking_lot.id,
        })
        # IN002 qty=1 lot002
        picking_in_02 = self._create_picking(
            'in', self.product_tracking_lot, qty=1, price_unit=200,
            lot=lot_002)
        move_line_in_02 = picking_in_02.move_line_ids
        self.assertFalse(move_line_in_02.move_line_relation_ids)

        lot_003 = self.env['stock.production.lot'].create({
            'name': '003',
            'product_id': self.product_tracking_lot.id,
        })
        # IN003 qty=1 lot003
        picking_in_03 = self._create_picking(
            'in', self.product_tracking_lot, qty=1, price_unit=300,
            lot=lot_003)
        move_line_in_03 = picking_in_03.move_line_ids
        self.assertFalse(move_line_in_03.move_line_relation_ids)
        # OUT001 qty=2
        #     qty=1 lot001 => REL con IN1: ml1
        #     qty=1 lot002 => REL con IN2: ml2
        picking_out_01 = self.env['stock.picking'].create({
            'location_id': self.ref('stock.stock_location_stock'),
            'location_dest_id': self.ref('stock.stock_location_customers'),
            'picking_type_id': self.ref('stock.picking_type_out'),
            'move_lines': [
                (0, 0, {
                    'product_id': self.product_tracking_lot.id,
                    'name': self.product_tracking_lot.name,
                    'product_uom': self.product_tracking_lot.uom_id.id,
                    'product_uom_qty': 2,
                    'procure_method': 'make_to_stock',
                    'price_unit': 100,
                    'value': 2 * 100,
                    'state': 'draft',
                }),
            ],
        })
        picking_out_01.onchange_picking_type()
        for ml in picking_out_01.move_lines:
            ml.onchange_product_id()
        picking_out_01.action_confirm()
        picking_out_01.action_assign()
        self.assertEqual(len(picking_out_01.move_line_ids), 2)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(len(move_lines_out_01), 2)
        move_line_out_01_lot_1 = move_lines_out_01.filtered(
            lambda ml: ml.lot_id == lot_001)
        self.assertEquals(len(move_line_out_01_lot_1), 1)
        move_line_out_01_lot_2 = move_lines_out_01.filtered(
            lambda ml: ml.lot_id == lot_002)
        self.assertEquals(len(move_line_out_01_lot_2), 1)
        for move_line in picking_out_01.move_line_ids:
            move_line.qty_done = move_line.product_uom_qty
        picking_out_01.action_done()
        time.sleep(1)
        move_lines_out_01 = picking_out_01.move_line_ids
        self.assertEquals(move_line_out_01_lot_1.lot_id, lot_001)
        self.assertEquals(move_line_out_01_lot_1.qty_done, 1)
        self.assertEquals(move_line_out_01_lot_2.lot_id, lot_002)
        self.assertEquals(move_line_out_01_lot_2.qty_done, 1)
        self.assertEquals(
            len(move_line_out_01_lot_1.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01_lot_1.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(
            move_line_out_01_lot_1.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01_lot_1.move_line_relation_ids.price_unit, 100)
        self.assertEquals(
            len(move_line_out_01_lot_2.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01_lot_2.move_line_relation_ids.move_line_id,
            move_line_in_02)
        self.assertEquals(
            move_line_out_01_lot_2.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01_lot_2.move_line_relation_ids.price_unit, 200)
        # Return OUT001 different original lot: qty=2 lot=003 (IN)
        return_picking = self.env['stock.return.picking'].with_context(
            active_ids=picking_out_01.ids,
            active_id=picking_out_01.ids[0],
        )
        return_picking = return_picking.create({})
        return_picking.product_return_moves[0].quantity = 2
        action = return_picking.create_returns()
        return_pick = self.env['stock.picking'].browse(action['res_id'])
        return_pick.action_assign()
        return_pick.move_lines[0].quantity_done = 2
        return_pick.move_lines[0].to_refund = True
        return_pick.move_line_ids[0].lot_id = lot_003.id
        return_pick.action_done()
        move_line_return_01 = return_pick.move_line_ids[0]
        self.assertEquals(len(move_line_return_01.move_line_relation_ids), 0)

    def test_stock_ml_rel_product_tracking_lot_fifo_return_picking_backorder2(
            self):
        self.product_tracking_lot.categ_id.property_cost_method = 'fifo'
        lot_001 = self.env['stock.production.lot'].create({
            'name': '001',
            'product_id': self.product_tracking_lot.id,
        })
        # IN001 qty=5 lot001
        picking_in_01 = self._create_picking(
            'in', self.product_tracking_lot, qty=5, price_unit=100,
            lot=lot_001)
        move_line_in_01 = picking_in_01.move_line_ids
        self.assertFalse(move_line_in_01.move_line_relation_ids)
        # OUT001 qty=5 lot001 => partial
        #   OUT001                                      1ud
        #   BACKORDER_OUT001(picking_out_back_01)       4ud => REL IN001
        picking_out_01 = self.env['stock.picking'].create({
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': (
                self.env.ref('stock.stock_location_customers').id),
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product_tracking_lot.id,
                    'name': self.product_tracking_lot.name,
                    'product_uom': self.product_tracking_lot.uom_id.id,
                    'product_uom_qty': 5,
                    'procure_method': 'make_to_stock',
                    'price_unit': 100,
                    'value': 5 * 100,
                    'state': 'draft',
                }),
            ],
        })
        picking_out_01.move_lines.onchange_product_id()
        picking_out_01.action_confirm()
        picking_out_01.action_assign()
        self.assertEqual(len(picking_out_01.move_line_ids), 1)
        picking_out_01.move_lines[0].quantity_done = 1
        res = picking_out_01.button_validate()
        self.assertEqual(res.get('res_model'), 'stock.backorder.confirmation')
        wizard = self.env[(res.get('res_model'))].browse(res.get('res_id'))
        wizard.process()
        time.sleep(1)
        picking_out_back_01 = self.env['stock.picking'].search([
            ('backorder_id', '=', picking_out_01.id),
        ])
        self.assertEqual(picking_out_01.move_lines.product_uom_qty, 1)
        self.assertEqual(picking_out_01.move_line_ids.qty_done, 1)
        self.assertEqual(picking_out_01.state, 'done')
        self.assertEqual(picking_out_back_01.move_lines.product_uom_qty, 4)
        self.assertEqual(picking_out_back_01.move_line_ids.qty_done, 0)
        self.assertEqual(picking_out_back_01.state, 'assigned')
        move_line_out_01 = picking_out_01.move_line_ids
        self.assertEqual(picking_out_01.move_line_ids.lot_id, lot_001)
        self.assertEquals(len(move_line_out_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(move_line_out_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_out_01.move_line_relation_ids.price_unit, 100)
        picking_out_back_01.onchange_picking_type()
        for ml in picking_out_back_01.move_lines:
            ml.onchange_product_id()
        picking_out_back_01.action_confirm()
        picking_out_back_01.action_assign()
        self.assertEqual(len(picking_out_back_01.move_line_ids), 1)
        picking_out_back_01.move_line_ids.qty_done = 4
        picking_out_back_01.move_line_ids.lot_id = lot_001
        picking_out_back_01.action_done()
        time.sleep(1)
        move_lines_out_back_01 = picking_out_back_01.move_line_ids
        self.assertEquals(move_lines_out_back_01.lot_id, lot_001)
        self.assertEquals(move_lines_out_back_01.qty_done, 4)
        self.assertEqual(picking_out_back_01.state, 'done')
        move_line_out_back_01 = picking_out_back_01.move_line_ids
        self.assertEqual(picking_out_back_01.move_line_ids.lot_id, lot_001)
        self.assertEquals(len(move_line_out_back_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_out_back_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(
            move_line_out_back_01.move_line_relation_ids.quantity, 4)
        self.assertEquals(
            move_line_out_back_01.move_line_relation_ids.price_unit, 100)
        # Return picking_out_back_01 qty=1 lot=001 (IN)
        return_picking_1 = self.env['stock.return.picking'].with_context(
            active_ids=picking_out_back_01.ids,
            active_id=picking_out_back_01.ids[0],
        )
        return_picking_1 = return_picking_1.create({})
        return_picking_1.product_return_moves.quantity = 1
        action = return_picking_1.create_returns()
        return_pick_1 = self.env['stock.picking'].browse(action['res_id'])
        return_pick_1.action_assign()
        return_pick_1.move_lines.quantity_done = 1
        return_pick_1.move_lines.to_refund = True
        return_pick_1.move_line_ids.lot_id = lot_001.id
        return_pick_1.action_done()
        time.sleep(1)
        self.assertEqual(return_pick_1.state, 'done')
        move_line_return_01 = return_pick_1.move_line_ids
        self.assertEqual(move_line_return_01.lot_id, lot_001)
        self.assertEquals(len(move_line_return_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.move_line_id,
            move_line_in_01)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_return_01.move_line_relation_ids.price_unit, 100)
        # Return backorder retuned qty=1 lot=001 (OUT)
        return_back_picking = self.env['stock.return.picking'].with_context(
            active_ids=return_pick_1.ids,
            active_id=return_pick_1.ids[0],
        )
        return_back_picking = return_back_picking.create({})
        return_back_picking.product_return_moves.quantity = 1
        action = return_back_picking.create_returns()
        return_pick_2 = self.env['stock.picking'].browse(action['res_id'])
        return_pick_2.action_assign()
        return_pick_2.move_lines.quantity_done = 1
        return_pick_2.move_lines.to_refund = True
        return_pick_2.move_line_ids.lot_id = lot_001.id
        return_pick_2.action_done()
        time.sleep(1)
        move_line_return_02 = return_pick_2.move_line_ids
        self.assertEqual(move_line_return_02.lot_id, lot_001)
        self.assertEquals(len(move_line_return_02.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_return_02.move_line_relation_ids.move_line_id,
            move_line_return_01)
        self.assertEquals(
            move_line_return_02.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_return_02.move_line_relation_ids.price_unit, 100)
        # Return del return qty=1 lot=001 (IN)
        return_return_back_picking = self.env[
            'stock.return.picking'].with_context(
                active_ids=return_pick_2.ids,
                active_id=return_pick_2.ids[0],
        )
        return_return_back_picking = return_return_back_picking.create({})
        return_return_back_picking.product_return_moves.quantity = 1
        action = return_return_back_picking.create_returns()
        return_pick_3 = self.env['stock.picking'].browse(action['res_id'])
        return_pick_3.action_assign()
        return_pick_3.move_lines.quantity_done = 1
        return_pick_3.move_lines.to_refund = True
        return_pick_3.move_line_ids.lot_id = lot_001.id
        return_pick_3.action_done()
        time.sleep(1)
        move_line_return_return_01 = return_pick_3.move_line_ids
        self.assertEqual(move_line_return_return_01.lot_id, lot_001)
        self.assertEquals(
            len(move_line_return_return_01.move_line_relation_ids), 1)
        self.assertEquals(
            move_line_return_return_01.move_line_relation_ids.move_line_id,
            move_line_return_01)
        self.assertEquals(
            move_line_return_return_01.move_line_relation_ids.quantity, 1)
        self.assertEquals(
            move_line_return_return_01.move_line_relation_ids.price_unit, 100)
