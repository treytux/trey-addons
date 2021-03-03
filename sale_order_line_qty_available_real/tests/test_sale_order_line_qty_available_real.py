###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _
from odoo.tests import common


class TestSaleOrderLineQuantityAvailableReal(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Product product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.location = self.env.ref('stock.stock_location_stock')

    def test_sale_order_line_qty_available_real(self):
        quantity = 100.0
        quant = self.env['stock.quant']
        quant._update_available_quantity(
            self.product, self.location, quantity)
        self.assertEqual(self.product.qty_available, quantity)
        self.assertEqual(self.product.qty_available_real, quantity)
        product_uom_qty = 10
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': product_uom_qty})]
        })
        sale.action_confirm()
        self.assertEqual(self.product.qty_available, quantity)
        self.assertEqual(
            self.product.qty_available_real,
            quantity - product_uom_qty)
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        self.assertEqual(
            self.product.qty_available,
            self.product.qty_available_real)

    def test_sale_order_line_not_stock_enough(self):
        quantity = 10.0
        quant = self.env['stock.quant']
        quant._update_available_quantity(
            self.product, self.location, quantity)
        self.assertEqual(self.product.qty_available, quantity)
        self.assertEqual(self.product.qty_available_real, quantity)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        product_uom_qty = 20
        order_line = self.env['sale.order.line'].create({
            'name': 'Test Line 1',
            'product_id': self.product.id,
            'product_uom_qty': product_uom_qty,
            'price_unit': self.product.list_price,
            'order_id': sale.id,
        })
        self.assertEqual(
            self.product.qty_available_real,
            order_line.qty_available_real)
        message = order_line._onchange_product_id_check_availability()
        self.assertEqual(
            message['warning']['title'],
            _('Not enough inventory!'))
        sale.action_confirm()
        self.assertEqual(
            self.product.qty_available_real,
            quantity - product_uom_qty)

    def test_product_template_qty_available_real(self):
        attr = self.env['product.attribute'].create({
            'name': 'Attribute test',
        })
        for value in ['A', 'B', 'C']:
            self.env['product.attribute.value'].create({
                'attribute_id': attr.id,
                'name': value,
            })
        product_tmpl = self.env['product.template'].create({
            'name': 'Test Purchase Product',
            'type': 'product',
            'standard_price': 10.00,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': attr.id,
                    'value_ids': [(6, 0, attr.value_ids.ids)],
                }),
            ]
        })
        self.assertEquals(len(product_tmpl.product_variant_ids), 3)
        quant = self.env['stock.quant']
        qty_1 = 5.0
        quant._update_available_quantity(
            product_tmpl.product_variant_ids[0], self.location, qty_1)
        qty_2 = 10.0
        quant._update_available_quantity(
            product_tmpl.product_variant_ids[1], self.location, qty_2)
        qty_3 = 15.0
        quant._update_available_quantity(
            product_tmpl.product_variant_ids[2], self.location, qty_3)
        total_qty = qty_1 + qty_2 + qty_3
        product_uom_qty = 3
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product_tmpl.product_variant_ids[0].id,
                    'price_unit': 100,
                    'product_uom_qty': product_uom_qty}),
                (0, 0, {
                    'product_id': product_tmpl.product_variant_ids[1].id,
                    'price_unit': 100,
                    'product_uom_qty': product_uom_qty}),
                (0, 0, {
                    'product_id': product_tmpl.product_variant_ids[2].id,
                    'price_unit': 100,
                    'product_uom_qty': product_uom_qty}),
            ],
        })
        self.assertEqual(product_tmpl.qty_available_real, total_qty)
        sale.action_confirm()
        self.assertEqual(
            product_tmpl.qty_available_real,
            total_qty - product_uom_qty * 3)
