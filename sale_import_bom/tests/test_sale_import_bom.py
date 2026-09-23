###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _
from odoo.exceptions import UserError
from odoo.tests import common


class TestSaleImportBom(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner Test',
        })
        mrp_route = self.env.ref('mrp.route_warehouse0_manufacture')
        self.product_main = self.env['product.product'].create({
            'name': 'Test Product Main',
            'type': 'product',
            'route_ids': [(6, 0, mrp_route.ids)],
        })
        self.product_comp_one = self.env['product.product'].create({
            'name': 'Test Component One',
            'type': 'product',
            'route_ids': [(6, 0, mrp_route.ids)],
        })
        self.product_comp_two = self.env['product.product'].create({
            'name': 'Test Component Two',
            'type': 'product',
            'route_ids': [(6, 0, mrp_route.ids)],
        })
        self.product_other = self.env['product.product'].create({
            'name': 'Test Component Other',
            'type': 'product',
            'route_ids': [(6, 0, mrp_route.ids)],
        })
        self.bom = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_main.product_tmpl_id.id,
            'product_uom_id': self.product_main.uom_id.id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.product_comp_one.id,
                    'product_qty': 2,
                    'product_uom_id': self.product_comp_one.uom_id.id,
                }),
                (0, 0, {
                    'product_id': self.product_comp_two.id,
                    'product_qty': 3,
                    'product_uom_id': self.product_comp_two.uom_id.id,
                }),
            ],
        })
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })

    def test_wizard_fields_default_values(self):
        wizard = self.env['wiz.sale_import_bom'].create({
            'order_id': self.sale_order.id,
            'bom_id': self.bom.id,
        })
        self.assertEqual(wizard.quantity, 1.0)
        self.assertFalse(wizard.only_import_products)

    def test_button_add_bom_without_valid_variant(self):
        product_tmpl = self.product_other.product_tmpl_id
        bom_no_variant = self.env['mrp.bom'].create({
            'product_tmpl_id': product_tmpl.id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.product_comp_one.id,
                    'product_qty': 2,
                    'product_uom_id': self.product_comp_one.uom_id.id,
                }),
            ],
        })
        self.product_other.active = False
        wizard = self.env['wiz.sale_import_bom'].create({
            'order_id': self.sale_order.id,
            'bom_id': bom_no_variant.id,
            'only_import_products': False,
        })
        with self.assertRaises(UserError) as result:
            wizard.button_add()
        expected_msg = _('The bill of materials does not have a valid variant.')
        self.assertEqual(result.exception.args[0], expected_msg)

    def test_button_add_bom_without_variant_only_products(self):
        bom_no_variant = self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_other.product_tmpl_id.id,
            'product_qty': 1,
            'bom_line_ids': [
                (0, 0, {
                    'product_id': self.product_comp_one.id,
                    'product_qty': 2,
                    'product_uom_id': self.product_comp_one.uom_id.id,
                }),
            ],
        })
        wizard = self.env['wiz.sale_import_bom'].create({
            'order_id': self.sale_order.id,
            'bom_id': bom_no_variant.id,
            'only_import_products': True,
        })
        result = wizard.button_add()
        self.assertEqual(result['type'], 'ir.actions.act_window_close')
        self.assertEqual(len(self.sale_order.order_line), 1)
        line = self.sale_order.order_line[0]
        self.assertEqual(line.product_id.id, self.product_comp_one.id)
        self.assertEqual(line.product_uom_qty, 2.0)

    def test_button_add_bom_full_import(self):
        wizard = self.env['wiz.sale_import_bom'].create({
            'order_id': self.sale_order.id,
            'bom_id': self.bom.id,
            'quantity': 1.0,
            'only_import_products': False,
        })
        result = wizard.button_add()
        self.assertEqual(result['type'], 'ir.actions.act_window_close')
        self.assertEqual(len(self.sale_order.order_line), 3)
        line_main = self.sale_order.order_line.filtered(
            lambda line: line.product_id.id == self.product_main.id)
        line_comp_one = self.sale_order.order_line.filtered(
            lambda line: line.product_id.id == self.product_comp_one.id)
        line_comp_two = self.sale_order.order_line.filtered(
            lambda line: line.product_id.id == self.product_comp_two.id)
        self.assertEqual(len(line_main), 1)
        self.assertEqual(line_main.product_uom_qty, 1.0)
        self.assertEqual(line_main.price_unit, 0.0)
        self.assertEqual(len(line_comp_one), 1)
        self.assertEqual(line_comp_one.product_uom_qty, 2.0)
        self.assertEqual(len(line_comp_two), 1)
        self.assertEqual(line_comp_two.product_uom_qty, 3.0)

    def test_button_add_bom_with_quantity(self):
        wizard = self.env['wiz.sale_import_bom'].create({
            'order_id': self.sale_order.id,
            'bom_id': self.bom.id,
            'quantity': 3.0,
            'only_import_products': False,
        })
        result = wizard.button_add()
        self.assertEqual(result['type'], 'ir.actions.act_window_close')
        self.assertEqual(len(self.sale_order.order_line), 3)
        line_main = self.sale_order.order_line.filtered(
            lambda line: line.product_id.id == self.product_main.id)
        line_comp_one = self.sale_order.order_line.filtered(
            lambda line: line.product_id.id == self.product_comp_one.id)
        line_comp_two = self.sale_order.order_line.filtered(
            lambda line: line.product_id.id == self.product_comp_two.id)
        self.assertEqual(line_main.product_uom_qty, 3.0)
        self.assertEqual(line_comp_one.product_uom_qty, 6.0)
        self.assertEqual(line_comp_two.product_uom_qty, 9.0)
