###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests import common


class TestMrpProductionSimulation(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.stock_wh = self.env.ref('stock.warehouse0')
        self.quant_obj = self.env['stock.quant']
        self.buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        self.mrp_route = self.env.ref('mrp.route_warehouse0_manufacture')
        self.table = self.env['product.product'].create({
            'name': 'Test Table',
            'type': 'product',
            'route_ids': [(6, 0, self.mrp_route.ids)],
        })
        self.board = self.env['product.product'].create({
            'name': 'Test Board',
            'type': 'product',
            'route_ids': [(6, 0, self.buy_route.ids)],
        })
        self.leg = self.env['product.product'].create({
            'name': 'Test Leg',
            'type': 'product',
            'route_ids': [(6, 0, self.buy_route.ids)],
        })
        self.bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.table.product_tmpl_id.id,
            'product_id': self.table.id,
            'product_uom_id': self.table.uom_id.id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.board.id,
                    'product_qty': 1,
                    'product_uom_id': self.board.uom_id.id,
                }),
                (0, 0, {
                    'product_id': self.leg.id,
                    'product_qty': 4,
                    'product_uom_id': self.leg.uom_id.id,
                })
            ],
        })

    def update_qty_on_hand(self, product, new_qty):
        self.quant_obj._update_available_quantity(
            product, self.stock_wh.lot_stock_id, new_qty)
        self.board.invalidate_model(['qty_available', 'virtual_available'])
        self.assertEqual(
            product.with_context(
                location_id=self.stock_wh.lot_stock_id.id).qty_available,
            new_qty)

    def test_simulation_from_mrp_production(self):
        qty_available_board = self.quant_obj._get_available_quantity(
            self.board, self.stock_wh.lot_stock_id)
        self.assertEqual(qty_available_board, 0)
        qty_available_leg = self.quant_obj._get_available_quantity(
            self.leg, self.stock_wh.lot_stock_id)
        self.assertEqual(qty_available_leg, 0)
        qty_available_table = self.quant_obj._get_available_quantity(
            self.table, self.stock_wh.lot_stock_id)
        self.assertEqual(qty_available_table, 0)
        mrp_production = self.env['mrp.production'].create({
            'product_id': self.table.id,
            'product_qty': 1,
            'product_uom_id': self.table.uom_id.id,
            'bom_id': self.bom.id,
            'location_src_id': self.stock_wh.lot_stock_id.id,
            'location_dest_id': self.stock_wh.lot_stock_id.id,
        })
        self.assertEqual(mrp_production.bom_id.id, self.bom.id)
        wizard = self.env['wiz.mrp.simulation'].with_context(
            active_id=mrp_production.id,
            active_model='mrp.production'
        ).create({})
        self.assertEqual(wizard.main_product_id, self.table)
        self.assertEqual(wizard.main_qty2produce, 1)
        self.assertEqual(len(wizard.line_ids), 2)
        line_board = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.board)
        self.assertEqual(len(line_board), 1)
        self.assertEqual(line_board.product_id, self.board)
        self.assertEqual(line_board.level, 1)
        self.assertEqual(line_board.quantity, 1)
        self.assertEqual(line_board.qty_available, 0)
        self.assertEqual(line_board.virtual_available, 0)
        self.assertEqual(line_board.qty_pending_buy, 1)
        self.assertEqual(line_board.qty_pending_produce, 0)
        self.assertEqual(line_board.product_route, 'buy')
        line_leg = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.leg)
        self.assertEqual(len(line_leg), 1)
        self.assertEqual(line_leg.product_id, self.leg)
        self.assertEqual(line_leg.level, 1)
        self.assertEqual(line_leg.quantity, 4)
        self.assertEqual(line_leg.qty_available, 0)
        self.assertEqual(line_leg.virtual_available, 0)
        self.assertEqual(line_leg.qty_pending_buy, 4)
        self.assertEqual(line_leg.qty_pending_produce, 0)
        self.assertEqual(line_leg.product_route, 'buy')
        self.update_qty_on_hand(self.board, 10)
        self.update_qty_on_hand(self.leg, 20)
        qty_available_board = self.board.with_context(
            location_id=self.stock_wh.lot_stock_id.id).qty_available
        self.assertEqual(qty_available_board, 10)
        qty_available_leg = self.leg.with_context(
            location_id=self.stock_wh.lot_stock_id.id).qty_available
        self.assertEqual(qty_available_leg, 20)
        wizard = self.env['wiz.mrp.simulation'].with_context(
            active_id=mrp_production.id,
            active_model='mrp.production'
        ).create({})
        self.assertEqual(wizard.main_product_id, self.table)
        self.assertEqual(wizard.main_qty2produce, 1)
        self.assertEqual(len(wizard.line_ids), 2)
        line_board = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.board)
        self.assertEqual(len(line_board), 1)
        self.assertEqual(line_board.product_id, self.board)
        self.assertEqual(line_board.level, 1)
        self.assertEqual(line_board.quantity, 1)
        self.assertEqual(line_board.qty_available, 10)
        self.assertEqual(line_board.virtual_available, 10)
        self.assertEqual(line_board.qty_pending_buy, 0)
        self.assertEqual(line_board.qty_pending_produce, 0)
        self.assertEqual(line_board.product_route, 'buy')
        line_leg = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.leg)
        self.assertEqual(len(line_leg), 1)
        self.assertEqual(line_leg.product_id, self.leg)
        self.assertEqual(line_leg.level, 1)
        self.assertEqual(line_leg.quantity, 4)
        self.assertEqual(line_leg.qty_available, 20)
        self.assertEqual(line_leg.virtual_available, 20)
        self.assertEqual(line_leg.qty_pending_buy, 0)
        self.assertEqual(line_leg.qty_pending_produce, 0)
        self.assertEqual(line_leg.product_route, 'buy')

    def test_simulation_from_mrp_production_multiple_qty_produced(self):
        qty_available_board = self.quant_obj._get_available_quantity(
            self.board, self.stock_wh.lot_stock_id)
        self.assertEqual(qty_available_board, 0)
        qty_available_leg = self.quant_obj._get_available_quantity(
            self.leg, self.stock_wh.lot_stock_id)
        self.assertEqual(qty_available_leg, 0)
        qty_available_table = self.quant_obj._get_available_quantity(
            self.table, self.stock_wh.lot_stock_id)
        self.assertEqual(qty_available_table, 0)
        mrp_production = self.env['mrp.production'].create({
            'product_id': self.table.id,
            'product_qty': 2,
            'product_uom_id': self.table.uom_id.id,
            'bom_id': self.bom.id,
            'location_src_id': self.stock_wh.lot_stock_id.id,
            'location_dest_id': self.stock_wh.lot_stock_id.id,
        })
        self.assertEqual(mrp_production.bom_id.id, self.bom.id)
        wizard = self.env['wiz.mrp.simulation'].with_context(
            active_id=mrp_production.id,
            active_model='mrp.production'
        ).create({})
        self.assertEqual(wizard.main_product_id, self.table)
        self.assertEqual(wizard.main_qty2produce, 2)
        self.assertEqual(len(wizard.line_ids), 2)
        line_board = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.board)
        self.assertEqual(len(line_board), 1)
        self.assertEqual(line_board.product_id, self.board)
        self.assertEqual(line_board.level, 1)
        self.assertEqual(line_board.quantity, 2)
        self.assertEqual(line_board.qty_available, 0)
        self.assertEqual(line_board.virtual_available, 0)
        self.assertEqual(line_board.qty_pending_buy, 2)
        self.assertEqual(line_board.qty_pending_produce, 0)
        self.assertEqual(line_board.product_route, 'buy')
        line_leg = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.leg)
        self.assertEqual(len(line_leg), 1)
        self.assertEqual(line_leg.product_id, self.leg)
        self.assertEqual(line_leg.level, 1)
        self.assertEqual(line_leg.quantity, 8)
        self.assertEqual(line_leg.qty_available, 0)
        self.assertEqual(line_leg.virtual_available, 0)
        self.assertEqual(line_leg.qty_pending_buy, 8)
        self.assertEqual(line_leg.qty_pending_produce, 0)
        self.assertEqual(line_leg.product_route, 'buy')
        self.update_qty_on_hand(self.board, 10)
        self.update_qty_on_hand(self.leg, 20)
        qty_available_board = self.board.with_context(
            location_id=self.stock_wh.lot_stock_id.id).qty_available
        self.assertEqual(qty_available_board, 10)
        qty_available_leg = self.leg.with_context(
            location_id=self.stock_wh.lot_stock_id.id).qty_available
        self.assertEqual(qty_available_leg, 20)
        wizard = self.env['wiz.mrp.simulation'].with_context(
            active_id=mrp_production.id,
            active_model='mrp.production'
        ).create({})
        self.assertEqual(wizard.main_product_id, self.table)
        self.assertEqual(wizard.main_qty2produce, 2)
        self.assertEqual(len(wizard.line_ids), 2)
        line_board = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.board)
        self.assertEqual(len(line_board), 1)
        self.assertEqual(line_board.product_id, self.board)
        self.assertEqual(line_board.level, 1)
        self.assertEqual(line_board.quantity, 2)
        self.assertEqual(line_board.qty_available, 10)
        self.assertEqual(line_board.virtual_available, 10)
        self.assertEqual(line_board.qty_pending_buy, 0)
        self.assertEqual(line_board.qty_pending_produce, 0)
        self.assertEqual(line_board.product_route, 'buy')
        line_leg = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.leg)
        self.assertEqual(len(line_leg), 1)
        self.assertEqual(line_leg.product_id, self.leg)
        self.assertEqual(line_leg.level, 1)
        self.assertEqual(line_leg.quantity, 8)
        self.assertEqual(line_leg.qty_available, 20)
        self.assertEqual(line_leg.virtual_available, 20)
        self.assertEqual(line_leg.qty_pending_buy, 0)
        self.assertEqual(line_leg.qty_pending_produce, 0)
        self.assertEqual(line_leg.product_route, 'buy')

    def test_simulation_from_mrp_production_mrp_nested(self):
        self.board.route_ids = [(6, 0, self.mrp_route.ids)]
        half_board = self.env['product.product'].create({
            'name': 'Test half board',
            'type': 'product',
            'route_ids': [(6, 0, self.buy_route.ids)],
        })
        self.env['mrp.bom'].create({
            'product_tmpl_id': self.board.product_tmpl_id.id,
            'product_id': self.board.id,
            'product_uom_id': self.board.uom_id.id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': half_board.id,
                    'product_qty': 2,
                    'product_uom_id': half_board.uom_id.id,
                }),
            ],
        })
        qty_available_board = self.quant_obj._get_available_quantity(
            self.board, self.stock_wh.lot_stock_id)
        self.assertEqual(qty_available_board, 0)
        qty_available_half_board = self.quant_obj._get_available_quantity(
            half_board, self.stock_wh.lot_stock_id)
        self.assertEqual(qty_available_half_board, 0)
        qty_available_leg = self.quant_obj._get_available_quantity(
            self.leg, self.stock_wh.lot_stock_id)
        self.assertEqual(qty_available_leg, 0)
        qty_available_table = self.quant_obj._get_available_quantity(
            self.table, self.stock_wh.lot_stock_id)
        self.assertEqual(qty_available_table, 0)
        mrp_production = self.env['mrp.production'].create({
            'product_id': self.table.id,
            'product_qty': 1,
            'product_uom_id': self.table.uom_id.id,
            'bom_id': self.bom.id,
            'location_src_id': self.stock_wh.lot_stock_id.id,
            'location_dest_id': self.stock_wh.lot_stock_id.id,
        })
        self.assertEqual(mrp_production.bom_id.id, self.bom.id)
        wizard = self.env['wiz.mrp.simulation'].with_context(
            active_id=mrp_production.id,
            active_model='mrp.production'
        ).create({})
        self.assertEqual(wizard.main_product_id, self.table)
        self.assertEqual(wizard.main_qty2produce, 1)
        self.assertEqual(len(wizard.line_ids), 3)
        line_board = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.board)
        self.assertEqual(len(line_board), 1)
        self.assertEqual(line_board.product_id, self.board)
        self.assertEqual(line_board.level, 1)
        self.assertEqual(line_board.quantity, 1)
        self.assertEqual(line_board.qty_available, 0)
        self.assertEqual(line_board.virtual_available, 0)
        self.assertEqual(line_board.qty_pending_buy, 0)
        self.assertEqual(line_board.qty_pending_produce, 1)
        self.assertEqual(line_board.product_route, 'manufacture')
        line_half_board = wizard.line_ids.filtered(
            lambda ln: ln.product_id == half_board)
        self.assertEqual(len(line_half_board), 1)
        self.assertEqual(line_half_board.product_id, half_board)
        self.assertEqual(line_half_board.level, 2)
        self.assertEqual(line_half_board.quantity, 2)
        self.assertEqual(line_half_board.qty_available, 0)
        self.assertEqual(line_half_board.virtual_available, 0)
        self.assertEqual(line_half_board.qty_pending_buy, 2)
        self.assertEqual(line_half_board.qty_pending_produce, 0)
        self.assertEqual(line_half_board.product_route, 'buy')
        line_leg = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.leg)
        self.assertEqual(len(line_leg), 1)
        self.assertEqual(line_leg.product_id, self.leg)
        self.assertEqual(line_leg.level, 1)
        self.assertEqual(line_leg.quantity, 4)
        self.assertEqual(line_leg.qty_available, 0)
        self.assertEqual(line_leg.virtual_available, 0)
        self.assertEqual(line_leg.qty_pending_buy, 4)
        self.assertEqual(line_leg.qty_pending_produce, 0)
        self.assertEqual(line_leg.product_route, 'buy')
        self.update_qty_on_hand(half_board, 10)
        self.update_qty_on_hand(self.leg, 20)
        qty_available_board = half_board.with_context(
            location_id=self.stock_wh.lot_stock_id.id).qty_available
        self.assertEqual(qty_available_board, 10)
        qty_available_leg = self.leg.with_context(
            location_id=self.stock_wh.lot_stock_id.id).qty_available
        self.assertEqual(qty_available_leg, 20)
        qty_available_table = self.table.with_context(
            location_id=self.stock_wh.lot_stock_id.id).qty_available
        self.assertEqual(qty_available_table, 0)
        mrp_production_2 = self.env['mrp.production'].create({
            'product_id': self.table.id,
            'product_qty': 1,
            'product_uom_id': self.table.uom_id.id,
            'bom_id': self.bom.id,
            'location_src_id': self.stock_wh.lot_stock_id.id,
            'location_dest_id': self.stock_wh.lot_stock_id.id,
        })
        self.assertEqual(mrp_production_2.bom_id.id, self.bom.id)
        wizard = self.env['wiz.mrp.simulation'].with_context(
            active_id=mrp_production_2.id,
            active_model='mrp.production'
        ).create({})
        self.assertEqual(wizard.main_product_id, self.table)
        self.assertEqual(wizard.main_qty2produce, 1)
        self.assertEqual(len(wizard.line_ids), 3)
        line_board = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.board)
        self.assertEqual(len(line_board), 1)
        self.assertEqual(line_board.product_id, self.board)
        self.assertEqual(line_board.level, 1)
        self.assertEqual(line_board.quantity, 1)
        self.assertEqual(line_board.qty_available, 0)
        self.assertEqual(line_board.virtual_available, 0)
        self.assertEqual(line_board.qty_pending_buy, 0)
        self.assertEqual(line_board.qty_pending_produce, 1)
        self.assertEqual(line_board.product_route, 'manufacture')
        line_half_board = wizard.line_ids.filtered(
            lambda ln: ln.product_id == half_board)
        self.assertEqual(len(line_half_board), 1)
        self.assertEqual(line_half_board.product_id, half_board)
        self.assertEqual(line_half_board.level, 2)
        self.assertEqual(line_half_board.quantity, 2)
        self.assertEqual(line_half_board.qty_available, 10)
        self.assertEqual(line_half_board.virtual_available, 10)
        self.assertEqual(line_half_board.qty_pending_buy, 0)
        self.assertEqual(line_half_board.qty_pending_produce, 0)
        self.assertEqual(line_half_board.product_route, 'buy')
        line_leg = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.leg)
        self.assertEqual(len(line_leg), 1)
        self.assertEqual(line_leg.product_id, self.leg)
        self.assertEqual(line_leg.level, 1)
        self.assertEqual(line_leg.quantity, 4)
        self.assertEqual(line_leg.qty_available, 20)
        self.assertEqual(line_leg.virtual_available, 20)
        self.assertEqual(line_leg.qty_pending_buy, 0)
        self.assertEqual(line_leg.qty_pending_produce, 0)
        self.assertEqual(line_leg.product_route, 'buy')

    def test_simulation_from_mrp_bom(self):
        qty_available_board = self.quant_obj._get_available_quantity(
            self.board, self.stock_wh.lot_stock_id)
        self.assertEqual(qty_available_board, 0)
        qty_available_leg = self.quant_obj._get_available_quantity(
            self.leg, self.stock_wh.lot_stock_id)
        self.assertEqual(qty_available_leg, 0)
        qty_available_table = self.quant_obj._get_available_quantity(
            self.table, self.stock_wh.lot_stock_id)
        self.assertEqual(qty_available_table, 0)
        wizard = self.env['wiz.mrp.simulation'].with_context(
            active_id=self.bom.id,
            active_model='mrp.bom'
        ).create({})
        self.assertEqual(wizard.main_product_id, self.table)
        self.assertEqual(wizard.main_qty2produce, 1)
        self.assertEqual(len(wizard.line_ids), 2)
        line_board = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.board)
        self.assertEqual(len(line_board), 1)
        self.assertEqual(line_board.product_id, self.board)
        self.assertEqual(line_board.level, 1)
        self.assertEqual(line_board.quantity, 1)
        self.assertEqual(line_board.qty_available, 0)
        self.assertEqual(line_board.virtual_available, 0)
        self.assertEqual(line_board.qty_pending_buy, 1)
        self.assertEqual(line_board.qty_pending_produce, 0)
        self.assertEqual(line_board.product_route, 'buy')
        line_leg = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.leg)
        self.assertEqual(len(line_leg), 1)
        self.assertEqual(line_leg.product_id, self.leg)
        self.assertEqual(line_leg.level, 1)
        self.assertEqual(line_leg.quantity, 4)
        self.assertEqual(line_leg.qty_available, 0)
        self.assertEqual(line_leg.virtual_available, 0)
        self.assertEqual(line_leg.qty_pending_buy, 4)
        self.assertEqual(line_leg.qty_pending_produce, 0)
        self.assertEqual(line_leg.product_route, 'buy')
        self.update_qty_on_hand(self.board, 10)
        self.update_qty_on_hand(self.leg, 20)
        qty_available_board = self.board.with_context(
            location_id=self.stock_wh.lot_stock_id.id).qty_available
        self.assertEqual(qty_available_board, 10)
        qty_available_leg = self.leg.with_context(
            location_id=self.stock_wh.lot_stock_id.id).qty_available
        self.assertEqual(qty_available_leg, 20)
        wizard = self.env['wiz.mrp.simulation'].with_context(
            active_id=self.bom.id,
            active_model='mrp.bom'
        ).create({})
        self.assertEqual(wizard.main_product_id, self.table)
        self.assertEqual(wizard.main_qty2produce, 1)
        self.assertEqual(len(wizard.line_ids), 2)
        line_board = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.board)
        self.assertEqual(len(line_board), 1)
        self.assertEqual(line_board.product_id, self.board)
        self.assertEqual(line_board.level, 1)
        self.assertEqual(line_board.quantity, 1)
        self.assertEqual(line_board.qty_available, 10)
        self.assertEqual(line_board.virtual_available, 10)
        self.assertEqual(line_board.qty_pending_buy, 0)
        self.assertEqual(line_board.qty_pending_produce, 0)
        self.assertEqual(line_board.product_route, 'buy')
        line_leg = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.leg)
        self.assertEqual(len(line_leg), 1)
        self.assertEqual(line_leg.product_id, self.leg)
        self.assertEqual(line_leg.level, 1)
        self.assertEqual(line_leg.quantity, 4)
        self.assertEqual(line_leg.qty_available, 20)
        self.assertEqual(line_leg.virtual_available, 20)
        self.assertEqual(line_leg.qty_pending_buy, 0)
        self.assertEqual(line_leg.qty_pending_produce, 0)
        self.assertEqual(line_leg.product_route, 'buy')

    def test_simulation_from_mrp_bom_mrp_nested(self):
        self.board.route_ids = [(6, 0, self.mrp_route.ids)]
        half_board = self.env['product.product'].create({
            'name': 'Test half board',
            'type': 'product',
            'route_ids': [(6, 0, self.buy_route.ids)],
        })
        self.env['mrp.bom'].create({
            'product_tmpl_id': self.board.product_tmpl_id.id,
            'product_id': self.board.id,
            'product_uom_id': self.board.uom_id.id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': half_board.id,
                    'product_qty': 2,
                    'product_uom_id': half_board.uom_id.id,
                }),
            ],
        })
        qty_available_board = self.quant_obj._get_available_quantity(
            self.board, self.stock_wh.lot_stock_id)
        self.assertEqual(qty_available_board, 0)
        qty_available_half_board = self.quant_obj._get_available_quantity(
            half_board, self.stock_wh.lot_stock_id)
        self.assertEqual(qty_available_half_board, 0)
        qty_available_leg = self.quant_obj._get_available_quantity(
            self.leg, self.stock_wh.lot_stock_id)
        self.assertEqual(qty_available_leg, 0)
        qty_available_table = self.quant_obj._get_available_quantity(
            self.table, self.stock_wh.lot_stock_id)
        self.assertEqual(qty_available_table, 0)
        wizard = self.env['wiz.mrp.simulation'].with_context(
            active_id=self.bom.id,
            active_model='mrp.bom'
        ).create({})
        self.assertEqual(wizard.main_product_id, self.table)
        self.assertEqual(wizard.main_qty2produce, 1)
        self.assertEqual(len(wizard.line_ids), 3)
        line_board = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.board)
        self.assertEqual(len(line_board), 1)
        self.assertEqual(line_board.product_id, self.board)
        self.assertEqual(line_board.level, 1)
        self.assertEqual(line_board.quantity, 1)
        self.assertEqual(line_board.qty_available, 0)
        self.assertEqual(line_board.virtual_available, 0)
        self.assertEqual(line_board.qty_pending_buy, 0)
        self.assertEqual(line_board.qty_pending_produce, 1)
        self.assertEqual(line_board.product_route, 'manufacture')
        line_half_board = wizard.line_ids.filtered(
            lambda ln: ln.product_id == half_board)
        self.assertEqual(len(line_half_board), 1)
        self.assertEqual(line_half_board.product_id, half_board)
        self.assertEqual(line_half_board.level, 2)
        self.assertEqual(line_half_board.quantity, 2)
        self.assertEqual(line_half_board.qty_available, 0)
        self.assertEqual(line_half_board.virtual_available, 0)
        self.assertEqual(line_half_board.qty_pending_buy, 2)
        self.assertEqual(line_half_board.qty_pending_produce, 0)
        self.assertEqual(line_half_board.product_route, 'buy')
        line_leg = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.leg)
        self.assertEqual(len(line_leg), 1)
        self.assertEqual(line_leg.product_id, self.leg)
        self.assertEqual(line_leg.level, 1)
        self.assertEqual(line_leg.quantity, 4)
        self.assertEqual(line_leg.qty_available, 0)
        self.assertEqual(line_leg.virtual_available, 0)
        self.assertEqual(line_leg.qty_pending_buy, 4)
        self.assertEqual(line_leg.qty_pending_produce, 0)
        self.assertEqual(line_leg.product_route, 'buy')
        self.update_qty_on_hand(half_board, 10)
        self.update_qty_on_hand(self.leg, 20)
        qty_available_board = half_board.with_context(
            location_id=self.stock_wh.lot_stock_id.id).qty_available
        self.assertEqual(qty_available_board, 10)
        qty_available_leg = self.leg.with_context(
            location_id=self.stock_wh.lot_stock_id.id).qty_available
        self.assertEqual(qty_available_leg, 20)
        qty_available_table = self.table.with_context(
            location_id=self.stock_wh.lot_stock_id.id).qty_available
        self.assertEqual(qty_available_table, 0)
        wizard = self.env['wiz.mrp.simulation'].with_context(
            active_id=self.bom.id,
            active_model='mrp.bom'
        ).create({})
        self.assertEqual(wizard.main_product_id, self.table)
        self.assertEqual(wizard.main_qty2produce, 1)
        self.assertEqual(len(wizard.line_ids), 3)
        line_board = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.board)
        self.assertEqual(len(line_board), 1)
        self.assertEqual(line_board.product_id, self.board)
        self.assertEqual(line_board.level, 1)
        self.assertEqual(line_board.quantity, 1)
        self.assertEqual(line_board.qty_available, 0)
        self.assertEqual(line_board.virtual_available, 0)
        self.assertEqual(line_board.qty_pending_buy, 0)
        self.assertEqual(line_board.qty_pending_produce, 1)
        self.assertEqual(line_board.product_route, 'manufacture')
        line_half_board = wizard.line_ids.filtered(
            lambda ln: ln.product_id == half_board)
        self.assertEqual(len(line_half_board), 1)
        self.assertEqual(line_half_board.product_id, half_board)
        self.assertEqual(line_half_board.level, 2)
        self.assertEqual(line_half_board.quantity, 2)
        self.assertEqual(line_half_board.qty_available, 10)
        self.assertEqual(line_half_board.virtual_available, 10)
        self.assertEqual(line_half_board.qty_pending_buy, 0)
        self.assertEqual(line_half_board.qty_pending_produce, 0)
        self.assertEqual(line_half_board.product_route, 'buy')
        line_leg = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.leg)
        self.assertEqual(len(line_leg), 1)
        self.assertEqual(line_leg.product_id, self.leg)
        self.assertEqual(line_leg.level, 1)
        self.assertEqual(line_leg.quantity, 4)
        self.assertEqual(line_leg.qty_available, 20)
        self.assertEqual(line_leg.virtual_available, 20)
        self.assertEqual(line_leg.qty_pending_buy, 0)
        self.assertEqual(line_leg.qty_pending_produce, 0)
        self.assertEqual(line_leg.product_route, 'buy')

    def test_raise_model_not_contempled(self):
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        purchase = self.env['purchase.order'].create({
            'partner_id': partner.id,
        })
        with self.assertRaises(ValidationError) as result:
            self.env['wiz.mrp.simulation'].with_context(
                active_id=purchase.id,
                active_model='purchase.order'
            ).create({})
        self.assertEqual(
            'Model purchase.order not contemplated!', result.exception.args[0])

    def test_raise_mrp_production_has_not_defined_any_bom(self):
        self.bom.unlink()
        self.assertFalse(self.table.bom_ids)
        mrp_production = self.env['mrp.production'].create({
            'product_id': self.table.id,
            'product_qty': 1,
            'product_uom_id': self.table.uom_id.id,
            'location_src_id': self.stock_wh.lot_stock_id.id,
            'location_dest_id': self.stock_wh.lot_stock_id.id,
        })
        with self.assertRaises(ValidationError) as result:
            self.env['wiz.mrp.simulation'].with_context(
                active_id=mrp_production.id,
                active_model='mrp.production'
            ).create({})
        self.assertEqual(
            'Mrp production mrp.production has not defined any bill of '
            'materials. You must assign it!', result.exception.args[0])

    def test_raise_product_has_not_defined_any_bom(self):
        table_02 = self.env['product.product'].create({
            'name': 'Test Table 2',
            'type': 'product',
            'route_ids': [(6, 0, self.mrp_route.ids)],
        })
        new_bom = self.env['mrp.bom'].create({
            'product_tmpl_id': table_02.product_tmpl_id.id,
            'product_id': table_02.id,
            'product_uom_id': table_02.uom_id.id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.board.id,
                    'product_qty': 1,
                    'product_uom_id': self.board.uom_id.id,
                }),
                (0, 0, {
                    'product_id': self.leg.id,
                    'product_qty': 1,
                    'product_uom_id': self.leg.uom_id.id,
                })
            ],
        })
        self.table.bom_ids = [(4, new_bom.id)]
        self.assertEqual(len(self.table.bom_ids), 2)
        mrp_production = self.env['mrp.production'].create({
            'product_id': table_02.id,
            'product_qty': 1,
            'product_uom_id': table_02.uom_id.id,
            'bom_id': new_bom.id,
            'location_src_id': self.stock_wh.lot_stock_id.id,
            'location_dest_id': self.stock_wh.lot_stock_id.id,
        })
        with self.assertRaises(ValidationError) as result:
            self.env['wiz.mrp.simulation'].with_context(
                active_id=mrp_production.id,
                active_model='mrp.production'
            ).create({})
        self.assertEqual(
            'Product Test Table 2 has not defined any bill of materials. '
            'You must assign it!', result.exception.args[0])

    def test_raise_bom_not_belong_product(self):
        table_02 = self.env['product.product'].create({
            'name': 'Test Table 2',
            'type': 'product',
            'route_ids': [(6, 0, self.mrp_route.ids)],
        })
        new_bom_01 = self.env['mrp.bom'].create({
            'product_tmpl_id': table_02.product_tmpl_id.id,
            'product_id': table_02.id,
            'product_uom_id': table_02.uom_id.id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.board.id,
                    'product_qty': 1,
                    'product_uom_id': self.board.uom_id.id,
                }),
                (0, 0, {
                    'product_id': self.leg.id,
                    'product_qty': 1,
                    'product_uom_id': self.leg.uom_id.id,
                })
            ],
        })
        table_02.bom_ids = [(4, new_bom_01.id)]
        new_bom_02 = new_bom_01.copy()
        table_02.bom_ids = [(4, new_bom_02.id)]
        new_bom_03 = new_bom_01.copy({
            'product_tmpl_id': self.table.product_tmpl_id.id,
            'product_id': self.table.id,
        })
        self.assertEqual(len(table_02.bom_ids), 2)
        mrp_production = self.env['mrp.production'].create({
            'product_id': table_02.id,
            'product_qty': 1,
            'product_uom_id': table_02.uom_id.id,
            'bom_id': new_bom_03.id,
            'location_src_id': self.stock_wh.lot_stock_id.id,
            'location_dest_id': self.stock_wh.lot_stock_id.id,
        })
        with self.assertRaises(ValidationError) as result:
            self.env['wiz.mrp.simulation'].with_context(
                active_id=mrp_production.id,
                active_model='mrp.production'
            ).create({})
        self.assertEqual(
            'The bill of material selected in the manufacturing order %s does '
            'not belong to any of those defined for the product to be '
            'manufactured Test Table 2.' % (mrp_production.name),
            result.exception.args[0])
