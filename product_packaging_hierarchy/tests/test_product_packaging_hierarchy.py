###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductPackagingHierarchy(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product_01 = self.env['product.product'].create({
            'detailed_type': 'product',
            'company_id': False,
            'name': 'Product test 01',
            'standard_price': 10,
            'list_price': 100,
        })
        self.product_02 = self.env['product.product'].create({
            'detailed_type': 'product',
            'company_id': False,
            'name': 'Product test 02',
            'standard_price': 10,
            'list_price': 100,
        })
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.customer_location = self.env.ref('stock.stock_location_customers')
        self.update_qty_on_hand(self.product_01, self.stock_location, 100)
        self.update_qty_on_hand(self.product_02, self.stock_location, 100)
        self.picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'move_ids_without_package': [
                (0, 0, {
                    'name': self.product_01.name,
                    'product_id': self.product_01.id,
                    'product_uom_qty': 10,
                    'product_uom': self.product_01.uom_id.id,
                    'location_id': self.stock_location.id,
                    'location_dest_id': self.customer_location.id,
                }),
                (0, 0, {
                    'name': self.product_02.name,
                    'product_id': self.product_02.id,
                    'product_uom_qty': 2,
                    'product_uom': self.product_02.uom_id.id,
                    'location_id': self.stock_location.id,
                    'location_dest_id': self.customer_location.id,
                }),
            ],
        })
        self.parent_package_01 = self.env['stock.quant.package'].create({
            'name': 'Parent package 01',
        })
        self.parent_package_02 = self.env['stock.quant.package'].create({
            'name': 'Parent package 02',
        })

    def update_qty_on_hand(self, product, location, new_qty):
        self.env['stock.quant']._update_available_quantity(
            product, location, new_qty)
        self.assertEqual(
            product.with_context(location=location.id).qty_available, new_qty)

    def test_put_in_pack_hierarchy_with_parent_package(self):
        self.picking.action_confirm()
        self.picking.action_assign()
        line_product_01 = self.picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_01)
        self.assertTrue(line_product_01)
        line_product_01.qty_done = 1.0
        line_product_02 = self.picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_02)
        self.assertTrue(line_product_02)
        line_product_02.qty_done = 1.0
        wizard_pack_1 = self.env['stock.quant.package.hierarchy'].with_context(
            active_model='stock.picking',
            active_ids=self.picking.ids,
        ).create({
            'parent_package_id': self.parent_package_01.id,
        })
        wizard_pack_1.action_confirm()
        move_line_pack_1_product_01 = (
            self.picking.move_line_ids.filtered(
                lambda ln: ln.product_id == self.product_01
                and ln.qty_done == 1))
        self.assertEqual(len(move_line_pack_1_product_01), 1)
        pack_1 = move_line_pack_1_product_01.result_package_id
        self.assertEqual(len(pack_1), 1)
        self.assertEqual(pack_1.parent_id, self.parent_package_01)
        self.assertEqual(self.parent_package_01.child_ids, pack_1)
        self.assertEqual(len(self.picking.package_level_ids), 1)
        move_line_pack_1_product_02 = (
            self.picking.move_line_ids.filtered(
                lambda ln: ln.product_id == self.product_02
                and ln.qty_done == 1))
        self.assertEqual(len(move_line_pack_1_product_02), 1)
        self.assertEqual(
            move_line_pack_1_product_02.result_package_id, pack_1)
        line_product_01.qty_done = 9
        line_product_02.qty_done = 1
        wizard_pack_2 = self.env['stock.quant.package.hierarchy'].with_context(
            active_model='stock.picking',
            active_ids=self.picking.ids,
        ).create({
            'parent_package_id': self.parent_package_02.id,
        })
        wizard_pack_2.action_confirm()
        move_line_pack_2_product_01 = (
            self.picking.move_line_ids.filtered(
                lambda ln: ln.product_id == self.product_01
                and ln.result_package_id != pack_1))
        self.assertEqual(len(move_line_pack_2_product_01), 1)
        move_line_pack_2_product_02 = (
            self.picking.move_line_ids.filtered(
                lambda ln: ln.product_id == self.product_02
                and ln.result_package_id != pack_1))
        self.assertEqual(len(move_line_pack_2_product_02), 1)
        self.assertEqual(
            move_line_pack_2_product_01.result_package_id,
            move_line_pack_2_product_02.result_package_id)
        pack_2 = move_line_pack_2_product_01.result_package_id
        self.assertEqual(len(pack_2), 1)
        self.assertEqual(pack_2.parent_id, self.parent_package_02)
        self.assertEqual(self.parent_package_02.child_ids, pack_2)
        self.assertEqual(len(self.picking.package_level_ids), 2)
        self.picking.button_validate()
        self.assertEqual(self.picking.state, 'done')
        self.assertEqual(len(pack_1.quant_ids), 2)
        self.assertEqual(sorted(pack_1.quant_ids.mapped('quantity')), [1, 1])
        self.assertEqual(len(pack_2.quant_ids), 2)
        self.assertEqual(sorted(pack_2.quant_ids.mapped('quantity')), [1, 9])

    def test_put_in_pack_hierarchy_without_parent_package(self):
        self.picking.action_confirm()
        self.picking.action_assign()
        line_product_01 = self.picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_01)
        self.assertTrue(line_product_01)
        line_product_01.qty_done = 1.0
        line_product_02 = self.picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_02)
        self.assertTrue(line_product_02)
        line_product_02.qty_done = 1.0
        wizard_pack_1 = self.env['stock.quant.package.hierarchy'].with_context(
            active_model='stock.picking',
            active_ids=self.picking.ids,
        ).create({})
        wizard_pack_1.action_confirm()
        move_line_pack_1_product_01 = (
            self.picking.move_line_ids.filtered(
                lambda ln: ln.product_id == self.product_01
                and ln.qty_done == 1))
        self.assertEqual(len(move_line_pack_1_product_01), 1)
        pack_1 = move_line_pack_1_product_01.result_package_id
        self.assertEqual(len(pack_1), 1)
        self.assertFalse(pack_1.parent_id)
        self.assertEqual(len(self.picking.package_level_ids), 1)
        line_product_01.qty_done = 9
        line_product_02.qty_done = 1
        wizard_pack_2 = self.env['stock.quant.package.hierarchy'].with_context(
            active_model='stock.picking',
            active_ids=self.picking.ids,
        ).create({})
        wizard_pack_2.action_confirm()
        move_line_pack_2_product_01 = (
            self.picking.move_line_ids.filtered(
                lambda ln: ln.product_id == self.product_01
                and ln.result_package_id != pack_1))
        self.assertEqual(len(move_line_pack_2_product_01), 1)
        move_line_pack_2_product_02 = (
            self.picking.move_line_ids.filtered(
                lambda ln: ln.product_id == self.product_02
                and ln.result_package_id != pack_1))
        self.assertEqual(len(move_line_pack_2_product_02), 1)
        self.assertEqual(
            move_line_pack_2_product_01.result_package_id,
            move_line_pack_2_product_02.result_package_id)
        pack_2 = move_line_pack_2_product_01.result_package_id
        self.assertEqual(len(pack_2), 1)
        self.assertFalse(pack_2.parent_id)
        self.assertEqual(len(self.picking.package_level_ids), 2)
        self.picking.button_validate()
        self.assertEqual(self.picking.state, 'done')
        self.assertEqual(len(pack_1.quant_ids), 2)
        self.assertEqual(sorted(pack_1.quant_ids.mapped('quantity')), [1, 1])
        self.assertEqual(len(pack_2.quant_ids), 2)
        self.assertEqual(sorted(pack_2.quant_ids.mapped('quantity')), [1, 9])
