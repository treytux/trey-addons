###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestStockPickingModifyQtyDoneWizard(TransactionCase):
    def setUp(self):
        super().setUp()
        self.stock_location = self.env.ref('stock.stock_location_stock')
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product_1 = self.env['product.product'].create({
            'type': 'product',
            'name': 'Product 1',
        })
        self.product_2 = self.env['product.product'].create({
            'type': 'product',
            'name': 'Product 2',
        })
        warehouse = self.env.ref('stock.warehouse0')
        customer_loc = self.env.ref('stock.stock_location_customers')
        self.picking = self.env['stock.picking'].create({
            'partner_id': partner.id,
            'picking_type_id': warehouse.out_type_id.id,
            'location_id': warehouse.out_type_id.default_location_src_id.id,
            'location_dest_id': customer_loc.id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product_1.id,
                    'name': self.product_1.name,
                    'product_uom': self.product_1.uom_id.id,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product_2.id,
                    'name': self.product_2.name,
                    'product_uom': self.product_2.uom_id.id,
                    'product_uom_qty': 2,
                }),
            ],
        })

    def get_wizard_calling_default_get(self):
        wizard = self.env['stock.picking.modify_qty_done'].new()
        res = wizard.with_context(
            active_model='stock.picking',
            active_id=self.picking.id,
            active_ids=self.picking.ids,
        ).default_get([])
        self.assertIn('line_ids', res)
        wizard.line_ids = res['line_ids']
        self.assertEquals(len(wizard.line_ids), 2)
        return wizard

    def check_new_wizard_lines_empty(self, wizard):
        line_product_1 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEqual(line_product_1.product_uom_qty, 1)
        self.assertEqual(line_product_1.reserved_availability, 0)
        self.assertEqual(line_product_1.quantity_done, 0)
        line_product_2 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEqual(line_product_2.product_uom_qty, 2)
        self.assertEqual(line_product_2.reserved_availability, 0)
        self.assertEqual(line_product_2.quantity_done, 0)

    def get_stock(self, product, location):
        return product.with_context(location=location.id).qty_available

    def update_stock(self, product, location, qty):
        wizard = self.env['stock.change.product.qty'].create({
            'product_id': product.id,
            'location_id': location.id,
            'new_quantity': qty,
        })
        wizard.change_product_qty()
        product_qty = self.get_stock(product, location)
        self.assertEquals(product_qty, qty)

    def test_fill_lines_manually(self):
        wizard = self.get_wizard_calling_default_get()
        line_product_1 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        line_product_1.quantity_done = 1
        self.assertEqual(line_product_1.product_uom_qty, 1)
        self.assertEqual(line_product_1.reserved_availability, 0)
        self.assertEqual(line_product_1.quantity_done, 1)
        line_product_2 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        line_product_2.quantity_done = 10
        self.assertEqual(line_product_2.product_uom_qty, 2)
        self.assertEqual(line_product_2.reserved_availability, 0)
        self.assertEqual(line_product_2.quantity_done, 10)
        wizard.action_modify_qty_done()
        move_product_1 = self.picking.move_lines.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertEquals(move_product_1.quantity_done, 1)
        move_product_2 = self.picking.move_lines.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertEquals(move_product_2.quantity_done, 10)

    def test_button_all_to_zero(self):
        wizard = self.get_wizard_calling_default_get()
        self.check_new_wizard_lines_empty(wizard)
        line_product_1 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        line_product_1.quantity_done = 33
        self.assertEqual(line_product_1.quantity_done, 33)
        line_product_2 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        line_product_2.quantity_done = 44
        self.assertEqual(line_product_2.quantity_done, 44)
        wizard.action_all_to_zero()
        self.assertEqual(line_product_1.product_uom_qty, 1)
        self.assertEqual(line_product_1.reserved_availability, 0)
        self.assertEqual(line_product_1.quantity_done, 0)
        self.assertEqual(line_product_2.product_uom_qty, 2)
        self.assertEqual(line_product_2.reserved_availability, 0)
        self.assertEqual(line_product_2.quantity_done, 0)
        wizard.action_modify_qty_done()
        move_product_1 = self.picking.move_lines.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertEquals(move_product_1.quantity_done, 0)
        move_product_2 = self.picking.move_lines.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertEquals(move_product_2.quantity_done, 0)

    def test_button_all_to_reserved(self):
        self.update_stock(self.product_1, self.stock_location, 100)
        self.picking.action_confirm()
        self.picking.action_assign()
        wizard = self.get_wizard_calling_default_get()
        line_product_1 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEqual(line_product_1.product_uom_qty, 1)
        self.assertEqual(line_product_1.reserved_availability, 1)
        self.assertEqual(line_product_1.quantity_done, 0)
        line_product_2 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEqual(line_product_2.product_uom_qty, 2)
        self.assertEqual(line_product_2.reserved_availability, 0)
        self.assertEqual(line_product_2.quantity_done, 0)
        line_product_1 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        line_product_1.quantity_done = 33
        self.assertEqual(line_product_1.quantity_done, 33)
        line_product_2 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        line_product_2.quantity_done = 44
        self.assertEqual(line_product_2.quantity_done, 44)
        wizard.action_all_to_reserved()
        self.assertEqual(line_product_1.product_uom_qty, 1)
        self.assertEqual(line_product_1.reserved_availability, 1)
        self.assertEqual(line_product_1.quantity_done, 1)
        self.assertEqual(line_product_2.product_uom_qty, 2)
        self.assertEqual(line_product_2.reserved_availability, 0)
        self.assertEqual(line_product_2.quantity_done, 0)
        wizard.action_modify_qty_done()
        move_product_1 = self.picking.move_lines.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertEquals(move_product_1.quantity_done, 1)
        move_product_2 = self.picking.move_lines.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertEquals(move_product_2.quantity_done, 0)

    def test_button_all_to_necessary(self):
        self.update_stock(self.product_1, self.stock_location, 100)
        self.picking.action_confirm()
        self.picking.action_assign()
        wizard = self.get_wizard_calling_default_get()
        line_product_1 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        self.assertEqual(line_product_1.product_uom_qty, 1)
        self.assertEqual(line_product_1.reserved_availability, 1)
        self.assertEqual(line_product_1.quantity_done, 0)
        line_product_2 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        self.assertEqual(line_product_2.product_uom_qty, 2)
        self.assertEqual(line_product_2.reserved_availability, 0)
        self.assertEqual(line_product_2.quantity_done, 0)
        line_product_1 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_1)
        self.assertTrue(line_product_1)
        line_product_1.quantity_done = 33
        self.assertEqual(line_product_1.quantity_done, 33)
        line_product_2 = wizard.line_ids.filtered(
            lambda ln: ln.product_id == self.product_2)
        self.assertTrue(line_product_2)
        line_product_2.quantity_done = 44
        self.assertEqual(line_product_2.quantity_done, 44)
        wizard.action_all_to_necessary()
        self.assertEqual(line_product_1.product_uom_qty, 1)
        self.assertEqual(line_product_1.reserved_availability, 1)
        self.assertEqual(line_product_1.quantity_done, 1)
        self.assertEqual(line_product_2.product_uom_qty, 2)
        self.assertEqual(line_product_2.reserved_availability, 0)
        self.assertEqual(line_product_2.quantity_done, 2)
        wizard.action_modify_qty_done()
        move_product_1 = self.picking.move_lines.filtered(
            lambda m: m.product_id == self.product_1)
        self.assertEquals(move_product_1.quantity_done, 1)
        move_product_2 = self.picking.move_lines.filtered(
            lambda m: m.product_id == self.product_2)
        self.assertEquals(move_product_2.quantity_done, 2)
