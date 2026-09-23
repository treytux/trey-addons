###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests import common


class TestMrpUnbuildExtend(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.stock_wh = self.env.ref('stock.warehouse0')
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

    def create_inventory(self, product, location, qty, lot=False):
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
            'prod_lot_id': lot and lot.id or None,
        })
        inventory._action_done()

    def create_lot(self, product):
        return self.env['stock.production.lot'].create({
            'product_id': product.id,
        })

    def _produce(self, mo, qty=0.0, lot=False):
        produce_wizard = self.env['mrp.product.produce'].with_context({
            'active_id': mo.id,
            'active_ids': [mo.id]
        }).create({
            'product_qty': qty,
            'lot_id': lot and lot.id or False,
        })
        produce_wizard._onchange_product_qty()
        produce_wizard.do_produce()
        return True

    def test_unbuild_without_lot_ok(self):
        self.create_inventory(self.leg, self.stock_wh.lot_stock_id, 4)
        self.create_inventory(self.board, self.stock_wh.lot_stock_id, 1)
        mo = self.env['mrp.production'].create({
            'product_id': self.table.id,
            'bom_id': self.bom.id,
            'product_qty': 1,
            'product_uom_id': self.table.uom_id.id,
        })
        mo.action_assign()
        self._produce(mo, 1.0)
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done')
        self.assertEqual(len(mo.move_finished_ids), 1)
        self.assertEqual(self.table.qty_available, 1)
        unbuild = self.env['mrp.unbuild'].create({
            'product_id': self.table.id,
            'bom_id': self.bom.id,
            'product_qty': 1,
            'product_uom_id': self.table.uom_id.id,
        })
        unbuild.action_unbuild()
        self.assertEqual(self.table.qty_available, 0)
        self.assertEqual(self.leg.qty_available, 4)
        self.assertEqual(self.board.qty_available, 1)
        self.assertFalse(
            unbuild.produce_line_ids.filtered(
                lambda m: m.product_id.type == 'service'))
        self.assertTrue(
            unbuild.produce_line_ids.filtered(
                lambda m: m.product_id.type != 'service'))

    def test_unbuild_with_lot_ok(self):
        self.table.tracking = 'lot'
        lot = self.create_lot(self.table)
        self.create_inventory(self.leg, self.stock_wh.lot_stock_id, 4)
        self.create_inventory(self.board, self.stock_wh.lot_stock_id, 1)
        mo = self.env['mrp.production'].create({
            'product_id': self.table.id,
            'bom_id': self.bom.id,
            'product_qty': 1,
            'product_uom_id': self.table.uom_id.id,
        })
        mo.action_assign()
        self._produce(mo, 1.0, lot)
        mo.button_mark_done()
        self.assertEqual(mo.state, 'done')
        self.assertEqual(len(mo.move_finished_ids), 1)
        self.assertEqual(mo.finished_move_line_ids.lot_id, lot)
        self.assertEqual(self.table.with_context(lot=lot).qty_available, 1)
        unbuild = self.env['mrp.unbuild'].create({
            'product_id': self.table.id,
            'bom_id': self.bom.id,
            'product_qty': 1,
            'product_uom_id': self.table.uom_id.id,
            'lot_id': lot.id,
        })
        unbuild.action_unbuild()
        self.assertEqual(self.table.with_context(lot=lot).qty_available, 0)
        self.assertEqual(self.leg.qty_available, 4)
        self.assertEqual(self.board.qty_available, 1)
        self.assertFalse(
            unbuild.produce_line_ids.filtered(
                lambda m: m.product_id.type == 'service'))
        self.assertTrue(
            unbuild.produce_line_ids.filtered(
                lambda m: m.product_id.type != 'service'))

    def test_unbuild_without_lot_not_produced_previously(self):
        unbuild = self.env['mrp.unbuild'].create({
            'product_id': self.table.id,
            'bom_id': self.bom.id,
            'product_qty': 1,
            'product_uom_id': self.table.uom_id.id,
        })
        with self.assertRaises(exceptions.UserError) as result:
            unbuild.action_unbuild()
        self.assertEqual(
            result.exception.name,
            'You cannot unbuild a product that has not been previously '
            'manufactured.'
        )

    def test_unbuild_with_lot_not_produced_previously(self):
        self.table.tracking = 'lot'
        lot = self.create_lot(self.table)
        self.create_inventory(self.table, self.stock_wh.lot_stock_id, 1, lot)
        unbuild = self.env['mrp.unbuild'].create({
            'product_id': self.table.id,
            'bom_id': self.bom.id,
            'product_qty': 1,
            'product_uom_id': self.table.uom_id.id,
            'lot_id': lot.id,
        })
        with self.assertRaises(exceptions.UserError) as result:
            unbuild.action_unbuild()
        self.assertEqual(
            result.exception.name,
            'You cannot unbuild a product with a lot that has not been '
            'previously manufactured.'
        )
