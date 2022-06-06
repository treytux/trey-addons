###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests import common


class TestFieldserviceSalePickingPack(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        self.location = self.env['fsm.location'].create({
            'name': 'Location test',
            'owner_id': self.partner.id,
        })
        self.assertTrue(self.location.inventory_location_id)
        self.component_1_1 = self.env['product.product'].create({
            'name': 'Component 1.1',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        self.component_1_2 = self.env['product.product'].create({
            'name': 'Component 1.2',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 500,
        })
        self.component_2_1 = self.env['product.product'].create({
            'name': 'Component 2.1',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        self.component_2_2 = self.env['product.product'].create({
            'name': 'Component 2.2',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        self.product_pack_detail_1 = self.env['product.product'].create({
            'name': 'Pack 1',
            'type': 'product',
            'list_price': 1,
            'invoice_policy': 'delivery',
            'pack_ok': True,
            'pack_type': 'detailed',
            'pack_component_price': 'detailed',
            'pack_line_ids': [
                (0, 0, {
                    'product_id': self.component_1_1.id,
                    'quantity': 1,
                }),
                (0, 0, {
                    'product_id': self.component_1_2.id,
                    'quantity': 2,
                }),
            ],
        })
        self.product_pack_detail_2 = self.env['product.product'].create({
            'name': 'Pack 2',
            'type': 'product',
            'list_price': 1,
            'invoice_policy': 'delivery',
            'pack_ok': True,
            'pack_type': 'non_detailed',
            'pack_line_ids': [
                (0, 0, {
                    'product_id': self.component_2_1.id,
                    'quantity': 1,
                }),
                (0, 0, {
                    'product_id': self.component_2_2.id,
                    'quantity': 3,
                }),
            ],
        })

    def test_fsm_track_sale_product_install_and_product_independend(self):
        product_installation_prod = self.env['product.product'].create({
            'name': 'Installation product',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 300,
            'field_service_tracking': 'sale',
            'installation_product': True,
            'product_tmpl_kit_id': (
                self.product_pack_detail_1.product_tmpl_id.id),
        })
        product_A = self.env['product.product'].create({
            'name': 'Product A',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_A.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_installation_prod.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        line_product_installation_prod = sale.order_line.filtered(
            lambda ln: ln.product_id == product_installation_prod)
        self.assertEquals(len(line_product_installation_prod), 1)
        line_product_A = sale.order_line.filtered(
            lambda ln: ln.product_id == product_A)
        self.assertEquals(len(line_product_A), 1)
        self.assertFalse(line_product_A.sale_line_fsm_id)
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 2)
        picking_out = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing')
        self.assertEquals(len(picking_out), 1)
        self.assertEquals(len(picking_out.move_lines), 2)
        moves_out = picking_out.move_lines
        self.assertFalse(moves_out.mapped('fsm_order_id'))
        move_product_A = moves_out.filtered(
            lambda m: m.product_id == product_A)
        self.assertTrue(move_product_A)
        self.assertEquals(move_product_A.product_uom_qty, 1)
        move_product_installation = moves_out.filtered(
            lambda m: m.product_id == product_installation_prod)
        self.assertTrue(move_product_installation)
        self.assertEquals(move_product_installation.product_uom_qty, 1)
        picking_internal = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'internal')
        self.assertEquals(len(picking_internal), 1)
        self.assertEquals(picking_internal.origin, sale.name)
        self.assertEquals(len(picking_internal.move_lines), 2)
        moves_internal = picking_internal.move_lines
        move_component_1_1 = moves_internal.filtered(
            lambda m: m.product_id == self.component_1_1)
        self.assertTrue(move_component_1_1)
        self.assertEquals(move_component_1_1.product_uom_qty, 1)
        move_component_1_2 = moves_internal.filtered(
            lambda m: m.product_id == self.component_1_2)
        self.assertTrue(move_component_1_2)
        self.assertEquals(move_component_1_2.product_uom_qty, 2)
        stock_location = sale.warehouse_id.lot_stock_id
        vehicle_location = sale.fsm_order_ids.warehouse_id.lot_stock_id
        self.assertEquals(picking_internal.location_id, stock_location)
        self.assertEquals(picking_internal.location_dest_id, vehicle_location)
        self.assertFalse(sale.fsm_order_ids.move_ids)
        self.assertEquals(sale.fsm_order_ids.move_internal_ids, moves_internal)
        self.assertEquals(sale.fsm_order_ids.delivery_count, 1)
        self.assertEquals(sale.fsm_order_ids.internal_count, 1)

    def test_fsm_track_sale_product_install_qty5_and_product_independend(self):
        product_installation_prod = self.env['product.product'].create({
            'name': 'Installation product',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 300,
            'field_service_tracking': 'sale',
            'installation_product': True,
            'product_tmpl_kit_id': (
                self.product_pack_detail_1.product_tmpl_id.id),
        })
        product_A = self.env['product.product'].create({
            'name': 'Product A',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_A.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_installation_prod.id,
                    'product_uom_qty': 5,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 2)
        picking_out = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing')
        self.assertEquals(len(picking_out), 1)
        self.assertEquals(len(picking_out.move_lines), 2)
        moves_out = picking_out.move_lines
        self.assertFalse(moves_out.mapped('fsm_order_id'))
        move_product_A = moves_out.filtered(
            lambda m: m.product_id == product_A)
        self.assertTrue(move_product_A)
        self.assertEquals(move_product_A.product_uom_qty, 1)
        move_product_installation = moves_out.filtered(
            lambda m: m.product_id == product_installation_prod)
        self.assertTrue(move_product_installation)
        self.assertEquals(move_product_installation.product_uom_qty, 5)
        picking_internal = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'internal')
        self.assertEquals(len(picking_internal), 1)
        self.assertEquals(picking_internal.origin, sale.name)
        self.assertEquals(len(picking_internal.move_lines), 2)
        moves_internal = picking_internal.move_lines
        move_component_1_1 = moves_internal.filtered(
            lambda m: m.product_id == self.component_1_1)
        self.assertTrue(move_component_1_1)
        self.assertEquals(move_component_1_1.product_uom_qty, 5)
        move_component_1_2 = moves_internal.filtered(
            lambda m: m.product_id == self.component_1_2)
        self.assertTrue(move_component_1_2)
        self.assertEquals(move_component_1_2.product_uom_qty, 10)
        stock_location = sale.warehouse_id.lot_stock_id
        vehicle_location = sale.fsm_order_ids.warehouse_id.lot_stock_id
        self.assertEquals(picking_internal.location_id, stock_location)
        self.assertEquals(picking_internal.location_dest_id, vehicle_location)
        self.assertFalse(sale.fsm_order_ids.move_ids)
        self.assertEquals(sale.fsm_order_ids.move_internal_ids, moves_internal)
        self.assertEquals(sale.fsm_order_ids.delivery_count, 1)
        self.assertEquals(sale.fsm_order_ids.internal_count, 1)

    def test_fsm_track_sale_product_not_install_and_product_independend(self):
        product_no_pack = self.env['product.product'].create({
            'name': 'Product no pack',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 300,
            'field_service_tracking': 'sale',
        })
        product_A = self.env['product.product'].create({
            'name': 'Product A',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_A.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_no_pack.id,
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
        moves_out = picking_out.move_lines
        self.assertFalse(moves_out.mapped('fsm_order_id'))
        move_product_A = moves_out.filtered(
            lambda m: m.product_id == product_A)
        self.assertTrue(move_product_A)
        self.assertEquals(move_product_A.product_uom_qty, 1)
        move_product_no_pack = moves_out.filtered(
            lambda m: m.product_id == product_no_pack)
        self.assertTrue(move_product_no_pack)
        self.assertEquals(move_product_no_pack.product_uom_qty, 1)
        self.assertFalse(sale.fsm_order_ids.move_ids)
        self.assertFalse(sale.fsm_order_ids.move_internal_ids)
        self.assertEquals(sale.fsm_order_ids.delivery_count, 1)
        self.assertEquals(sale.fsm_order_ids.internal_count, 0)

    def test_fsm_track_sale_line_product_install_and_product_independend(self):
        product_installation_prod = self.env['product.product'].create({
            'name': 'Installation product',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 300,
            'field_service_tracking': 'sale',
            'installation_product': True,
            'product_tmpl_kit_id': (
                self.product_pack_detail_1.product_tmpl_id.id),
        })
        product_no_pack_fsm_line = self.env['product.product'].create({
            'name': 'Product no pack fsm by line',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 300,
            'field_service_tracking': 'line',
        })
        product_A = self.env['product.product'].create({
            'name': 'Product A',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_A.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_installation_prod.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_no_pack_fsm_line.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 2)
        self.assertEquals(len(sale.picking_ids), 2)
        picking_out = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing')
        self.assertEquals(len(picking_out), 1)
        self.assertEquals(len(picking_out.move_lines), 3)
        moves_out = picking_out.move_lines
        self.assertFalse(moves_out.mapped('fsm_order_id'))
        move_product_A = moves_out.filtered(
            lambda m: m.product_id == product_A)
        self.assertTrue(move_product_A)
        self.assertEquals(move_product_A.product_uom_qty, 1)
        move_product_installation = moves_out.filtered(
            lambda m: m.product_id == product_installation_prod)
        self.assertTrue(move_product_installation)
        self.assertEquals(move_product_installation.product_uom_qty, 1)
        move_product_no_pack_fsm_line = moves_out.filtered(
            lambda m: m.product_id == product_no_pack_fsm_line)
        self.assertTrue(move_product_no_pack_fsm_line)
        self.assertEquals(move_product_no_pack_fsm_line.product_uom_qty, 1)
        picking_internal = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'internal')
        self.assertEquals(len(picking_internal), 1)
        self.assertEquals(picking_internal.origin, sale.name)
        self.assertEquals(len(picking_internal.move_lines), 2)
        moves_internal = picking_internal.move_lines
        self.assertIn(
            picking_internal.move_lines.mapped('fsm_order_id'),
            sale.fsm_order_ids)
        self.assertIn(
            moves_internal.mapped('fsm_order_id'), sale.fsm_order_ids)
        move_component_1_1 = moves_internal.filtered(
            lambda m: m.product_id == self.component_1_1)
        self.assertTrue(move_component_1_1)
        self.assertEquals(move_component_1_1.product_uom_qty, 1)
        move_component_1_2 = moves_internal.filtered(
            lambda m: m.product_id == self.component_1_2)
        self.assertTrue(move_component_1_2)
        self.assertEquals(move_component_1_2.product_uom_qty, 2)
        stock_location = sale.warehouse_id.lot_stock_id
        for fsm in sale.fsm_order_ids:
            vehicle_location = fsm.warehouse_id.lot_stock_id
        self.assertEquals(picking_internal.location_id, stock_location)
        self.assertEquals(picking_internal.location_dest_id, vehicle_location)
        fsm_install_1 = sale.fsm_order_ids.filtered(
            lambda f: f.move_internal_ids)
        self.assertEquals(fsm_install_1.delivery_count, 1)
        self.assertEquals(fsm_install_1.internal_count, 1)
        fsm_install_2 = sale.fsm_order_ids.filtered(
            lambda f: not f.move_internal_ids)
        self.assertEquals(fsm_install_2.delivery_count, 0)
        self.assertEquals(fsm_install_2.internal_count, 0)

    def test_fsm_contraint_product_tmpl(self):
        product_nopack = self.env['product.product'].create({
            'name': 'No pack',
            'type': 'product',
            'list_price': 1,
            'invoice_policy': 'delivery',
            'pack_ok': False,
        })
        with self.assertRaises(ValidationError) as result:
            self.env['product.product'].create({
                'name': 'Installation product',
                'type': 'product',
                'invoice_policy': 'delivery',
                'list_price': 300,
                'field_service_tracking': 'sale',
                'installation_product': True,
                'product_tmpl_kit_id': product_nopack.product_tmpl_id.id,
            })
        self.assertEqual(
            result.exception.name,
            'Warning! The \'Product kit\' field must be a pack.')

    def test_fsm_track_sale_service_install_and_product_independend(self):
        product_installation_service = self.env['product.product'].create({
            'name': 'Installation service',
            'type': 'service',
            'invoice_policy': 'delivery',
            'list_price': 300,
            'field_service_tracking': 'sale',
            'installation_product': True,
            'product_tmpl_kit_id': (
                self.product_pack_detail_1.product_tmpl_id.id),
        })
        product_A = self.env['product.product'].create({
            'name': 'Product A',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_A.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_installation_service.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 2)
        picking_out = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing')
        self.assertEquals(len(picking_out), 1)
        self.assertEquals(len(picking_out.move_lines), 1)
        moves_out = picking_out.move_lines
        self.assertFalse(moves_out.mapped('fsm_order_id'))
        move_product_A = moves_out.filtered(
            lambda m: m.product_id == product_A)
        self.assertTrue(move_product_A)
        self.assertEquals(move_product_A.product_uom_qty, 1)
        move_product_installation = moves_out.filtered(
            lambda m: m.product_id == product_installation_service)
        self.assertFalse(move_product_installation)
        picking_internal = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'internal')
        self.assertEquals(len(picking_internal), 1)
        self.assertEquals(picking_internal.origin, sale.name)
        self.assertEquals(len(picking_internal.move_lines), 2)
        moves_internal = picking_internal.move_lines
        move_component_1_1 = moves_internal.filtered(
            lambda m: m.product_id == self.component_1_1)
        self.assertTrue(move_component_1_1)
        self.assertEquals(move_component_1_1.product_uom_qty, 1)
        move_component_1_2 = moves_internal.filtered(
            lambda m: m.product_id == self.component_1_2)
        self.assertTrue(move_component_1_2)
        self.assertEquals(move_component_1_2.product_uom_qty, 2)
        stock_location = sale.warehouse_id.lot_stock_id
        vehicle_location = sale.fsm_order_ids.warehouse_id.lot_stock_id
        self.assertEquals(picking_internal.location_id, stock_location)
        self.assertEquals(picking_internal.location_dest_id, vehicle_location)
        self.assertFalse(sale.fsm_order_ids.move_ids)
        self.assertEquals(sale.fsm_order_ids.move_internal_ids, moves_internal)
        self.assertEquals(sale.fsm_order_ids.delivery_count, 1)
        self.assertEquals(sale.fsm_order_ids.internal_count, 1)

    def test_fsm_track_sale_service_install_qty5_and_product_independend(self):
        product_installation_service = self.env['product.product'].create({
            'name': 'Installation service',
            'type': 'service',
            'invoice_policy': 'delivery',
            'list_price': 300,
            'field_service_tracking': 'sale',
            'installation_product': True,
            'product_tmpl_kit_id': (
                self.product_pack_detail_1.product_tmpl_id.id),
        })
        product_A = self.env['product.product'].create({
            'name': 'Product A',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_A.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_installation_service.id,
                    'product_uom_qty': 5,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 2)
        picking_out = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing')
        self.assertEquals(len(picking_out), 1)
        self.assertEquals(len(picking_out.move_lines), 1)
        moves_out = picking_out.move_lines
        self.assertFalse(moves_out.mapped('fsm_order_id'))
        move_product_A = moves_out.filtered(
            lambda m: m.product_id == product_A)
        self.assertTrue(move_product_A)
        self.assertEquals(move_product_A.product_uom_qty, 1)
        move_product_installation = moves_out.filtered(
            lambda m: m.product_id == product_installation_service)
        self.assertFalse(move_product_installation)
        picking_internal = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'internal')
        self.assertEquals(len(picking_internal), 1)
        self.assertEquals(picking_internal.origin, sale.name)
        self.assertEquals(len(picking_internal.move_lines), 2)
        moves_internal = picking_internal.move_lines
        move_component_1_1 = moves_internal.filtered(
            lambda m: m.product_id == self.component_1_1)
        self.assertTrue(move_component_1_1)
        self.assertEquals(move_component_1_1.product_uom_qty, 5)
        move_component_1_2 = moves_internal.filtered(
            lambda m: m.product_id == self.component_1_2)
        self.assertTrue(move_component_1_2)
        self.assertEquals(move_component_1_2.product_uom_qty, 10)
        stock_location = sale.warehouse_id.lot_stock_id
        vehicle_location = sale.fsm_order_ids.warehouse_id.lot_stock_id
        self.assertEquals(picking_internal.location_id, stock_location)
        self.assertEquals(picking_internal.location_dest_id, vehicle_location)
        self.assertFalse(sale.fsm_order_ids.move_ids)
        self.assertEquals(sale.fsm_order_ids.move_internal_ids, moves_internal)
        self.assertEquals(sale.fsm_order_ids.delivery_count, 1)
        self.assertEquals(sale.fsm_order_ids.internal_count, 1)

    def test_fsm_track_line_service_installs_and_product_dependend(self):
        product_installation_line_1 = self.env['product.product'].create({
            'name': 'Installation product 1',
            'type': 'service',
            'invoice_policy': 'delivery',
            'list_price': 300,
            'field_service_tracking': 'line',
            'installation_product': True,
            'product_tmpl_kit_id': (
                self.product_pack_detail_1.product_tmpl_id.id),
        })
        product_installation_line_2 = self.env['product.product'].create({
            'name': 'Installation product 2',
            'type': 'service',
            'invoice_policy': 'delivery',
            'list_price': 300,
            'field_service_tracking': 'line',
            'installation_product': True,
            'product_tmpl_kit_id': (
                self.product_pack_detail_2.product_tmpl_id.id),
        })
        product_A = self.env['product.product'].create({
            'name': 'Product A',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_A.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_installation_line_1.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_installation_line_2.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        line_product_installation_line_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == product_installation_line_1)
        self.assertEquals(len(line_product_installation_line_1), 1)
        line_product_A = sale.order_line.filtered(
            lambda ln: ln.product_id == product_A)
        self.assertEquals(len(line_product_A), 1)
        self.assertFalse(line_product_A.sale_line_fsm_id)
        wizard = self.env['sale.order.relate_to_installations'].with_context({
            'active_ids': sale.ids,
            'active_id': sale.id,
        }).create({})
        self.assertEquals(len(wizard.line_ids), 1)
        wizard.line_ids[0].sale_line_fsm_id = (
            line_product_installation_line_1.id)
        wizard.button_accept()
        self.assertEquals(
            line_product_A.sale_line_fsm_id, line_product_installation_line_1)
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 2)
        self.assertEquals(len(sale.picking_ids), 3)
        picking_out = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing')
        self.assertEquals(len(picking_out), 1)
        self.assertEquals(len(picking_out.move_lines), 1)
        moves_out = picking_out.move_lines
        move_product_A = moves_out.filtered(
            lambda m: m.product_id == product_A)
        self.assertTrue(move_product_A)
        self.assertEquals(move_product_A.product_uom_qty, 1)
        move_product_installation_line_1 = moves_out.filtered(
            lambda m: m.product_id == product_installation_line_1)
        self.assertFalse(move_product_installation_line_1)
        picking_internals = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'internal')
        self.assertEquals(len(picking_internals), 2)
        picking_internal_1 = picking_internals.filtered(
            lambda p: self.component_1_1 in p.move_lines.mapped('product_id'))
        self.assertEquals(len(picking_internal_1), 1)
        self.assertEquals(len(picking_internal_1.move_lines), 2)
        moves_internal_1 = picking_internal_1.move_lines
        move_component_1_1 = moves_internal_1.filtered(
            lambda m: m.product_id == self.component_1_1)
        self.assertTrue(move_component_1_1)
        self.assertEquals(move_component_1_1.product_uom_qty, 1)
        move_component_1_2 = moves_internal_1.filtered(
            lambda m: m.product_id == self.component_1_2)
        self.assertTrue(move_component_1_2)
        self.assertEquals(move_component_1_2.product_uom_qty, 2)
        picking_internal_2 = picking_internals.filtered(
            lambda p: self.component_2_1 in p.move_lines.mapped('product_id'))
        self.assertEquals(len(picking_internal_2), 1)
        self.assertEquals(len(picking_internal_2.move_lines), 2)
        moves_internal_2 = picking_internal_2.move_lines
        move_component_2_1 = moves_internal_2.filtered(
            lambda m: m.product_id == self.component_2_1)
        self.assertTrue(move_component_2_1)
        self.assertEquals(move_component_2_1.product_uom_qty, 1)
        move_component_2_2 = moves_internal_2.filtered(
            lambda m: m.product_id == self.component_2_2)
        self.assertTrue(move_component_2_2)
        self.assertEquals(move_component_2_2.product_uom_qty, 3)
        kit_1 = product_installation_line_1.product_tmpl_kit_id
        components_install_1 = kit_1.pack_line_ids.mapped('product_id')
        fsm_install_1 = sale.fsm_order_ids.filtered(
            lambda f: f.move_internal_ids.mapped(
                'product_id') == components_install_1)
        self.assertTrue(fsm_install_1)
        self.assertEquals(fsm_install_1.move_ids.product_id, product_A)
        self.assertEquals(move_product_A.fsm_order_id, fsm_install_1)
        kit_2 = product_installation_line_2.product_tmpl_kit_id
        components_install_2 = kit_2.pack_line_ids.mapped('product_id')
        fsm_install_2 = sale.fsm_order_ids.filtered(
            lambda f: f.move_internal_ids.mapped(
                'product_id') == components_install_2)
        self.assertTrue(fsm_install_2)
        self.assertNotEquals(fsm_install_2.move_ids.product_id, product_A)
        self.assertFalse(fsm_install_2.move_ids.product_id)
        stock_location = sale.warehouse_id.lot_stock_id
        vehicle_location = sale.fsm_order_ids.mapped(
            'warehouse_id.lot_stock_id')
        self.assertEquals(
            picking_internals.mapped('location_id'), stock_location)
        self.assertEquals(
            picking_internals.mapped('location_dest_id'), vehicle_location)
        self.assertEquals(fsm_install_1.delivery_count, 1)
        self.assertEquals(fsm_install_1.internal_count, 1)
        self.assertEquals(fsm_install_2.delivery_count, 0)
        self.assertEquals(fsm_install_2.internal_count, 1)

    def test_fsm_track_line_service_installs_and_2products_dependend(self):
        product_installation_line_1 = self.env['product.product'].create({
            'name': 'Installation product 1',
            'type': 'service',
            'invoice_policy': 'delivery',
            'list_price': 300,
            'field_service_tracking': 'line',
            'installation_product': True,
            'product_tmpl_kit_id': (
                self.product_pack_detail_1.product_tmpl_id.id),
        })
        product_installation_line_2 = self.env['product.product'].create({
            'name': 'Installation product 2',
            'type': 'service',
            'invoice_policy': 'delivery',
            'list_price': 300,
            'field_service_tracking': 'line',
            'installation_product': True,
            'product_tmpl_kit_id': (
                self.product_pack_detail_2.product_tmpl_id.id),
        })
        product_A = self.env['product.product'].create({
            'name': 'Product A',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        product_B = self.env['product.product'].create({
            'name': 'Product B',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_A.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_installation_line_1.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_installation_line_2.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_B.id,
                    'product_uom_qty': 5,
                }),
            ]
        })
        line_product_installation_line_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == product_installation_line_1)
        self.assertEquals(len(line_product_installation_line_1), 1)
        line_product_A = sale.order_line.filtered(
            lambda ln: ln.product_id == product_A)
        self.assertEquals(len(line_product_A), 1)
        line_product_B = sale.order_line.filtered(
            lambda ln: ln.product_id == product_B)
        self.assertEquals(len(line_product_B), 1)
        self.assertFalse(line_product_A.sale_line_fsm_id)
        self.assertFalse(line_product_B.sale_line_fsm_id)
        wizard = self.env['sale.order.relate_to_installations'].with_context({
            'active_ids': sale.ids,
            'active_id': sale.id,
        }).create({})
        self.assertEquals(len(wizard.line_ids), 2)
        wizard_line_product_A = wizard.line_ids.filtered(
            lambda ln: ln.sale_line_id.product_id == product_A)
        self.assertTrue(wizard_line_product_A)
        wizard_line_product_A.sale_line_fsm_id = (
            line_product_installation_line_1.id)
        wizard_line_product_B = wizard.line_ids.filtered(
            lambda ln: ln.sale_line_id.product_id == product_B)
        self.assertTrue(wizard_line_product_B)
        wizard_line_product_B.sale_line_fsm_id = (
            line_product_installation_line_1.id)
        wizard.button_accept()
        self.assertEquals(
            line_product_A.sale_line_fsm_id, line_product_installation_line_1)
        self.assertEquals(
            line_product_B.sale_line_fsm_id, line_product_installation_line_1)
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 2)
        self.assertEquals(len(sale.picking_ids), 3)
        picking_out = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing')
        self.assertEquals(len(picking_out), 1)
        self.assertEquals(len(picking_out.move_lines), 2)
        moves_out = picking_out.move_lines
        move_product_A = moves_out.filtered(
            lambda m: m.product_id == product_A)
        self.assertTrue(move_product_A)
        self.assertEquals(move_product_A.product_uom_qty, 1)
        move_product_B = moves_out.filtered(
            lambda m: m.product_id == product_B)
        self.assertTrue(move_product_B)
        self.assertEquals(move_product_B.product_uom_qty, 5)
        move_product_installation_line_1 = moves_out.filtered(
            lambda m: m.product_id == product_installation_line_1)
        self.assertFalse(move_product_installation_line_1)
        picking_internals = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'internal')
        self.assertEquals(len(picking_internals), 2)
        picking_internal_1 = picking_internals.filtered(
            lambda p: self.component_1_1 in p.move_lines.mapped('product_id'))
        self.assertEquals(len(picking_internal_1), 1)
        self.assertEquals(picking_internal_1.origin, sale.name)
        self.assertEquals(len(picking_internal_1.move_lines), 2)
        moves_internal_1 = picking_internal_1.move_lines
        move_component_1_1 = moves_internal_1.filtered(
            lambda m: m.product_id == self.component_1_1)
        self.assertTrue(move_component_1_1)
        self.assertEquals(move_component_1_1.product_uom_qty, 1)
        move_component_1_2 = moves_internal_1.filtered(
            lambda m: m.product_id == self.component_1_2)
        self.assertTrue(move_component_1_2)
        self.assertEquals(move_component_1_2.product_uom_qty, 2)
        picking_internal_2 = picking_internals.filtered(
            lambda p: self.component_2_1 in p.move_lines.mapped('product_id'))
        self.assertEquals(len(picking_internal_2), 1)
        self.assertEquals(picking_internal_2.origin, sale.name)
        self.assertEquals(len(picking_internal_2.move_lines), 2)
        moves_internal_2 = picking_internal_2.move_lines
        move_component_2_1 = moves_internal_2.filtered(
            lambda m: m.product_id == self.component_2_1)
        self.assertTrue(move_component_2_1)
        self.assertEquals(move_component_2_1.product_uom_qty, 1)
        move_component_2_2 = moves_internal_2.filtered(
            lambda m: m.product_id == self.component_2_2)
        self.assertTrue(move_component_2_2)
        self.assertEquals(move_component_2_2.product_uom_qty, 3)
        kit_1 = product_installation_line_1.product_tmpl_kit_id
        components_install_1 = kit_1.pack_line_ids.mapped('product_id')
        fsm_install_1 = sale.fsm_order_ids.filtered(
            lambda f: f.move_internal_ids.mapped(
                'product_id') == components_install_1)
        self.assertTrue(fsm_install_1)
        move_out_product_A = fsm_install_1.move_ids.filtered(
            lambda m: m.product_id == product_A)
        self.assertEquals(len(move_out_product_A), 1)
        move_out_product_B = fsm_install_1.move_ids.filtered(
            lambda m: m.product_id == product_B)
        self.assertEquals(len(move_out_product_B), 1)
        self.assertEquals(move_product_A.fsm_order_id, fsm_install_1)
        self.assertEquals(move_product_B.fsm_order_id, fsm_install_1)
        kit_2 = product_installation_line_2.product_tmpl_kit_id
        components_install_2 = kit_2.pack_line_ids.mapped('product_id')
        fsm_install_2 = sale.fsm_order_ids.filtered(
            lambda f: f.move_internal_ids.mapped(
                'product_id') == components_install_2)
        self.assertTrue(fsm_install_2)
        move_out_product_A = fsm_install_2.move_ids.filtered(
            lambda m: m.product_id == product_A)
        self.assertFalse(move_out_product_A)
        move_out_product_B = fsm_install_2.move_ids.filtered(
            lambda m: m.product_id == product_B)
        self.assertFalse(move_out_product_B)
        stock_location = sale.warehouse_id.lot_stock_id
        vehicle_location = sale.fsm_order_ids.mapped(
            'warehouse_id.lot_stock_id')
        self.assertEquals(
            picking_internals.mapped('location_id'), stock_location)
        self.assertEquals(
            picking_internals.mapped('location_dest_id'), vehicle_location)
        self.assertEquals(fsm_install_1.delivery_count, 1)
        self.assertEquals(fsm_install_1.internal_count, 1)
        self.assertEquals(fsm_install_2.delivery_count, 0)
        self.assertEquals(fsm_install_2.internal_count, 1)

    def test_fsm_track_line_2service_installs_and_3products_dependend1(self):
        product_installation_line_1 = self.env['product.product'].create({
            'name': 'Installation product 1',
            'type': 'service',
            'invoice_policy': 'delivery',
            'list_price': 300,
            'field_service_tracking': 'line',
            'installation_product': True,
            'product_tmpl_kit_id': (
                self.product_pack_detail_1.product_tmpl_id.id),
        })
        product_installation_line_2 = self.env['product.product'].create({
            'name': 'Installation product 2',
            'type': 'service',
            'invoice_policy': 'delivery',
            'list_price': 300,
            'field_service_tracking': 'line',
            'installation_product': True,
            'product_tmpl_kit_id': (
                self.product_pack_detail_2.product_tmpl_id.id),
        })
        product_A = self.env['product.product'].create({
            'name': 'Product A',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        product_B = self.env['product.product'].create({
            'name': 'Product B',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        product_C = self.env['product.product'].create({
            'name': 'Product C',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_A.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_installation_line_1.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_installation_line_2.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_B.id,
                    'product_uom_qty': 5,
                }),
                (0, 0, {
                    'product_id': product_C.id,
                    'product_uom_qty': 3,
                }),
            ]
        })
        line_product_installation_line_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == product_installation_line_1)
        self.assertEquals(len(line_product_installation_line_1), 1)
        line_product_A = sale.order_line.filtered(
            lambda ln: ln.product_id == product_A)
        self.assertEquals(len(line_product_A), 1)
        line_product_B = sale.order_line.filtered(
            lambda ln: ln.product_id == product_B)
        self.assertEquals(len(line_product_B), 1)
        line_product_C = sale.order_line.filtered(
            lambda ln: ln.product_id == product_C)
        self.assertEquals(len(line_product_C), 1)
        self.assertFalse(line_product_B.sale_line_fsm_id)
        wizard = self.env['sale.order.relate_to_installations'].with_context({
            'active_ids': sale.ids,
            'active_id': sale.id,
        }).create({})
        self.assertEquals(len(wizard.line_ids), 3)
        wizard_line_product_A = wizard.line_ids.filtered(
            lambda ln: ln.sale_line_id.product_id == product_A)
        self.assertTrue(wizard_line_product_A)
        wizard_line_product_A.sale_line_fsm_id = (
            line_product_installation_line_1.id)
        wizard_line_product_B = wizard.line_ids.filtered(
            lambda ln: ln.sale_line_id.product_id == product_B)
        self.assertTrue(wizard_line_product_B)
        wizard_line_product_B.sale_line_fsm_id = (
            line_product_installation_line_1.id)
        wizard_line_product_C = wizard.line_ids.filtered(
            lambda ln: ln.sale_line_id.product_id == product_C)
        self.assertTrue(wizard_line_product_C)
        wizard_line_product_C.sale_line_fsm_id = (
            line_product_installation_line_1.id)
        wizard.button_accept()
        self.assertEquals(
            line_product_A.sale_line_fsm_id, line_product_installation_line_1)
        self.assertEquals(
            line_product_B.sale_line_fsm_id, line_product_installation_line_1)
        self.assertEquals(
            line_product_C.sale_line_fsm_id, line_product_installation_line_1)
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 2)
        self.assertEquals(len(sale.picking_ids), 3)
        picking_out = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing')
        self.assertEquals(len(picking_out), 1)
        self.assertEquals(len(picking_out.move_lines), 3)
        moves_out = picking_out.move_lines
        move_product_A = moves_out.filtered(
            lambda m: m.product_id == product_A)
        self.assertTrue(move_product_A)
        self.assertEquals(move_product_A.product_uom_qty, 1)
        move_product_B = moves_out.filtered(
            lambda m: m.product_id == product_B)
        self.assertTrue(move_product_B)
        self.assertEquals(move_product_B.product_uom_qty, 5)
        move_product_C = moves_out.filtered(
            lambda m: m.product_id == product_C)
        self.assertTrue(move_product_C)
        self.assertEquals(move_product_C.product_uom_qty, 3)
        move_product_installation_line_1 = moves_out.filtered(
            lambda m: m.product_id == product_installation_line_1)
        self.assertFalse(move_product_installation_line_1)
        picking_internals = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'internal')
        self.assertEquals(len(picking_internals), 2)
        picking_internal_1 = picking_internals.filtered(
            lambda p: self.component_1_1 in p.move_lines.mapped('product_id'))
        self.assertEquals(len(picking_internal_1), 1)
        self.assertEquals(picking_internal_1.origin, sale.name)
        self.assertEquals(len(picking_internal_1.move_lines), 2)
        moves_internal_1 = picking_internal_1.move_lines
        move_component_1_1 = moves_internal_1.filtered(
            lambda m: m.product_id == self.component_1_1)
        self.assertTrue(move_component_1_1)
        self.assertEquals(move_component_1_1.product_uom_qty, 1)
        move_component_1_2 = moves_internal_1.filtered(
            lambda m: m.product_id == self.component_1_2)
        self.assertTrue(move_component_1_2)
        self.assertEquals(move_component_1_2.product_uom_qty, 2)
        picking_internal_2 = picking_internals.filtered(
            lambda p: self.component_2_1 in p.move_lines.mapped('product_id'))
        self.assertEquals(len(picking_internal_2), 1)
        self.assertEquals(picking_internal_2.origin, sale.name)
        self.assertEquals(len(picking_internal_2.move_lines), 2)
        moves_internal_2 = picking_internal_2.move_lines
        move_component_2_1 = moves_internal_2.filtered(
            lambda m: m.product_id == self.component_2_1)
        self.assertTrue(move_component_2_1)
        self.assertEquals(move_component_2_1.product_uom_qty, 1)
        move_component_2_2 = moves_internal_2.filtered(
            lambda m: m.product_id == self.component_2_2)
        self.assertTrue(move_component_2_2)
        self.assertEquals(move_component_2_2.product_uom_qty, 3)
        kit_1 = product_installation_line_1.product_tmpl_kit_id
        components_install_1 = kit_1.pack_line_ids.mapped('product_id')
        fsm_install_1 = sale.fsm_order_ids.filtered(
            lambda f: f.move_internal_ids.mapped(
                'product_id') == components_install_1)
        self.assertTrue(fsm_install_1)
        move_out_product_A = fsm_install_1.move_ids.filtered(
            lambda m: m.product_id == product_A)
        self.assertEquals(len(move_out_product_A), 1)
        move_out_product_B = fsm_install_1.move_ids.filtered(
            lambda m: m.product_id == product_B)
        self.assertEquals(len(move_out_product_B), 1)
        move_out_product_C = fsm_install_1.move_ids.filtered(
            lambda m: m.product_id == product_C)
        self.assertEquals(len(move_out_product_C), 1)
        self.assertEquals(move_product_A.fsm_order_id, fsm_install_1)
        self.assertEquals(move_product_B.fsm_order_id, fsm_install_1)
        self.assertEquals(move_product_C.fsm_order_id, fsm_install_1)
        kit_2 = product_installation_line_2.product_tmpl_kit_id
        components_install_2 = kit_2.pack_line_ids.mapped('product_id')
        fsm_install_2 = sale.fsm_order_ids.filtered(
            lambda f: f.move_internal_ids.mapped(
                'product_id') == components_install_2)
        self.assertTrue(fsm_install_2)
        move_out_product_A = fsm_install_2.move_ids.filtered(
            lambda m: m.product_id == product_A)
        self.assertFalse(move_out_product_A)
        move_out_product_B = fsm_install_2.move_ids.filtered(
            lambda m: m.product_id == product_B)
        self.assertFalse(move_out_product_B)
        move_out_product_C = fsm_install_2.move_ids.filtered(
            lambda m: m.product_id == product_C)
        self.assertFalse(move_out_product_C)
        stock_location = sale.warehouse_id.lot_stock_id
        vehicle_location = sale.fsm_order_ids.mapped(
            'warehouse_id.lot_stock_id')
        self.assertEquals(
            picking_internals.mapped('location_id'), stock_location)
        self.assertEquals(
            picking_internals.mapped('location_dest_id'), vehicle_location)
        self.assertEquals(fsm_install_1.delivery_count, 1)
        self.assertEquals(fsm_install_1.internal_count, 1)
        self.assertEquals(fsm_install_2.delivery_count, 0)
        self.assertEquals(fsm_install_2.internal_count, 1)

    def test_fsm_track_line_2service_installs_and_3products_dependend_both(
            self):
        product_installation_line_1 = self.env['product.product'].create({
            'name': 'Installation product 1',
            'type': 'service',
            'invoice_policy': 'delivery',
            'list_price': 300,
            'field_service_tracking': 'line',
            'installation_product': True,
            'product_tmpl_kit_id': (
                self.product_pack_detail_1.product_tmpl_id.id),
        })
        product_installation_line_2 = self.env['product.product'].create({
            'name': 'Installation product 2',
            'type': 'service',
            'invoice_policy': 'delivery',
            'list_price': 300,
            'field_service_tracking': 'line',
            'installation_product': True,
            'product_tmpl_kit_id': (
                self.product_pack_detail_2.product_tmpl_id.id),
        })
        product_A = self.env['product.product'].create({
            'name': 'Product A',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        product_B = self.env['product.product'].create({
            'name': 'Product B',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        product_C = self.env['product.product'].create({
            'name': 'Product C',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_A.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_installation_line_1.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_installation_line_2.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_B.id,
                    'product_uom_qty': 5,
                }),
                (0, 0, {
                    'product_id': product_C.id,
                    'product_uom_qty': 3,
                }),
            ]
        })
        line_product_installation_line_1 = sale.order_line.filtered(
            lambda ln: ln.product_id == product_installation_line_1)
        self.assertEquals(len(line_product_installation_line_1), 1)
        line_product_A = sale.order_line.filtered(
            lambda ln: ln.product_id == product_A)
        self.assertEquals(len(line_product_A), 1)
        line_product_B = sale.order_line.filtered(
            lambda ln: ln.product_id == product_B)
        self.assertEquals(len(line_product_B), 1)
        line_product_C = sale.order_line.filtered(
            lambda ln: ln.product_id == product_C)
        self.assertEquals(len(line_product_C), 1)
        line_product_installation_line_2 = sale.order_line.filtered(
            lambda ln: ln.product_id == product_installation_line_2)
        self.assertEquals(len(line_product_installation_line_2), 1)
        self.assertFalse(line_product_A.sale_line_fsm_id)
        self.assertFalse(line_product_B.sale_line_fsm_id)
        self.assertFalse(line_product_C.sale_line_fsm_id)
        wizard = self.env['sale.order.relate_to_installations'].with_context({
            'active_ids': sale.ids,
            'active_id': sale.id,
        }).create({})
        self.assertEquals(len(wizard.line_ids), 3)
        wizard_line_product_A = wizard.line_ids.filtered(
            lambda ln: ln.sale_line_id.product_id == product_A)
        self.assertTrue(wizard_line_product_A)
        wizard_line_product_A.sale_line_fsm_id = (
            line_product_installation_line_1.id)
        wizard_line_product_B = wizard.line_ids.filtered(
            lambda ln: ln.sale_line_id.product_id == product_B)
        self.assertTrue(wizard_line_product_B)
        wizard_line_product_B.sale_line_fsm_id = (
            line_product_installation_line_1.id)
        wizard_line_product_C = wizard.line_ids.filtered(
            lambda ln: ln.sale_line_id.product_id == product_C)
        self.assertTrue(wizard_line_product_C)
        wizard_line_product_C.sale_line_fsm_id = (
            line_product_installation_line_2.id)
        wizard.button_accept()
        self.assertEquals(
            line_product_A.sale_line_fsm_id, line_product_installation_line_1)
        self.assertEquals(
            line_product_B.sale_line_fsm_id, line_product_installation_line_1)
        self.assertEquals(
            line_product_C.sale_line_fsm_id, line_product_installation_line_2)
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 2)
        self.assertEquals(len(sale.picking_ids), 4)
        pickings_out = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing')
        self.assertEquals(len(pickings_out), 2)
        picking_out_1 = pickings_out.filtered(
            lambda p: product_A in p.move_lines.mapped('product_id'))
        self.assertEquals(len(picking_out_1), 1)
        self.assertEquals(len(picking_out_1.move_lines), 2)
        moves_out_1 = picking_out_1.move_lines
        move_product_A = moves_out_1.filtered(
            lambda m: m.product_id == product_A)
        self.assertTrue(move_product_A)
        self.assertEquals(move_product_A.product_uom_qty, 1)
        move_product_B = moves_out_1.filtered(
            lambda m: m.product_id == product_B)
        self.assertTrue(move_product_B)
        picking_out_2 = pickings_out.filtered(
            lambda p: product_C == p.move_lines.mapped('product_id'))
        self.assertEquals(len(picking_out_2), 1)
        self.assertEquals(len(picking_out_2.move_lines), 1)
        moves_out_2 = picking_out_2.move_lines
        move_product_C = moves_out_2.filtered(
            lambda m: m.product_id == product_C)
        self.assertTrue(move_product_C)
        self.assertEquals(move_product_C.product_uom_qty, 3)
        move_product_installation_line_1 = moves_out_1.filtered(
            lambda m: m.product_id == product_installation_line_1)
        self.assertFalse(move_product_installation_line_1)
        move_product_installation_line_1 = moves_out_2.filtered(
            lambda m: m.product_id == product_installation_line_1)
        self.assertFalse(move_product_installation_line_1)
        move_product_installation_line_2 = moves_out_1.filtered(
            lambda m: m.product_id == product_installation_line_2)
        self.assertFalse(move_product_installation_line_2)
        move_product_installation_line_2 = moves_out_2.filtered(
            lambda m: m.product_id == product_installation_line_2)
        self.assertFalse(move_product_installation_line_2)
        picking_internals = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'internal')
        self.assertEquals(len(picking_internals), 2)
        picking_internal_1 = picking_internals.filtered(
            lambda p: self.component_1_1 in p.move_lines.mapped('product_id'))
        self.assertEquals(len(picking_internal_1), 1)
        self.assertEquals(picking_internal_1.origin, sale.name)
        self.assertEquals(len(picking_internal_1.move_lines), 2)
        moves_internal_1 = picking_internal_1.move_lines
        move_component_1_1 = moves_internal_1.filtered(
            lambda m: m.product_id == self.component_1_1)
        self.assertTrue(move_component_1_1)
        self.assertEquals(move_component_1_1.product_uom_qty, 1)
        move_component_1_2 = moves_internal_1.filtered(
            lambda m: m.product_id == self.component_1_2)
        self.assertTrue(move_component_1_2)
        self.assertEquals(move_component_1_2.product_uom_qty, 2)
        picking_internal_2 = picking_internals.filtered(
            lambda p: self.component_2_1 in p.move_lines.mapped('product_id'))
        self.assertEquals(len(picking_internal_2), 1)
        self.assertEquals(picking_internal_2.origin, sale.name)
        self.assertEquals(len(picking_internal_2.move_lines), 2)
        moves_internal_2 = picking_internal_2.move_lines
        move_component_2_1 = moves_internal_2.filtered(
            lambda m: m.product_id == self.component_2_1)
        self.assertTrue(move_component_2_1)
        self.assertEquals(move_component_2_1.product_uom_qty, 1)
        move_component_2_2 = moves_internal_2.filtered(
            lambda m: m.product_id == self.component_2_2)
        self.assertTrue(move_component_2_2)
        self.assertEquals(move_component_2_2.product_uom_qty, 3)
        kit_1 = product_installation_line_1.product_tmpl_kit_id
        components_install_1 = kit_1.pack_line_ids.mapped('product_id')
        fsm_install_1 = sale.fsm_order_ids.filtered(
            lambda f: f.move_internal_ids.mapped(
                'product_id') == components_install_1)
        self.assertTrue(fsm_install_1)
        move_out_product_A = fsm_install_1.move_ids.filtered(
            lambda m: m.product_id == product_A)
        self.assertEquals(len(move_out_product_A), 1)
        move_out_product_B = fsm_install_1.move_ids.filtered(
            lambda m: m.product_id == product_B)
        self.assertEquals(len(move_out_product_B), 1)
        move_out_product_C = fsm_install_1.move_ids.filtered(
            lambda m: m.product_id == product_C)
        self.assertFalse(move_out_product_C)
        self.assertEquals(move_product_A.fsm_order_id, fsm_install_1)
        self.assertEquals(move_product_B.fsm_order_id, fsm_install_1)
        kit_2 = product_installation_line_2.product_tmpl_kit_id
        components_install_2 = kit_2.pack_line_ids.mapped('product_id')
        fsm_install_2 = sale.fsm_order_ids.filtered(
            lambda f: f.move_internal_ids.mapped(
                'product_id') == components_install_2)
        self.assertTrue(fsm_install_2)
        move_out_product_A = fsm_install_2.move_ids.filtered(
            lambda m: m.product_id == product_A)
        self.assertFalse(move_out_product_A)
        move_out_product_B = fsm_install_2.move_ids.filtered(
            lambda m: m.product_id == product_B)
        self.assertFalse(move_out_product_B)
        move_out_product_C = fsm_install_2.move_ids.filtered(
            lambda m: m.product_id == product_C)
        self.assertEquals(len(move_out_product_C), 1)
        self.assertEquals(move_product_C.fsm_order_id, fsm_install_2)
        stock_location = sale.warehouse_id.lot_stock_id
        vehicle_location = sale.fsm_order_ids.mapped(
            'warehouse_id.lot_stock_id')
        self.assertEquals(
            picking_internals.mapped('location_id'), stock_location)
        self.assertEquals(
            picking_internals.mapped('location_dest_id'), vehicle_location)
        self.assertEquals(fsm_install_1.delivery_count, 1)
        self.assertEquals(fsm_install_1.internal_count, 1)
        self.assertEquals(fsm_install_2.delivery_count, 1)
        self.assertEquals(fsm_install_2.internal_count, 1)

    def test_fsm_track_sale_2service_installs_and_product_independend(self):
        product_installation_line_1 = self.env['product.product'].create({
            'name': 'Installation product 1',
            'type': 'service',
            'invoice_policy': 'delivery',
            'list_price': 300,
            'field_service_tracking': 'sale',
            'installation_product': True,
            'product_tmpl_kit_id': (
                self.product_pack_detail_1.product_tmpl_id.id),
        })
        product_installation_line_2 = self.env['product.product'].create({
            'name': 'Installation product 2',
            'type': 'service',
            'invoice_policy': 'delivery',
            'list_price': 300,
            'field_service_tracking': 'sale',
            'installation_product': True,
            'product_tmpl_kit_id': (
                self.product_pack_detail_2.product_tmpl_id.id),
        })
        product_A = self.env['product.product'].create({
            'name': 'Product A',
            'type': 'product',
            'invoice_policy': 'delivery',
            'list_price': 100,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'fsm_location_id': self.location.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_A.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_installation_line_1.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': product_installation_line_2.id,
                    'product_uom_qty': 1,
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.fsm_order_ids), 1)
        self.assertEquals(len(sale.picking_ids), 3)
        picking_out = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'outgoing')
        self.assertEquals(len(picking_out), 1)
        self.assertEquals(len(picking_out.move_lines), 1)
        moves_out = picking_out.move_lines
        self.assertFalse(moves_out.mapped('fsm_order_id'))
        move_product_A = moves_out.filtered(
            lambda m: m.product_id == product_A)
        self.assertTrue(move_product_A)
        self.assertEquals(move_product_A.product_uom_qty, 1)
        move_product_installation_line_1 = moves_out.filtered(
            lambda m: m.product_id == product_installation_line_1)
        self.assertFalse(move_product_installation_line_1)
        move_product_installation_line_2 = moves_out.filtered(
            lambda m: m.product_id == product_installation_line_2)
        self.assertFalse(move_product_installation_line_2)
        picking_internals = sale.picking_ids.filtered(
            lambda p: p.picking_type_id.code == 'internal')
        self.assertEquals(len(picking_internals), 2)
        picking_internal_1 = picking_internals.filtered(
            lambda p: self.component_1_1 in p.move_lines.mapped('product_id'))
        self.assertEquals(len(picking_internal_1), 1)
        self.assertEquals(picking_internal_1.origin, sale.name)
        self.assertEquals(len(picking_internal_1.move_lines), 2)
        moves_internal_1 = picking_internal_1.move_lines
        move_component_1_1 = moves_internal_1.filtered(
            lambda m: m.product_id == self.component_1_1)
        self.assertTrue(move_component_1_1)
        self.assertEquals(move_component_1_1.product_uom_qty, 1)
        move_component_1_2 = moves_internal_1.filtered(
            lambda m: m.product_id == self.component_1_2)
        self.assertTrue(move_component_1_2)
        self.assertEquals(move_component_1_2.product_uom_qty, 2)
        picking_internal_2 = picking_internals.filtered(
            lambda p: self.component_2_1 in p.move_lines.mapped('product_id'))
        self.assertEquals(len(picking_internal_2), 1)
        self.assertEquals(picking_internal_2.origin, sale.name)
        self.assertEquals(len(picking_internal_2.move_lines), 2)
        moves_internal_2 = picking_internal_2.move_lines
        move_component_2_1 = moves_internal_2.filtered(
            lambda m: m.product_id == self.component_2_1)
        self.assertTrue(move_component_2_1)
        self.assertEquals(move_component_2_1.product_uom_qty, 1)
        move_component_2_2 = moves_internal_2.filtered(
            lambda m: m.product_id == self.component_2_2)
        self.assertTrue(move_component_2_2)
        self.assertEquals(move_component_2_2.product_uom_qty, 3)
        stock_location = sale.warehouse_id.lot_stock_id
        vehicle_location = sale.fsm_order_ids.mapped(
            'warehouse_id.lot_stock_id')
        self.assertEquals(
            picking_internals.mapped('location_id'), stock_location)
        self.assertEquals(
            picking_internals.mapped('location_dest_id'), vehicle_location)
        self.assertFalse(sale.fsm_order_ids.mapped('move_ids'))
        self.assertTrue(
            set(moves_internal_1.ids).issubset(
                sale.fsm_order_ids.mapped('move_internal_ids').ids))
        self.assertEquals(sale.fsm_order_ids.delivery_count, 1)
        self.assertEquals(sale.fsm_order_ids.internal_count, 2)
