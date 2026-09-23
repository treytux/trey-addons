###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests import common


class TestProductUseManagement(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.qc_test = self.env.ref('quality_control.qc_test_1')
        self.val_ok = self.env.ref('quality_control.qc_test_question_value_1')
        self.val_ko = self.env.ref('quality_control.qc_test_question_value_2')
        self.qc_trigger = self.env['qc.trigger'].create({
            'name': 'Test trigger',
            'active': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 20,
            'tracking': 'lot',
        })
        self.lot = self.env['stock.production.lot'].create({
            'name': 'Lot tests 01',
            'product_id': self.product.id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.location = self.env.ref('stock.stock_location_stock')
        self.inventory = self.env['stock.inventory'].create({
            'name': 'Add products for tests',
            'filter': 'partial',
            'location_id': self.location.id,
            'exhausted': True,
        })
        self.inventory.action_start()
        self.inventory.line_ids.create({
            'inventory_id': self.inventory.id,
            'product_id': self.product.id,
            'product_qty': 100,
            'location_id': self.location.id,
            'prod_lot_id': self.lot.id,
        })
        self.inventory._action_done()
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })

    def test_use_product_and_create_inspection_success(self):
        product_tmpl_id = self.product.product_tmpl_id
        self.assertFalse(product_tmpl_id.use_management)
        product_tmpl_id.use_management = True
        self.assertTrue(product_tmpl_id.use_management)
        self.assertEquals(self.lot.number_of_uses, 1)
        self.assertEquals(self.lot.times_used, 0)
        self.assertEquals(self.lot.pending_uses, 1)
        product_tmpl_id.write({
            'qc_triggers': [(0, 0, {
                'trigger': self.qc_trigger.id,
                'test': self.qc_test.id,
            })],
        })
        self.assertEquals(len(product_tmpl_id.qc_triggers), 1)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        picking.signed_stock_picking_with_product_use_management()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEquals(self.lot.number_of_uses, 1)
        self.assertEquals(self.lot.times_used, 1)
        self.assertEquals(self.lot.pending_uses, 0)
        self.assertEquals(len(self.lot.qc_use_dates), 1)
        inspections = self.env['qc.inspection'].search([
            ('lot_id', '=', self.lot.id),
        ])
        self.assertEquals(len(inspections), 1)
        inspection = inspections[0]
        self.assertEquals(inspection.lot_id, self.lot)
        self.assertEquals(inspection.product_id, self.lot.product_id)
        wizard = self.env['qc.inspection.set.test'].with_context(
            active_id=inspection.id).create({
                'test': self.qc_test.id,
            })
        wizard.action_create_test()
        inspection.action_todo()
        self.assertEquals(inspection.state, 'ready')
        for line in inspection.inspection_lines:
            if line.question_type == 'qualitative':
                line.qualitative_value = self.val_ok
            if line.question_type == 'quantitative':
                line.quantitative_value = 6.0
        inspection.action_confirm()
        self.assertTrue(inspection.success)
        self.assertEquals(self.lot.times_used, 0)
        self.assertEquals(self.lot.pending_uses, 1)
        self.assertEquals(len(self.lot.qc_use_dates), 1)

    def test_use_product_and_create_inspection_failed(self):
        self.assertFalse(self.product.product_tmpl_id.use_management)
        self.product.product_tmpl_id.use_management = True
        self.assertTrue(self.product.product_tmpl_id.use_management)
        self.assertEquals(self.lot.number_of_uses, 1)
        self.assertEquals(self.lot.times_used, 0)
        self.assertEquals(self.lot.pending_uses, 1)
        self.product.product_tmpl_id.write({
            'qc_triggers': [(0, 0, {
                'trigger': self.qc_trigger.id,
                'test': self.qc_test.id,
            })],
        })
        self.assertEquals(len(self.product.product_tmpl_id.qc_triggers), 1)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        picking.signed_stock_picking_with_product_use_management()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEquals(self.lot.number_of_uses, 1)
        self.assertEquals(self.lot.times_used, 1)
        self.assertEquals(self.lot.pending_uses, 0)
        self.assertEquals(len(self.lot.qc_use_dates), 1)
        inspections = self.env['qc.inspection'].search([
            ('lot_id', '=', self.lot.id),
        ])
        self.assertEquals(len(inspections), 1)
        inspection = inspections[0]
        self.assertEquals(inspection.lot_id, self.lot)
        self.assertEquals(inspection.product_id, self.lot.product_id)
        wizard = self.env['qc.inspection.set.test'].with_context(
            active_id=inspection.id).create({
                'test': self.qc_test.id,
            })
        wizard.action_create_test()
        inspection.action_todo()
        self.assertEquals(inspection.state, 'ready')
        for line in inspection.inspection_lines:
            if line.question_type == 'qualitative':
                line.qualitative_value = self.val_ko
            if line.question_type == 'quantitative':
                line.quantitative_value = 5.0
        inspection.action_confirm()
        self.assertFalse(inspection.success)
        self.assertEquals(self.lot.times_used, 1)
        self.assertEquals(self.lot.pending_uses, 0)
        self.assertEquals(self.lot.number_of_uses, 1)

    def test_check_error_not_signed_picking(self):
        self.assertFalse(self.product.product_tmpl_id.use_management)
        self.assertFalse(self.lot.use_management)
        self.product.product_tmpl_id.use_management = True
        self.assertTrue(self.product.product_tmpl_id)
        self.assertTrue(self.lot.use_management)
        self.assertEquals(self.lot.number_of_uses, 1)
        self.assertEquals(self.lot.times_used, 0)
        self.assertEquals(self.lot.pending_uses, 1)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        with self.assertRaises(exceptions.ValidationError) as result:
            picking.action_done()
        self.assertEquals(
            result.exception.name, 'You have to sign the picking.')

    def test_add_use_to_product_without_exceeding_the_limit(self):
        self.assertFalse(self.lot.use_management)
        self.product.product_tmpl_id.use_management = True
        self.assertTrue(self.product.product_tmpl_id.use_management)
        self.assertTrue(self.lot.use_management)
        self.assertEquals(self.lot.number_of_uses, 1)
        self.lot.number_of_uses = 2
        self.assertEquals(self.lot.number_of_uses, 2)
        self.assertEquals(self.lot.times_used, 0)
        self.assertEquals(self.lot.pending_uses, 2)
        self.assertEquals(len(self.lot.qc_use_dates), 0)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        self.assertFalse(picking.signed_use_management)
        picking.signed_stock_picking_with_product_use_management()
        picking.action_done()
        self.assertEquals(self.lot.times_used, 1)
        self.assertEquals(self.lot.pending_uses, 1)
        self.assertEquals(len(self.lot.qc_use_dates), 1)
        self.assertEquals(self.lot.qc_use_dates[0].picking_id, picking)
        self.assertEquals(self.lot.qc_use_dates[0].user_id, self.env.user)
        self.assertEquals(
            self.lot.qc_use_dates[0].product_tmpl_id,
            self.product.product_tmpl_id)
        inspections = self.env['qc.inspection'].search([
            ('lot_id', '=', self.lot.id),
        ])
        self.assertEquals(len(inspections), 0)

    def test_get_product_with_use_management_picking(self):
        product_tmpl_id = self.product.product_tmpl_id
        self.assertFalse(product_tmpl_id.use_management)
        product_tmpl_id.use_management = True
        self.assertTrue(product_tmpl_id.use_management)
        self.assertEquals(self.lot.number_of_uses, 1)
        self.assertEquals(self.lot.times_used, 0)
        self.assertEquals(self.lot.pending_uses, 1)
        product_tmpl_id.write({
            'qc_triggers': [(0, 0, {
                'trigger': self.qc_trigger.id,
                'test': self.qc_test.id,
            })],
        })
        self.assertEquals(len(product_tmpl_id.qc_triggers), 1)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertTrue(picking.products_with_use_management)

    def test_create_inspection_product_qc_test_ids(self):
        product_tmpl_id = self.product.product_tmpl_id
        self.assertFalse(product_tmpl_id.use_management)
        product_tmpl_id.use_management = True
        self.assertTrue(product_tmpl_id.use_management)
        self.assertFalse(product_tmpl_id.qc_test_ids)
        product_tmpl_id.write({
            'qc_test_ids': [(6, 0, [self.qc_test.id])],
        })
        self.assertTrue(product_tmpl_id.qc_test_ids)
        self.assertEquals(self.lot.number_of_uses, 1)
        self.assertEquals(self.lot.times_used, 0)
        self.assertEquals(self.lot.pending_uses, 1)
        product_tmpl_id.write({
            'qc_triggers': [(0, 0, {
                'trigger': self.qc_trigger.id,
                'test': self.qc_test.id,
            })],
        })
        self.assertEquals(len(product_tmpl_id.qc_triggers), 1)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        picking.signed_stock_picking_with_product_use_management()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEquals(self.lot.number_of_uses, 1)
        self.assertEquals(self.lot.times_used, 1)
        self.assertEquals(self.lot.pending_uses, 0)
        self.assertEquals(len(self.lot.qc_use_dates), 1)
        inspections = self.env['qc.inspection'].search([
            ('lot_id', '=', self.lot.id),
        ])
        self.assertEquals(len(inspections), 1)
        inspection = inspections[0]
        self.assertEquals(inspection.test, self.qc_test)

    def test_get_products_qc_use_date(self):
        product_tmpl_id = self.product.product_tmpl_id
        self.assertFalse(product_tmpl_id.use_management)
        product_tmpl_id.use_management = True
        self.assertTrue(product_tmpl_id.use_management)
        self.assertEquals(self.lot.number_of_uses, 1)
        self.assertEquals(self.lot.times_used, 0)
        self.assertEquals(self.lot.pending_uses, 1)
        product_tmpl_id.write({
            'qc_triggers': [(0, 0, {
                'trigger': self.qc_trigger.id,
                'test': self.qc_test.id,
            })],
        })
        self.assertEquals(len(product_tmpl_id.qc_triggers), 1)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        picking.signed_stock_picking_with_product_use_management()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEquals(self.lot.number_of_uses, 1)
        self.assertEquals(self.lot.times_used, 1)
        self.assertEquals(self.lot.pending_uses, 0)
        self.assertEquals(len(self.lot.qc_use_dates), 1)
        uses = product_tmpl_id.get_product_qc_use_date(product_tmpl_id)
        self.assertEquals(len(uses), 1)
