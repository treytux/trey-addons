###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleOrderLineQuantityAvailable(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'name': 'Test product',
            'type': 'product',
            'list_price': 10,
        })
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.inventory = self.env['stock.inventory'].create({
            'name': 'Inventory Test',
            'filter': 'product',
            'location_id': self.stock_location.id,
            'product_id': self.product.id,
        })
        self.order_1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self.order_2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self.order_line_1 = self.env['sale.order.line'].create({
            'name': 'Test Line 1',
            'product_id': self.product.id,
            'product_uom_qty': 20,
            'price_unit': self.product.list_price,
            'order_id': self.order_1.id,
        })
        self.order_line_2 = self.env['sale.order.line'].create({
            'name': 'Test Line 2',
            'product_id': self.product.id,
            'product_uom_qty': 10,
            'price_unit': self.product.list_price,
            'order_id': self.order_2.id,
        })

    def test_sale_order_line_qty_available(self):
        quantity = 100.0
        quant = self.env['stock.quant']
        quant._update_available_quantity(
            self.product, self.stock_location, quantity)
        self.assertEqual(
            quant._get_available_quantity(self.product, self.stock_location),
            quantity)
        self.assertEqual(
            self.product.qty_available,
            self.order_line_1.qty_available)
        self.inventory.action_start()
        theorical = self.inventory.line_ids.theoretical_qty
        product_uom_qty = self.order_line_1.product_uom_qty
        self.assertEqual(theorical, quantity)
        self.inventory.line_ids.product_qty = theorical - product_uom_qty
        self.inventory.action_validate()
        self.assertNotEqual(
            quant._get_available_quantity(self.product, self.stock_location),
            self.order_line_1.qty_available)
        self.assertEqual(
            quant._get_available_quantity(self.product, self.stock_location),
            self.inventory.line_ids.product_qty)
        self.assertEqual(
            quant._get_available_quantity(self.product, self.stock_location),
            self.order_line_2.qty_available)
        self.assertEqual(
            self.product.qty_available,
            self.order_line_2.qty_available)
