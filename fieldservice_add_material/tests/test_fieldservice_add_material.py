###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests import common


class TestFieldserviceAddMaterial(common.TransactionCase):

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
            'field_service_tracking': 'sale',
            'fsm_order_template_id': self.fsm_template.id,
            'list_price': 100,
        })
        self.product_2 = self.env['product.product'].create({
            'name': 'Component 2',
            'type': 'product',
            'field_service_tracking': 'sale',
            'fsm_order_template_id': self.fsm_template.id,
            'list_price': 500,
        })
        self.product_no_tracking = self.env['product.product'].create({
            'name': 'Product',
            'type': 'product',
            'list_price': 250,
        })
        self.warehouse_2 = self.env['stock.warehouse'].create({
            'code': 'WH2',
            'name': 'Warehouse 2',
        })

    def test_fieldservice_add_material_is_invoiced_false(self):
        new_product = self.env['product.product'].create({
            'name': 'New product',
            'type': 'product',
            'list_price': 10,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'picking_policy': 'direct',
            'fsm_location_id': self.fsm_location.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing')
        self.assertEquals(len(picking_out), 1)
        self.assertEquals(len(picking_out.move_lines), 2)
        self.assertEquals(picking_out.state, 'confirmed')
        moves_out = picking_out.move_lines
        move_product_1 = moves_out.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = moves_out.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 1)
        self.assertEquals(sale.fsm_order_ids.move_ids, moves_out)
        self.assertEquals(sale.fsm_order_ids.warehouse_id, sale.warehouse_id)
        self.assertEquals(
            picking_out.location_id, sale.warehouse_id.lot_stock_id)
        self.assertEquals(picking_out.location_dest_id, self.customer_location)
        for move in picking_out.move_lines:
            self.assertEquals(move.location_id, sale.warehouse_id.lot_stock_id)
            self.assertEquals(move.location_dest_id, self.customer_location)
        sale.fsm_order_ids.write({
            'warehouse_id': self.warehouse_2.id,
        })
        wizard = self.env['fieldservice.add_material'].with_context({
            'active_ids': sale.fsm_order_ids[0].ids,
            'active_id': sale.fsm_order_ids[0].id,
        }).create({})
        line_obj = self.env['fieldservice.add_material.line']
        line = line_obj.with_context({
            'active_id': sale.fsm_order_ids[0].id,
        }).new({
            'wizard_id': wizard.id,
            'product_id': new_product.id,
            'product_qty': 1,
        })
        line.onchange_product_id()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        self.assertEquals(len(wizard.line_ids), 1)
        wizard.button_accept()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        new_picking_out = self.env['stock.picking'].search([
            ('picking_type_code', '=', 'outgoing'),
            ('partner_id', '=', self.partner.id),
        ], order='id desc', limit=1)
        self.assertEquals(len(new_picking_out), 1)
        self.assertEquals(new_picking_out.state, 'done')
        self.assertEquals(
            new_picking_out.location_id, self.warehouse_2.lot_stock_id)
        self.assertEquals(
            new_picking_out.location_dest_id, self.customer_location)
        self.assertEquals(len(new_picking_out.move_lines), 1)
        self.assertEquals(new_picking_out.move_lines.product_id, new_product)
        self.assertEquals(new_picking_out.move_lines.product_qty, 1)
        self.assertEquals(
            new_picking_out.move_lines.location_id,
            self.warehouse_2.lot_stock_id)
        self.assertEquals(
            new_picking_out.move_lines.location_dest_id,
            self.customer_location)
        picking_message = new_picking_out.message_ids[0]
        self.assertIn('This transfer has been', picking_message.body)
        self.assertIn('%s' % (sale.fsm_order_ids[0].name), picking_message.body)
        fsm_message = sale.fsm_order_ids[0].message_ids[1]
        self.assertIn(
            'This fieldservice order has created picking', fsm_message.body)
        self.assertIn('%s' % (new_picking_out.name), fsm_message.body)

    def test_fieldservice_add_material_is_invoiced_true(self):
        new_product = self.env['product.product'].create({
            'name': 'New product',
            'type': 'product',
            'list_price': 10,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'picking_policy': 'direct',
            'fsm_location_id': self.fsm_location.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing')
        self.assertEquals(len(picking_out), 1)
        self.assertEquals(len(picking_out.move_lines), 2)
        self.assertEquals(picking_out.state, 'confirmed')
        moves_out = picking_out.move_lines
        move_product_1 = moves_out.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = moves_out.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 1)
        self.assertEquals(sale.fsm_order_ids.move_ids, moves_out)
        self.assertEquals(sale.fsm_order_ids.warehouse_id, sale.warehouse_id)
        self.assertEquals(
            picking_out.location_id, sale.warehouse_id.lot_stock_id)
        self.assertEquals(picking_out.location_dest_id, self.customer_location)
        for move in picking_out.move_lines:
            self.assertEquals(move.location_id, sale.warehouse_id.lot_stock_id)
            self.assertEquals(move.location_dest_id, self.customer_location)
        sale.fsm_order_ids.write({
            'warehouse_id': self.warehouse_2.id,
        })
        wizard = self.env['fieldservice.add_material'].with_context({
            'active_ids': sale.fsm_order_ids[0].ids,
            'active_id': sale.fsm_order_ids[0].id,
        }).create({})
        line_obj = self.env['fieldservice.add_material.line']
        line = line_obj.with_context({
            'active_id': sale.fsm_order_ids[0].id,
        }).new({
            'wizard_id': wizard.id,
            'product_id': new_product.id,
            'product_qty': 1,
            'is_invoiced': True,
        })
        line.onchange_product_id()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        self.assertEquals(len(wizard.line_ids), 1)
        wizard.button_accept()
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', self.partner.id),
        ], order='id desc', limit=1)
        self.assertEquals(len(new_sale), 1)
        self.assertEquals(new_sale.state, 'sale')
        self.assertFalse(new_sale.fsm_order_ids)
        self.assertEquals(new_sale.warehouse_id, self.warehouse_2)
        new_picking_out = new_sale.picking_ids
        self.assertEquals(len(new_picking_out), 1)
        self.assertEquals(new_picking_out.state, 'done')
        self.assertEquals(new_picking_out.picking_type_code, 'outgoing')
        self.assertEquals(
            new_picking_out.location_id, self.warehouse_2.lot_stock_id)
        self.assertEquals(
            new_picking_out.location_dest_id, self.customer_location)
        self.assertEquals(len(new_picking_out.move_lines), 1)
        self.assertEquals(new_picking_out.move_lines.product_id, new_product)
        self.assertEquals(new_picking_out.move_lines.product_qty, 1)
        self.assertEquals(
            new_picking_out.move_lines.location_id,
            self.warehouse_2.lot_stock_id)
        self.assertEquals(
            new_picking_out.move_lines.location_dest_id,
            self.customer_location)
        order_message = new_sale.message_ids[0]
        self.assertIn('This sale order has been', order_message.body)
        self.assertIn('%s' % (sale.fsm_order_ids[0].name), order_message.body)
        fsm_message = sale.fsm_order_ids[0].message_ids[1]
        self.assertIn(
            'This fieldservice order has created sale', fsm_message.body)
        self.assertIn('%s' % (new_sale.name), fsm_message.body)

    def test_fieldservice_add_material_line_negative(self):
        new_product = self.env['product.product'].create({
            'name': 'New product',
            'type': 'product',
            'list_price': 10,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'picking_policy': 'direct',
            'fsm_location_id': self.fsm_location.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing')
        self.assertEquals(len(picking_out), 1)
        self.assertEquals(len(picking_out.move_lines), 2)
        self.assertEquals(picking_out.state, 'confirmed')
        moves_out = picking_out.move_lines
        move_product_1 = moves_out.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = moves_out.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 1)
        self.assertEquals(sale.fsm_order_ids.move_ids, moves_out)
        self.assertEquals(sale.fsm_order_ids.warehouse_id, sale.warehouse_id)
        self.assertEquals(
            picking_out.location_id, sale.warehouse_id.lot_stock_id)
        self.assertEquals(picking_out.location_dest_id, self.customer_location)
        for move in picking_out.move_lines:
            self.assertEquals(move.location_id, sale.warehouse_id.lot_stock_id)
            self.assertEquals(move.location_dest_id, self.customer_location)
        sale.fsm_order_ids.write({
            'warehouse_id': self.warehouse_2.id,
        })
        wizard = self.env['fieldservice.add_material'].with_context({
            'active_ids': sale.fsm_order_ids[0].ids,
            'active_id': sale.fsm_order_ids[0].id,
        }).create({})
        line_obj = self.env['fieldservice.add_material.line']
        line = line_obj.with_context({
            'active_id': sale.fsm_order_ids[0].id,
        }).new({
            'wizard_id': wizard.id,
            'product_id': new_product.id,
            'product_qty': -1,
            'is_invoiced': True,
        })
        line.onchange_product_id()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        self.assertEquals(len(wizard.line_ids), 1)
        with self.assertRaises(exceptions.UserError) as result:
            wizard.button_accept()
        self.assertEqual(
            result.exception.name, 'The amounts must be positive.')

    def test_fieldservice_add_material_is_invoiced_false_and_true(self):
        new_product = self.env['product.product'].create({
            'name': 'New product',
            'type': 'product',
            'list_price': 10,
        })
        new_product2 = self.env['product.product'].create({
            'name': 'New product',
            'type': 'product',
            'list_price': 20,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'picking_policy': 'direct',
            'fsm_location_id': self.fsm_location.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing')
        self.assertEquals(len(picking_out), 1)
        self.assertEquals(len(picking_out.move_lines), 2)
        self.assertEquals(picking_out.state, 'confirmed')
        moves_out = picking_out.move_lines
        move_product_1 = moves_out.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = moves_out.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 1)
        self.assertEquals(sale.fsm_order_ids.move_ids, moves_out)
        self.assertEquals(sale.fsm_order_ids.warehouse_id, sale.warehouse_id)
        self.assertEquals(
            picking_out.location_id, sale.warehouse_id.lot_stock_id)
        self.assertEquals(picking_out.location_dest_id, self.customer_location)
        for move in picking_out.move_lines:
            self.assertEquals(move.location_id, sale.warehouse_id.lot_stock_id)
            self.assertEquals(move.location_dest_id, self.customer_location)
        sale.fsm_order_ids.write({
            'warehouse_id': self.warehouse_2.id,
        })
        wizard = self.env['fieldservice.add_material'].with_context({
            'active_ids': sale.fsm_order_ids[0].ids,
            'active_id': sale.fsm_order_ids[0].id,
        }).create({})
        line_obj = self.env['fieldservice.add_material.line']
        line = line_obj.with_context({
            'active_id': sale.fsm_order_ids[0].id,
        }).new({
            'wizard_id': wizard.id,
            'product_id': new_product.id,
            'product_qty': 1,
        })
        line.onchange_product_id()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        line = line_obj.with_context({
            'active_id': sale.fsm_order_ids[0].id,
        }).new({
            'wizard_id': wizard.id,
            'product_id': new_product2.id,
            'product_qty': 2,
            'is_invoiced': True,
        })
        line.onchange_product_id()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        self.assertEquals(len(wizard.line_ids), 2)
        wizard.button_accept()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        new_picking_out = self.env['stock.picking'].search([
            ('picking_type_code', '=', 'outgoing'),
            ('partner_id', '=', self.partner.id),
        ], order='id desc', limit=1)
        self.assertEquals(len(new_picking_out), 1)
        self.assertEquals(new_picking_out.state, 'done')
        self.assertEquals(
            new_picking_out.location_id, self.warehouse_2.lot_stock_id)
        self.assertEquals(
            new_picking_out.location_dest_id, self.customer_location)
        self.assertEquals(len(new_picking_out.move_lines), 1)
        self.assertEquals(new_picking_out.move_lines.product_id, new_product)
        self.assertEquals(new_picking_out.move_lines.product_qty, 1)
        self.assertEquals(
            new_picking_out.move_lines.location_id,
            self.warehouse_2.lot_stock_id)
        self.assertEquals(
            new_picking_out.move_lines.location_dest_id,
            self.customer_location)
        picking_message = new_picking_out.message_ids[0]
        self.assertIn('This transfer has been', picking_message.body)
        self.assertIn('%s' % (sale.fsm_order_ids[0].name), picking_message.body)
        fsm_message = sale.fsm_order_ids[0].message_ids[1]
        self.assertIn(
            'This fieldservice order has created picking', fsm_message.body)
        self.assertIn('%s' % (new_picking_out.name), fsm_message.body)
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', self.partner.id),
        ], order='id desc', limit=1)
        self.assertEquals(len(new_sale), 1)
        self.assertEquals(new_sale.state, 'sale')
        self.assertFalse(new_sale.fsm_order_ids)
        self.assertEquals(new_sale.warehouse_id, self.warehouse_2)
        new_picking_out = new_sale.picking_ids
        self.assertEquals(len(new_picking_out), 1)
        self.assertEquals(new_picking_out.state, 'done')
        self.assertEquals(new_picking_out.picking_type_code, 'outgoing')
        self.assertEquals(
            new_picking_out.location_id, self.warehouse_2.lot_stock_id)
        self.assertEquals(
            new_picking_out.location_dest_id, self.customer_location)
        self.assertEquals(len(new_picking_out.move_lines), 1)
        self.assertEquals(new_picking_out.move_lines.product_id, new_product2)
        self.assertEquals(new_picking_out.move_lines.product_qty, 2)
        self.assertEquals(
            new_picking_out.move_lines.location_id,
            self.warehouse_2.lot_stock_id)
        self.assertEquals(
            new_picking_out.move_lines.location_dest_id,
            self.customer_location)
        sale_message = new_sale.message_ids[0]
        self.assertIn('This sale order has been', sale_message.body)
        self.assertIn('%s' % (sale.fsm_order_ids[0].name), sale_message.body)
        fsm_message = sale.fsm_order_ids[0].message_ids[2]
        self.assertIn(
            'This fieldservice order has created sale', fsm_message.body)
        self.assertIn('%s' % (new_sale.name), fsm_message.body)

    def test_fieldservice_add_material_is_invoiced_false_different_uom(self):
        new_product = self.env['product.product'].create({
            'name': 'New product',
            'type': 'product',
            'list_price': 10,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'picking_policy': 'direct',
            'fsm_location_id': self.fsm_location.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing')
        self.assertEquals(len(picking_out), 1)
        self.assertEquals(len(picking_out.move_lines), 2)
        self.assertEquals(picking_out.state, 'confirmed')
        moves_out = picking_out.move_lines
        move_product_1 = moves_out.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = moves_out.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 1)
        self.assertEquals(sale.fsm_order_ids.move_ids, moves_out)
        self.assertEquals(sale.fsm_order_ids.warehouse_id, sale.warehouse_id)
        self.assertEquals(
            picking_out.location_id, sale.warehouse_id.lot_stock_id)
        self.assertEquals(picking_out.location_dest_id, self.customer_location)
        for move in picking_out.move_lines:
            self.assertEquals(move.location_id, sale.warehouse_id.lot_stock_id)
            self.assertEquals(move.location_dest_id, self.customer_location)
        sale.fsm_order_ids.write({
            'warehouse_id': self.warehouse_2.id,
        })
        wizard = self.env['fieldservice.add_material'].with_context({
            'active_ids': sale.fsm_order_ids[0].ids,
            'active_id': sale.fsm_order_ids[0].id,
        }).create({})
        line_obj = self.env['fieldservice.add_material.line']
        line = line_obj.with_context({
            'active_id': sale.fsm_order_ids[0].id,
        }).new({
            'wizard_id': wizard.id,
            'product_id': new_product.id,
            'product_qty': 1,
        })
        line.onchange_product_id()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        self.assertEquals(len(wizard.line_ids), 1)
        unit = self.env.ref('uom.product_uom_unit')
        dozen = self.env.ref('uom.product_uom_dozen')
        self.assertEquals(line.product_uom_id, unit)
        line.product_uom_id = dozen.id
        self.assertEquals(line.product_uom_id, dozen)
        wizard.button_accept()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        new_picking_out = self.env['stock.picking'].search([
            ('picking_type_code', '=', 'outgoing'),
            ('partner_id', '=', self.partner.id),
        ], order='id desc', limit=1)
        self.assertEquals(len(new_picking_out), 1)
        self.assertEquals(new_picking_out.state, 'done')
        self.assertEquals(
            new_picking_out.location_id, self.warehouse_2.lot_stock_id)
        self.assertEquals(
            new_picking_out.location_dest_id, self.customer_location)
        self.assertEquals(len(new_picking_out.move_lines), 1)
        self.assertEquals(new_picking_out.move_lines.product_id, new_product)
        self.assertEquals(new_picking_out.move_lines.product_qty, 12)
        self.assertEquals(new_picking_out.move_lines.product_uom, unit)
        self.assertEquals(
            new_picking_out.move_lines.location_id,
            self.warehouse_2.lot_stock_id)
        self.assertEquals(
            new_picking_out.move_lines.location_dest_id,
            self.customer_location)
        picking_message = new_picking_out.message_ids[0]
        self.assertIn('This transfer has been', picking_message.body)
        self.assertIn('%s' % (sale.fsm_order_ids[0].name), picking_message.body)
        fsm_message = sale.fsm_order_ids[0].message_ids[1]
        self.assertIn(
            'This fieldservice order has created picking', fsm_message.body)
        self.assertIn('%s' % (new_picking_out.name), fsm_message.body)

    def test_fieldservice_add_material_is_invoiced_true_different_uom(self):
        new_product = self.env['product.product'].create({
            'name': 'New product',
            'type': 'product',
            'list_price': 10,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'picking_policy': 'direct',
            'fsm_location_id': self.fsm_location.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing')
        self.assertEquals(len(picking_out), 1)
        self.assertEquals(len(picking_out.move_lines), 2)
        self.assertEquals(picking_out.state, 'confirmed')
        moves_out = picking_out.move_lines
        move_product_1 = moves_out.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = moves_out.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 1)
        self.assertEquals(sale.fsm_order_ids.move_ids, moves_out)
        self.assertEquals(sale.fsm_order_ids.warehouse_id, sale.warehouse_id)
        self.assertEquals(
            picking_out.location_id, sale.warehouse_id.lot_stock_id)
        self.assertEquals(picking_out.location_dest_id, self.customer_location)
        for move in picking_out.move_lines:
            self.assertEquals(move.location_id, sale.warehouse_id.lot_stock_id)
            self.assertEquals(move.location_dest_id, self.customer_location)
        sale.fsm_order_ids.write({
            'warehouse_id': self.warehouse_2.id,
        })
        wizard = self.env['fieldservice.add_material'].with_context({
            'active_ids': sale.fsm_order_ids[0].ids,
            'active_id': sale.fsm_order_ids[0].id,
        }).create({})
        line_obj = self.env['fieldservice.add_material.line']
        line = line_obj.with_context({
            'active_id': sale.fsm_order_ids[0].id,
        }).new({
            'wizard_id': wizard.id,
            'product_id': new_product.id,
            'product_qty': 1,
            'is_invoiced': True,
        })
        line.onchange_product_id()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        self.assertEquals(len(wizard.line_ids), 1)
        unit = self.env.ref('uom.product_uom_unit')
        dozen = self.env.ref('uom.product_uom_dozen')
        self.assertEquals(line.product_uom_id, unit)
        line.product_uom_id = dozen.id
        self.assertEquals(line.product_uom_id, dozen)
        wizard.button_accept()
        new_sale = self.env['sale.order'].search([
            ('partner_id', '=', self.partner.id),
        ], order='id desc', limit=1)
        self.assertEquals(len(new_sale), 1)
        self.assertEquals(new_sale.state, 'sale')
        self.assertFalse(new_sale.fsm_order_ids)
        self.assertEquals(new_sale.warehouse_id, self.warehouse_2)
        new_picking_out = new_sale.picking_ids
        self.assertEquals(len(new_picking_out), 1)
        self.assertEquals(new_picking_out.state, 'done')
        self.assertEquals(new_picking_out.picking_type_code, 'outgoing')
        self.assertEquals(
            new_picking_out.location_id, self.warehouse_2.lot_stock_id)
        self.assertEquals(
            new_picking_out.location_dest_id, self.customer_location)
        self.assertEquals(len(new_picking_out.move_lines), 1)
        self.assertEquals(new_picking_out.move_lines.product_id, new_product)
        self.assertEquals(new_picking_out.move_lines.product_qty, 12)
        self.assertEquals(new_picking_out.move_lines.product_uom, unit)
        self.assertEquals(
            new_picking_out.move_lines.location_id,
            self.warehouse_2.lot_stock_id)
        self.assertEquals(
            new_picking_out.move_lines.location_dest_id,
            self.customer_location)
        sale_message = new_sale.message_ids[0]
        self.assertIn('This sale order has been', sale_message.body)
        self.assertIn('%s' % (sale.fsm_order_ids[0].name), sale_message.body)
        fsm_message = sale.fsm_order_ids[0].message_ids[1]
        self.assertIn(
            'This fieldservice order has created sale', fsm_message.body)
        self.assertIn('%s' % (new_sale.name), fsm_message.body)

    def test_fieldservice_add_material_duplicated_line(self):
        new_product = self.env['product.product'].create({
            'name': 'New product',
            'type': 'product',
            'list_price': 10,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'picking_policy': 'direct',
            'fsm_location_id': self.fsm_location.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 1)
        picking_out = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing')
        self.assertEquals(len(picking_out), 1)
        self.assertEquals(len(picking_out.move_lines), 2)
        self.assertEquals(picking_out.state, 'confirmed')
        moves_out = picking_out.move_lines
        move_product_1 = moves_out.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertTrue(move_product_1)
        self.assertEquals(move_product_1.product_uom_qty, 1)
        move_product_2 = moves_out.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertTrue(move_product_2)
        self.assertEquals(move_product_2.product_uom_qty, 1)
        self.assertEquals(sale.fsm_order_ids.move_ids, moves_out)
        self.assertEquals(sale.fsm_order_ids.warehouse_id, sale.warehouse_id)
        self.assertEquals(
            picking_out.location_id, sale.warehouse_id.lot_stock_id)
        self.assertEquals(picking_out.location_dest_id, self.customer_location)
        for move in picking_out.move_lines:
            self.assertEquals(move.location_id, sale.warehouse_id.lot_stock_id)
            self.assertEquals(move.location_dest_id, self.customer_location)
        sale.fsm_order_ids.write({
            'warehouse_id': self.warehouse_2.id,
        })
        wizard = self.env['fieldservice.add_material'].with_context({
            'active_ids': sale.fsm_order_ids[0].ids,
            'active_id': sale.fsm_order_ids[0].id,
        }).create({})
        line_obj = self.env['fieldservice.add_material.line']
        line = line_obj.with_context({
            'active_id': sale.fsm_order_ids[0].id,
        }).new({
            'wizard_id': wizard.id,
            'product_id': new_product.id,
            'product_qty': 1,
        })
        line.onchange_product_id()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        line = line_obj.with_context({
            'active_id': sale.fsm_order_ids[0].id,
        }).new({
            'wizard_id': wizard.id,
            'product_id': new_product.id,
            'product_qty': 1,
        })
        line.onchange_product_id()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        self.assertEquals(len(wizard.line_ids), 2)
        with self.assertRaises(exceptions.UserError) as result:
            wizard.button_accept()
        self.assertEqual(
            result.exception.name,
            'There are duplicated products in wizard lines!')
