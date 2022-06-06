###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests import common


class TestFieldserviceStockReturn(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.customer_location = self.env.ref('stock.stock_location_customers')
        self.picking_internal_type = self.env.ref(
            'stock.picking_type_internal')
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        self.fsm_location = self.env['fsm.location'].create({
            'name': 'Location test',
            'owner_id': self.partner.id,
        })
        self.fsm_template = self.env['fsm.template'].create({
            'name': 'Template 1',
        })
        self.assertTrue(self.fsm_location.inventory_location_id)
        self.product_1 = self.env['product.product'].create({
            'name': 'Component 1',
            'type': 'product',
        })
        self.product_2 = self.env['product.product'].create({
            'name': 'Component 2',
            'type': 'product',
        })
        self.product_pack = self.env['product.product'].create({
            'name': 'Product pack',
            'pack_ok': True,
            'type': 'service',
            'pack_type': 'non_detailed',
            'list_price': 50,
            'pack_line_ids': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'quantity': 1,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'quantity': 2,
                }),
            ]
        })
        self.service_fsm = self.env['product.product'].create({
            'name': 'Service FSM product',
            'type': 'service',
            'field_service_tracking': 'line',
            'fsm_order_template_id': self.fsm_template.id,
            'installation_product': True,
            'product_tmpl_kit_id': self.product_pack.product_tmpl_id.id,
            'list_price': 100,
        })
        self.warehouse_2 = self.env['stock.warehouse'].create({
            'code': 'WH2',
            'name': 'Warehouse 2',
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'picking_policy': 'direct',
            'fsm_location_id': self.fsm_location.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.service_fsm.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        self.sale.action_confirm()

    def test_fieldservice_stock_return_partially(self):
        self.assertEquals(len(self.sale.fsm_order_ids), 1)
        fsm_order = self.sale.fsm_order_ids[0]
        self.assertEquals(len(self.sale.picking_ids), 1)
        fsm_order.write({
            'warehouse_id': self.warehouse_2.id,
        })
        internal_picking = fsm_order.move_internal_ids.mapped(
            'picking_id')
        self.assertEquals(len(internal_picking), 1)
        internal_picking.action_confirm()
        internal_picking.action_assign()
        move_product_1 = internal_picking.move_lines.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = internal_picking.move_lines.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertEquals(move_product_2.product_uom_qty, 2)
        for move in internal_picking.move_lines:
            move.quantity_done = move.product_uom_qty
        internal_picking.action_done()
        wizard = self.env['fieldservice.add_material'].with_context({
            'active_ids': fsm_order.ids,
            'active_id': fsm_order.id,
        }).create({})
        for line in wizard.line_ids:
            line.product_qty = 1
        self.assertEquals(len(wizard.line_ids), 2)
        wizard.button_accept()
        new_picking_out = self.env['stock.picking'].search([
            ('picking_type_code', '=', 'outgoing'),
            ('partner_id', '=', self.partner.id),
        ], order='id desc', limit=1)
        self.assertEquals(len(new_picking_out), 1)
        fsm_order.action_complete()
        self.assertEquals(len(self.sale.fsm_order_ids), 1)
        self.assertEquals(fsm_order.stage_id.is_closed, True)
        fsm_order.action_return_stock()
        new_picking_internal = self.env['stock.picking'].search([
            ('picking_type_code', '=', 'internal'),
            ('partner_id', '=', self.partner.id),
        ], order='id desc', limit=1)
        self.assertEquals(len(new_picking_internal.move_lines), 1)
        self.assertEquals(new_picking_internal.move_lines.quantity_done, 1)
        self.assertEquals(
            new_picking_internal.move_lines.product_id, self.product_2)
        self.assertEquals(new_picking_internal.state, 'done')

    def test_fieldservice_stock_return_cancelled_order(self):
        self.assertEquals(len(self.sale.fsm_order_ids), 1)
        fsm_order = self.sale.fsm_order_ids[0]
        self.assertEquals(len(self.sale.picking_ids), 1)
        fsm_order.write({
            'warehouse_id': self.warehouse_2.id,
        })
        internal_picking = fsm_order.move_internal_ids.mapped(
            'picking_id')
        self.assertEquals(len(internal_picking), 1)
        internal_picking.action_confirm()
        internal_picking.action_assign()
        move_product_1 = internal_picking.move_lines.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = internal_picking.move_lines.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertEquals(move_product_2.product_uom_qty, 2)
        for move in internal_picking.move_lines:
            move.quantity_done = move.product_uom_qty
        internal_picking.action_done()
        fsm_order.action_cancel()
        self.assertEquals(len(self.sale.fsm_order_ids), 1)
        self.assertEquals(fsm_order.stage_id.is_closed, True)
        fsm_order.action_return_stock()
        new_picking_internal = self.env['stock.picking'].search([
            ('picking_type_code', '=', 'internal'),
            ('partner_id', '=', self.partner.id),
        ], order='id desc', limit=1)
        self.assertEquals(len(new_picking_internal.move_lines), 2)
        move_product_1 = new_picking_internal.move_lines.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = new_picking_internal.move_lines.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertEquals(move_product_1.quantity_done, 1)
        self.assertEquals(move_product_2.quantity_done, 2)
        self.assertEquals(new_picking_internal.state, 'done')

    def test_fieldservice_stock_multiple_return(self):
        self.assertEquals(len(self.sale.fsm_order_ids), 1)
        fsm_order = self.sale.fsm_order_ids[0]
        self.assertEquals(len(self.sale.picking_ids), 1)
        fsm_order.write({
            'warehouse_id': self.warehouse_2.id,
        })
        internal_picking = fsm_order.move_internal_ids.mapped(
            'picking_id')
        self.assertEquals(len(internal_picking), 1)
        internal_picking.action_confirm()
        internal_picking.action_assign()
        move_product_1 = internal_picking.move_lines.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = internal_picking.move_lines.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertEquals(move_product_2.product_uom_qty, 2)
        for move in internal_picking.move_lines:
            move.quantity_done = move.product_uom_qty
        internal_picking.action_done()
        wizard = self.env['fieldservice.add_material'].with_context({
            'active_ids': fsm_order.ids,
            'active_id': fsm_order.id,
        }).create({})
        for line in wizard.line_ids:
            line.product_qty = 1
        self.assertEquals(len(wizard.line_ids), 2)
        wizard.button_accept()
        new_picking_out = self.env['stock.picking'].search([
            ('picking_type_code', '=', 'outgoing'),
            ('partner_id', '=', self.partner.id),
        ], order='id desc', limit=1)
        self.assertEquals(len(new_picking_out), 1)
        fsm_order.action_complete()
        self.assertEquals(len(self.sale.fsm_order_ids), 1)
        self.assertEquals(fsm_order.stage_id.is_closed, True)
        fsm_order.action_return_stock()
        new_picking_internal = self.env['stock.picking'].search([
            ('picking_type_code', '=', 'internal'),
            ('partner_id', '=', self.partner.id),
        ], order='id desc', limit=1)
        self.assertEquals(len(new_picking_internal.move_lines), 1)
        self.assertEquals(new_picking_internal.move_lines.quantity_done, 1)
        self.assertEquals(
            new_picking_internal.move_lines.product_id, self.product_2)
        self.assertEquals(new_picking_internal.state, 'done')
        with self.assertRaises(exceptions.UserError) as result:
            fsm_order.action_return_stock()
        self.assertEqual(
            result.exception.name, 'Fieldservice order stock already returned.')

    def test_fieldservice_stock_return_no_pending_stock(self):
        self.assertEquals(len(self.sale.fsm_order_ids), 1)
        fsm_order = self.sale.fsm_order_ids[0]
        self.assertEquals(len(self.sale.picking_ids), 1)
        fsm_order.write({
            'warehouse_id': self.warehouse_2.id,
        })
        internal_picking = fsm_order.move_internal_ids.mapped(
            'picking_id')
        self.assertEquals(len(internal_picking), 1)
        internal_picking.action_confirm()
        internal_picking.action_assign()
        move_product_1 = internal_picking.move_lines.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = internal_picking.move_lines.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertEquals(move_product_2.product_uom_qty, 2)
        for move in internal_picking.move_lines:
            move.quantity_done = move.product_uom_qty
        internal_picking.action_done()
        wizard = self.env['fieldservice.add_material'].with_context({
            'active_ids': fsm_order.ids,
            'active_id': fsm_order.id,
        }).create({})
        for line in wizard.line_ids:
            line.product_qty = line.quantity_available
        self.assertEquals(len(wizard.line_ids), 2)
        wizard.button_accept()
        new_picking_out = self.env['stock.picking'].search([
            ('picking_type_code', '=', 'outgoing'),
            ('partner_id', '=', self.partner.id),
        ], order='id desc', limit=1)
        self.assertEquals(len(new_picking_out), 1)
        fsm_order.action_complete()
        self.assertEquals(len(self.sale.fsm_order_ids), 1)
        self.assertEquals(fsm_order.stage_id.is_closed, True)
        with self.assertRaises(exceptions.ValidationError) as result:
            fsm_order.action_return_stock()
        self.assertEqual(
            result.exception.name, 'There are not quantities to return.')

    def test_fieldservice_stock_return_fsm_not_done(self):
        self.assertEquals(len(self.sale.fsm_order_ids), 1)
        fsm_order = self.sale.fsm_order_ids[0]
        self.assertEquals(len(self.sale.picking_ids), 1)
        fsm_order.write({
            'warehouse_id': self.warehouse_2.id,
        })
        internal_picking = fsm_order.move_internal_ids.mapped(
            'picking_id')
        self.assertEquals(len(internal_picking), 1)
        internal_picking.action_confirm()
        internal_picking.action_assign()
        move_product_1 = internal_picking.move_lines.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = internal_picking.move_lines.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertEquals(move_product_2.product_uom_qty, 2)
        for move in internal_picking.move_lines:
            move.quantity_done = move.product_uom_qty
        internal_picking.action_done()
        wizard = self.env['fieldservice.add_material'].with_context({
            'active_ids': fsm_order.ids,
            'active_id': fsm_order.id,
        }).create({})
        for line in wizard.line_ids:
            line.product_qty = line.quantity_available
        self.assertEquals(len(wizard.line_ids), 2)
        wizard.button_accept()
        new_picking_out = self.env['stock.picking'].search([
            ('picking_type_code', '=', 'outgoing'),
            ('partner_id', '=', self.partner.id),
        ], order='id desc', limit=1)
        self.assertEquals(len(new_picking_out), 1)
        self.assertEquals(len(self.sale.fsm_order_ids), 1)
        self.assertEquals(fsm_order.stage_id.is_closed, False)
        with self.assertRaises(exceptions.ValidationError) as result:
            fsm_order.action_return_stock()
        self.assertEqual(
            result.exception.name,
            'Fieldservice order must be in done or cancel state.')

    def test_fieldservice_stock_return_internal_picking_not_done(self):
        self.assertEquals(len(self.sale.fsm_order_ids), 1)
        fsm_order = self.sale.fsm_order_ids[0]
        self.assertEquals(len(self.sale.picking_ids), 1)
        fsm_order.write({
            'warehouse_id': self.warehouse_2.id,
        })
        internal_picking = fsm_order.move_internal_ids.mapped(
            'picking_id')
        self.assertEquals(len(internal_picking), 1)
        internal_picking.action_confirm()
        internal_picking.action_assign()
        move_product_1 = internal_picking.move_lines.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = internal_picking.move_lines.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertEquals(move_product_2.product_uom_qty, 2)
        for move in internal_picking.move_lines:
            move.quantity_done = move.product_uom_qty
        fsm_order.action_complete()
        with self.assertRaises(exceptions.UserError) as result:
            fsm_order.action_return_stock()
        self.assertEqual(
            result.exception.name, 'There no are stock moves done.')
