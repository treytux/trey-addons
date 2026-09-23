###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestMrpCostPrice(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.leg = self.env['product.product'].create({
            'name': 'Leg',
            'type': 'product',
            'default_code': 'LEG',
            'standard_price': 1,
        })
        self.board = self.env['product.product'].create({
            'name': 'Board ',
            'type': 'product',
            'default_code': 'BOARD',
            'standard_price': 1,
        })
        self.service_01 = self.env['product.product'].create({
            'name': 'Service 01',
            'type': 'service',
            'default_code': 'SERVICE01',
            'standard_price': 1,
        })
        self.service_02 = self.env['product.product'].create({
            'name': 'Service 02',
            'type': 'service',
            'default_code': 'SERVICE02',
            'standard_price': 1,
        })
        self.table = self.env['product.product'].create({
            'name': 'Table',
            'type': 'product',
            'default_code': 'TABLE',
            'standard_price': 1,
        })
        self.bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.table.product_tmpl_id.id,
            'product_id': self.table.id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.leg.id,
                    'product_qty': 4,
                }),
                (0, 0, {
                    'product_id': self.board.id,
                    'product_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.service_01.id,
                    'product_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.service_02.id,
                    'product_qty': 1,
                }),
            ]
        })

    def _create_picking_in(self, product, qty, price_unit):
        stock_location = self.env.ref('stock.stock_location_stock')
        inventory_location = self.env.ref('stock.location_inventory')
        picking = self.env['stock.picking'].create({
            'location_id': inventory_location.id,
            'location_dest_id': stock_location.id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'move_lines': [
                (0, 0, {
                    'product_id': product.id,
                    'name': product.name,
                    'product_uom': product.uom_id.id,
                    'product_uom_qty': qty,
                    'procure_method': 'make_to_stock',
                    'price_unit': price_unit,
                    'value': qty * price_unit,
                }),
            ],
        })
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()

    def _produce(self, mo, qty=0.0):
        produce_wizard = self.env['mrp.product.produce'].with_context({
            'active_id': mo.id,
            'active_ids': [mo.id]
        }).create({
            'product_qty': qty
        })
        produce_wizard._onchange_product_qty()
        produce_wizard.do_produce()
        return True

    def test_mrp_table_cost_method_standard(self):
        self.service_01.standard_price = 25
        self.service_02.standard_price = 75
        self.leg.standard_price = 10
        self.board.standard_price = 50
        self.table.categ_id.property_cost_method = 'standard'
        self._create_picking_in(self.leg, qty=8, price_unit=100)
        self._create_picking_in(self.board, qty=2, price_unit=500)
        self.assertEqual(sum(self.leg.stock_move_ids.mapped('value')), 80)
        self.assertEqual(sum(self.board.stock_move_ids.mapped('value')), 100)
        mo = self.env['mrp.production'].create({
            'product_id': self.table.id,
            'bom_id': self.bom.id,
            'product_qty': 2,
            'product_uom_id': self.table.uom_id.id,
        })
        mo.action_assign()
        self._produce(mo, 2.0)
        self.assertEqual(self.table.standard_price, 1)
        mo.button_mark_done()
        self.assertEqual(self.table.standard_price, 1)
        self.assertEqual(len(mo.move_finished_ids), 1)
        self.assertEqual(mo.move_finished_ids.price_unit, 190)
        self.assertEqual(mo.move_finished_ids.value, 380)
        self.assertEqual(mo.move_finished_ids.remaining_value, 380)
        self.assertEqual(mo.move_finished_ids.remaining_qty, 2)
        raw_leg = mo.move_raw_ids.filtered(lambda p: p.product_id == self.leg)
        self.assertEqual(raw_leg.price_unit, -10)
        self.assertEqual(raw_leg.value, -80)
        self.assertEqual(raw_leg.remaining_value, 0)
        self.assertEqual(raw_leg.remaining_qty, 0)
        raw_board = mo.move_raw_ids.filtered(
            lambda p: p.product_id == self.board)
        self.assertEqual(raw_board.price_unit, -50)
        self.assertEqual(raw_board.value, -100)
        self.assertEqual(raw_board.remaining_value, 0)
        self.assertEqual(raw_board.remaining_qty, 0)
        self._create_picking_in(self.leg, qty=8, price_unit=100)
        self._create_picking_in(self.board, qty=2, price_unit=500)
        self.assertEqual(self.leg.standard_price, 10)
        self.assertEqual(self.board.standard_price, 50)
        mo = self.env['mrp.production'].create({
            'product_id': self.table.id,
            'bom_id': self.bom.id,
            'product_qty': 2,
            'product_uom_id': self.table.uom_id.id,
        })
        mo.action_assign()
        self._produce(mo, 2.0)
        self.assertEqual(self.table.standard_price, 1)
        mo.button_mark_done()
        self.assertEqual(self.table.standard_price, 1)
        self.assertEqual(len(mo.move_finished_ids), 1)
        self.assertEqual(mo.move_finished_ids.price_unit, 190)
        self.assertEqual(mo.move_finished_ids.value, 380)
        self.assertEqual(mo.move_finished_ids.remaining_value, 380)
        self.assertEqual(mo.move_finished_ids.remaining_qty, 2)
        raw_leg = mo.move_raw_ids.filtered(lambda p: p.product_id == self.leg)
        self.assertEqual(raw_leg.price_unit, -10)
        self.assertEqual(raw_leg.value, -80)
        self.assertEqual(raw_leg.remaining_value, 0)
        self.assertEqual(raw_leg.remaining_qty, 0)
        raw_board = mo.move_raw_ids.filtered(
            lambda p: p.product_id == self.board)
        self.assertEqual(raw_board.price_unit, -50)
        self.assertEqual(raw_board.value, -100)
        self.assertEqual(raw_board.remaining_value, 0)
        self.assertEqual(raw_board.remaining_qty, 0)

    def test_mrp_table_cost_method_average(self):
        self.service_01.standard_price = 25
        self.service_02.standard_price = 75
        self.leg.standard_price = 0
        self.board.standard_price = 0
        self.table.categ_id.property_cost_method = 'average'
        self._create_picking_in(self.leg, qty=8, price_unit=10)
        self._create_picking_in(self.board, qty=2, price_unit=50)
        self.assertEqual(sum(self.leg.stock_move_ids.mapped('value')), 80)
        self.assertEqual(sum(self.board.stock_move_ids.mapped('value')), 100)
        self.assertEqual(self.leg.standard_price, 10)
        self.assertEqual(self.board.standard_price, 50)
        mo = self.env['mrp.production'].create({
            'product_id': self.table.id,
            'bom_id': self.bom.id,
            'product_qty': 2,
            'product_uom_id': self.table.uom_id.id,
        })
        mo.action_assign()
        self._produce(mo, 2.0)
        self.assertEqual(self.table.standard_price, 1)
        mo.button_mark_done()
        self.assertEqual(self.table.standard_price, 190)
        self.assertEqual(len(mo.move_finished_ids), 1)
        self.assertEqual(mo.move_finished_ids.price_unit, 190)
        self.assertEqual(mo.move_finished_ids.value, 380)
        self.assertEqual(mo.move_finished_ids.remaining_value, 380)
        self.assertEqual(mo.move_finished_ids.remaining_qty, 2)
        raw_leg = mo.move_raw_ids.filtered(lambda p: p.product_id == self.leg)
        self.assertEqual(raw_leg.price_unit, -10)
        self.assertEqual(raw_leg.value, -80)
        self.assertEqual(raw_leg.remaining_value, 0)
        self.assertEqual(raw_leg.remaining_qty, 0)
        raw_board = mo.move_raw_ids.filtered(
            lambda p: p.product_id == self.board)
        self.assertEqual(raw_board.price_unit, -50)
        self.assertEqual(raw_board.value, -100)
        self.assertEqual(raw_board.remaining_value, 0)
        self.assertEqual(raw_board.remaining_qty, 0)
        self.assertEqual(self.leg.standard_price, 10)
        self.assertEqual(self.board.standard_price, 50)
        self._create_picking_in(self.leg, qty=8, price_unit=100)
        self._create_picking_in(self.board, qty=2, price_unit=500)
        self.assertEqual(self.leg.standard_price, 100)
        self.assertEqual(self.board.standard_price, 500)
        mo = self.env['mrp.production'].create({
            'product_id': self.table.id,
            'bom_id': self.bom.id,
            'product_qty': 2,
            'product_uom_id': self.table.uom_id.id,
        })
        mo.action_assign()
        self._produce(mo, 2.0)
        self.assertEqual(self.table.standard_price, 190)
        mo.button_mark_done()
        self.assertEqual(self.table.standard_price, 595)
        self.assertEqual(len(mo.move_finished_ids), 1)
        self.assertEqual(mo.move_finished_ids.price_unit, 1000)
        self.assertEqual(mo.move_finished_ids.value, 2000)
        self.assertEqual(mo.move_finished_ids.remaining_value, 2000)
        self.assertEqual(mo.move_finished_ids.remaining_qty, 2)
        raw_leg = mo.move_raw_ids.filtered(lambda p: p.product_id == self.leg)
        self.assertEqual(raw_leg.price_unit, -100)
        self.assertEqual(raw_leg.value, -800)
        self.assertEqual(raw_leg.remaining_value, 0)
        self.assertEqual(raw_leg.remaining_qty, 0)
        raw_board = mo.move_raw_ids.filtered(
            lambda p: p.product_id == self.board)
        self.assertEqual(raw_board.price_unit, -500)
        self.assertEqual(raw_board.value, -1000)
        self.assertEqual(raw_board.remaining_value, 0)
        self.assertEqual(raw_board.remaining_qty, 0)

    def test_mrp_table_cost_method_fifo(self):
        self.service_01.standard_price = 25
        self.service_02.standard_price = 75
        self.table.categ_id.property_cost_method = 'fifo'
        self._create_picking_in(self.leg, qty=8, price_unit=10)
        self._create_picking_in(self.board, qty=2, price_unit=50)
        mo = self.env['mrp.production'].create({
            'product_id': self.table.id,
            'bom_id': self.bom.id,
            'product_qty': 2,
            'product_uom_id': self.table.uom_id.id,
        })
        mo.action_assign()
        self._produce(mo, 2.0)
        self.assertEqual(self.table.standard_price, 1)
        mo.button_mark_done()
        self.assertEqual(self.table.standard_price, 190)
        self.assertEqual(len(mo.move_finished_ids), 1)
        self.assertEqual(mo.move_finished_ids.price_unit, 190)
        self.assertEqual(mo.move_finished_ids.value, 380)
        self.assertEqual(mo.move_finished_ids.remaining_value, 380)
        self.assertEqual(mo.move_finished_ids.remaining_qty, 2)
        raw_leg = mo.move_raw_ids.filtered(lambda p: p.product_id == self.leg)
        self.assertEqual(raw_leg.price_unit, -10)
        self.assertEqual(raw_leg.value, -80)
        self.assertEqual(raw_leg.remaining_value, 0)
        self.assertEqual(raw_leg.remaining_qty, 0)
        raw_board = mo.move_raw_ids.filtered(
            lambda p: p.product_id == self.board)
        self.assertEqual(raw_board.price_unit, -50)
        self.assertEqual(raw_board.value, -100)
        self.assertEqual(raw_board.remaining_value, 0)
        self.assertEqual(raw_board.remaining_qty, 0)
        self._create_picking_in(self.leg, qty=8, price_unit=100)
        self._create_picking_in(self.board, qty=2, price_unit=500)
        self.assertEqual(self.leg.standard_price, 10)
        self.assertEqual(self.board.standard_price, 50)
        mo = self.env['mrp.production'].create({
            'product_id': self.table.id,
            'bom_id': self.bom.id,
            'product_qty': 2,
            'product_uom_id': self.table.uom_id.id,
        })
        mo.action_assign()
        self._produce(mo, 2.0)
        self.assertEqual(self.table.standard_price, 190)
        mo.button_mark_done()
        self.assertEqual(self.table.standard_price, 190)
        self.assertEqual(len(mo.move_finished_ids), 1)
        self.assertEqual(mo.move_finished_ids.price_unit, 1000)
        self.assertEqual(mo.move_finished_ids.value, 2000)
        self.assertEqual(mo.move_finished_ids.remaining_value, 2000)
        self.assertEqual(mo.move_finished_ids.remaining_qty, 2)
        raw_leg = mo.move_raw_ids.filtered(lambda p: p.product_id == self.leg)
        self.assertEqual(raw_leg.price_unit, -100)
        self.assertEqual(raw_leg.value, -800)
        self.assertEqual(raw_leg.remaining_value, 0)
        self.assertEqual(raw_leg.remaining_qty, 0)
        raw_board = mo.move_raw_ids.filtered(
            lambda p: p.product_id == self.board)
        self.assertEqual(raw_board.price_unit, -500)
        self.assertEqual(raw_board.value, -1000)
        self.assertEqual(raw_board.remaining_value, 0)
        self.assertEqual(raw_board.remaining_qty, 0)

    def test_mrp_table_partial_mark_done_fifo(self):
        self.service_01.standard_price = 25
        self.service_02.standard_price = 75
        self.table.categ_id.property_cost_method = 'fifo'
        self._create_picking_in(self.leg, qty=8, price_unit=10)
        self._create_picking_in(self.board, qty=2, price_unit=50)
        mo = self.env['mrp.production'].create({
            'product_id': self.table.id,
            'bom_id': self.bom.id,
            'product_qty': 2,
            'product_uom_id': self.table.uom_id.id,
        })
        mo.action_assign()
        self.assertEqual(len(mo.move_raw_ids), 2)
        self.assertEqual(self.table.standard_price, 1)
        self._produce(mo, 1.0)
        self.assertEqual(self.table.standard_price, 1)
        self.assertEqual(len(mo.move_finished_ids), 1)
        self.assertEqual(mo.move_finished_ids[0].state, 'confirmed')
        self.assertEqual(mo.move_finished_ids[0].quantity_done, 1)
        self.assertEqual(mo.move_finished_ids[0].price_unit, 0)
        self.assertEqual(mo.move_finished_ids[0].value, 0)
        self._produce(mo, 1.0)
        self.assertEqual(self.table.standard_price, 1)
        self.assertEqual(len(mo.move_finished_ids), 1)
        self.assertEqual(mo.move_finished_ids[0].state, 'confirmed')
        self.assertEqual(mo.move_finished_ids[0].quantity_done, 2)
        self.assertEqual(mo.move_finished_ids[0].price_unit, 0)
        self.assertEqual(mo.move_finished_ids[0].value, 0)
        mo.button_mark_done()
        self.assertEqual(self.table.standard_price, 190)
        self.assertEqual(len(mo.move_finished_ids), 1)
        self.assertEqual(mo.move_finished_ids.price_unit, 190)
        self.assertEqual(mo.move_finished_ids.value, 380)
        self.assertEqual(mo.move_finished_ids.remaining_value, 380)
        self.assertEqual(mo.move_finished_ids.remaining_qty, 2)
        raw_leg = mo.move_raw_ids.filtered(lambda p: p.product_id == self.leg)
        self.assertEqual(raw_leg.price_unit, -10)
        self.assertEqual(raw_leg.value, -80)
        self.assertEqual(raw_leg.remaining_value, 0)
        self.assertEqual(raw_leg.remaining_qty, 0)
        raw_board = mo.move_raw_ids.filtered(
            lambda p: p.product_id == self.board)
        self.assertEqual(raw_board.price_unit, -50)
        self.assertEqual(raw_board.value, -100)
        self.assertEqual(raw_board.remaining_value, 0)
        self.assertEqual(raw_board.remaining_qty, 0)

    def test_mrp_table_partial_post_inventory_fifo(self):
        self.service_01.standard_price = 25
        self.service_02.standard_price = 75
        self.table.categ_id.property_cost_method = 'fifo'
        self._create_picking_in(self.leg, qty=8, price_unit=10)
        self._create_picking_in(self.board, qty=2, price_unit=50)
        mo = self.env['mrp.production'].create({
            'product_id': self.table.id,
            'bom_id': self.bom.id,
            'product_qty': 2,
            'product_uom_id': self.table.uom_id.id,
        })
        mo.action_assign()
        self.assertEqual(len(mo.move_raw_ids), 2)
        self.assertEqual(self.table.standard_price, 1)
        self._produce(mo, 1.0)
        self.assertEqual(self.table.standard_price, 1)
        self.assertEqual(len(mo.move_finished_ids), 1)
        self.assertEqual(mo.move_finished_ids.state, 'confirmed')
        self.assertEqual(mo.move_finished_ids.quantity_done, 1)
        self.assertEqual(mo.move_finished_ids.price_unit, 0)
        self.assertEqual(mo.move_finished_ids.value, 0)
        self.assertEqual(self.table.standard_price, 1)
        mo.post_inventory()
        self.assertEqual(self.table.standard_price, 190)
        self.assertEqual(len(mo.move_finished_ids), 2)
        self.assertEqual(mo.move_finished_ids[0].state, 'done')
        self.assertEqual(mo.move_finished_ids[0].quantity_done, 1)
        self.assertEqual(mo.move_finished_ids[0].price_unit, 190)
        self.assertEqual(mo.move_finished_ids[0].value, 190)
        self.assertEqual(mo.move_finished_ids[1].state, 'confirmed')
        self.assertEqual(mo.move_finished_ids[1].quantity_done, 0)
        self.assertEqual(mo.move_finished_ids[1].price_unit, 190)
        self.assertEqual(mo.move_finished_ids[1].value, 0)
        self._produce(mo, 1.0)
        mo.post_inventory()
        self.assertEqual(len(mo.move_finished_ids), 2)
        self.assertEqual(mo.move_finished_ids[0].state, 'done')
        self.assertEqual(mo.move_finished_ids[0].quantity_done, 1)
        self.assertEqual(mo.move_finished_ids[0].price_unit, 190)
        self.assertEqual(mo.move_finished_ids[0].value, 190)
        self.assertEqual(mo.move_finished_ids[1].state, 'done')
        self.assertEqual(mo.move_finished_ids[1].quantity_done, 1)
        self.assertEqual(mo.move_finished_ids[1].price_unit, 190)
        self.assertEqual(mo.move_finished_ids[1].value, 190)
        mo.button_mark_done()
        self.assertEqual(len(mo.move_finished_ids), 2)
        self.assertEqual(mo.move_finished_ids[0].state, 'done')
        self.assertEqual(mo.move_finished_ids[0].quantity_done, 1)
        self.assertEqual(mo.move_finished_ids[0].price_unit, 190)
        self.assertEqual(mo.move_finished_ids[0].value, 190)
        self.assertEqual(mo.move_finished_ids[1].state, 'done')
        self.assertEqual(mo.move_finished_ids[1].quantity_done, 1)
        self.assertEqual(mo.move_finished_ids[1].price_unit, 190)
        self.assertEqual(mo.move_finished_ids[1].value, 190)

    def test_compute_cost_with_fifo(self):
        def stock_value(product):
            return sum(product.stock_move_ids.mapped('value'))

        self.service_01.standard_price = 25
        self.service_02.standard_price = 75
        self.table.categ_id.property_cost_method = 'fifo'
        self._create_picking_in(self.leg, qty=8, price_unit=10)
        self._create_picking_in(self.board, qty=2, price_unit=50)
        self.assertEqual(self.leg.standard_price, 1)
        self.assertEqual(self.leg.qty_available, 8)
        self.assertEqual(stock_value(self.leg), 80)
        self._create_picking_in(self.leg, qty=8, price_unit=100)
        self.assertEqual(self.leg.standard_price, 1)
        self.assertEqual(self.leg.qty_available, 16)
        self.assertEqual(stock_value(self.leg), 880)
        self.assertEqual(self.board.standard_price, 1)
        self.assertEqual(self.board.qty_available, 2)
        self.assertEqual(stock_value(self.board), 100)
        self._create_picking_in(self.board, qty=2, price_unit=100)
        self.assertEqual(self.board.standard_price, 1)
        self.assertEqual(self.board.qty_available, 4)
        self.assertEqual(stock_value(self.board), 300)
        mo = self.env['mrp.production'].create({
            'product_id': self.table.id,
            'bom_id': self.bom.id,
            'product_qty': 3,
            'product_uom_id': self.table.uom_id.id,
        })
        mo.action_assign()
        self._produce(mo, 3.0)
        self.assertEqual(self.table.standard_price, 1)
        mo.button_mark_done()
        self.assertEqual(round(self.table.standard_price, 2), 326.67)
        self.assertEqual(self.leg.qty_available, 4)
        self.assertEqual(stock_value(self.leg), 400)
        self.assertEqual(self.leg.standard_price, 100)
        self.assertEqual(self.board.qty_available, 1)
        self.assertEqual(stock_value(self.board), 100)
        self.assertEqual(self.board.standard_price, 100)
        self.assertEqual(self.table.stock_move_ids.value, 980)
        self.assertEqual(
            round(self.table.stock_move_ids.price_unit, 2), 326.67)

    def test_compute_cost_bom_multiple_qty(self):
        def stock_value(product):
            return sum(product.stock_move_ids.mapped('value'))

        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.table.product_tmpl_id.id,
            'product_id': self.table.id,
            'product_qty': 10,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.leg.id,
                    'product_qty': 40,
                }),
                (0, 0, {
                    'product_id': self.board.id,
                    'product_qty': 10,
                }),
                (0, 0, {
                    'product_id': self.service_01.id,
                    'product_qty': 10,
                }),
                (0, 0, {
                    'product_id': self.service_02.id,
                    'product_qty': 10,
                }),
            ]
        })
        self.service_01.standard_price = 25
        self.service_02.standard_price = 75
        self.table.categ_id.property_cost_method = 'fifo'
        self._create_picking_in(self.leg, qty=40, price_unit=10)
        self._create_picking_in(self.board, qty=10, price_unit=50)
        mo = self.env['mrp.production'].create({
            'product_id': self.table.id,
            'bom_id': bom.id,
            'product_qty': 1,
            'product_uom_id': self.table.uom_id.id,
        })
        mo.action_assign()
        self._produce(mo, 1.0)
        self.assertEqual(self.table.standard_price, 1)
        mo.button_mark_done()
        self.assertEqual(round(self.table.standard_price, 2), 190)
        self.assertEqual(self.leg.qty_available, 36)
        self.assertEqual(stock_value(self.leg), 360)
        self.assertEqual(self.leg.standard_price, 10)
        self.assertEqual(self.board.qty_available, 9)
        self.assertEqual(stock_value(self.board), 450)
        self.assertEqual(self.board.standard_price, 50)
        self.assertEqual(self.table.stock_move_ids.value, 190)
        self.assertEqual(
            round(self.table.stock_move_ids.price_unit, 2), 190)
