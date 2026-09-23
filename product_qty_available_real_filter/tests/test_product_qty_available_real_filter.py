###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductQtyAvailableRealFilter(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product a',
            'default_code': 'product_stock_1',
            'standard_price': 10,
            'list_price': 100,
        })
        self.location = self.env.ref('stock.stock_location_stock')
        attributevalue_obj = self.env['product.attribute.value']
        product_attribute_test_color = self.env['product.attribute'].create({
            'name': 'Test Color',
            'create_variant': 'always',
        })
        product_attribute_value_color_red = attributevalue_obj.create({
            'name': 'Test Red',
            'attribute_id': product_attribute_test_color.id,
        })
        product_attribute_value_color_gray = attributevalue_obj.create({
            'name': 'Test Gray',
            'attribute_id': product_attribute_test_color.id,
        })
        product_attribute_value_color_blue = attributevalue_obj.create({
            'name': 'Test Blue',
            'attribute_id': product_attribute_test_color.id,
        })
        self.tmpl_with_variants = self.env['product.template'].create({
            'name': 'Product b',
            'type': 'product',
            'company_id': False,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': product_attribute_test_color.id,
                    'value_ids': [(6, 0, [
                        product_attribute_value_color_red.id,
                        product_attribute_value_color_gray.id,
                        product_attribute_value_color_blue.id,
                    ])],
                })
            ]
        })
        self.assertEqual(len(self.tmpl_with_variants.product_variant_ids), 3)
        self.product_red = (
            self.tmpl_with_variants.product_variant_ids.filtered(
                lambda p: p.attribute_value_ids
                == product_attribute_value_color_red))
        self.product_gray = (
            self.tmpl_with_variants.product_variant_ids.filtered(
                lambda p: p.attribute_value_ids
                == product_attribute_value_color_gray))
        self.product_blue = (
            self.tmpl_with_variants.product_variant_ids.filtered(
                lambda p: p.attribute_value_ids
                == product_attribute_value_color_blue))

    def test_search_qty_available_real_unique_variant(self):
        self.env['stock.quant']._update_available_quantity(
            self.product, self.location, 10)
        self.assertEqual(self.product.qty_available, 10)
        self.assertEqual(self.product.qty_available_real, 10)
        product_obj = self.env['product.product']
        template_obj = self.env['product.template']
        product_with_real_stock = product_obj.search([
            ('qty_available_real', '>', 0),
            ('default_code', '=', 'product_stock_1'),
        ])
        self.assertEqual(len(product_with_real_stock), 1)
        template_with_real_stock = template_obj.search([
            ('qty_available_real', '>', 0),
            ('default_code', '=', 'product_stock_1'),
        ])
        self.assertEqual(len(template_with_real_stock), 1)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 10,
            })]
        })
        sale.action_confirm()
        self.assertEqual(self.product.qty_available, 10)
        self.assertEqual(self.product.qty_available_real, 0)
        product_with_real_stock = product_obj.search([
            ('qty_available_real', '>', 0),
            ('default_code', '=', 'product_stock_1'),
        ])
        self.assertEqual(len(product_with_real_stock), 0)
        template_with_real_stock = template_obj.search([
            ('qty_available_real', '>', 0),
            ('default_code', '=', 'product_stock_1'),
        ])
        self.assertEqual(len(template_with_real_stock), 0)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(self.product.qty_available, 0)
        self.assertEqual(self.product.qty_available_real, 0)
        product_with_real_stock = product_obj.search([
            ('qty_available_real', '>', 0),
            ('default_code', '=', 'product_stock_1'),
        ])
        self.assertEqual(len(product_with_real_stock), 0)
        template_with_real_stock = template_obj.search([
            ('qty_available_real', '>', 0),
            ('default_code', '=', 'product_stock_1'),
        ])
        self.assertEqual(len(template_with_real_stock), 0)

    def test_search_qty_available_real_with_variants(self):
        stock_quant_obj = self.env['stock.quant']
        product_obj = self.env['product.product']
        stock_quant_obj._update_available_quantity(
            self.product_red, self.location, 5)
        stock_quant_obj._update_available_quantity(
            self.product_gray, self.location, 10)
        stock_quant_obj._update_available_quantity(
            self.product_blue, self.location, 15)
        self.assertEqual(self.product_red.qty_available, 5)
        self.assertEqual(self.product_red.qty_available_real, 5)
        self.assertEqual(self.product_gray.qty_available, 10)
        self.assertEqual(self.product_gray.qty_available_real, 10)
        self.assertEqual(self.product_blue.qty_available, 15)
        self.assertEqual(self.product_blue.qty_available_real, 15)
        products_with_real_stock = product_obj.search([
            ('qty_available_real', '>', 0),
            ('id', 'in', self.tmpl_with_variants.product_variant_ids.ids),
        ])
        self.assertEqual(len(products_with_real_stock), 3)
        self.assertEqual(self.tmpl_with_variants.qty_available, 30)
        self.assertEqual(self.tmpl_with_variants.qty_available_real, 30)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_red.id,
                    'product_uom_qty': 5,
                }),
                (0, 0, {
                    'product_id': self.product_gray.id,
                    'product_uom_qty': 5,
                }),
                (0, 0, {
                    'product_id': self.product_blue.id,
                    'product_uom_qty': 5,
                })
            ]
        })
        sale.action_confirm()
        self.assertEqual(self.product_red.qty_available, 5)
        self.assertEqual(self.product_red.qty_available_real, 0)
        self.assertEqual(self.product_gray.qty_available, 10)
        self.assertEqual(self.product_gray.qty_available_real, 5)
        self.assertEqual(self.product_blue.qty_available, 15)
        self.assertEqual(self.product_blue.qty_available_real, 10)
        self.assertEqual(self.tmpl_with_variants.qty_available, 30)
        self.assertEqual(self.tmpl_with_variants.qty_available_real, 15)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(self.product_red.qty_available, 0)
        self.assertEqual(self.product_red.qty_available_real, 0)
        self.assertEqual(self.product_gray.qty_available, 5)
        self.assertEqual(self.product_gray.qty_available_real, 5)
        self.assertEqual(self.product_blue.qty_available, 10)
        self.assertEqual(self.product_blue.qty_available_real, 10)
        self.assertEqual(self.tmpl_with_variants.qty_available, 15)
        self.assertEqual(self.tmpl_with_variants.qty_available_real, 15)
        products_with_real_stock = product_obj.search([
            ('qty_available_real', '>', 0),
            ('id', 'in', self.tmpl_with_variants.product_variant_ids.ids),
        ])
        self.assertEqual(len(products_with_real_stock), 2)
