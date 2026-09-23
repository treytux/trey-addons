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
        initial_quantity = 100.0
        quant = self.env['stock.quant']
        quant._update_available_quantity(
            self.product, self.stock_location, initial_quantity)
        self.assertEqual(
            self.product.qty_available,
            initial_quantity)
        self.assertEqual(
            self.order_line_1.qty_available,
            initial_quantity)
        target_quantity = initial_quantity - self.order_line_1.product_uom_qty
        current_quantity = self.product.qty_available
        quantity_difference = target_quantity - current_quantity
        quant._update_available_quantity(
            self.product, self.stock_location, quantity_difference)
        self.product.refresh()
        self.order_line_1.refresh()
        self.order_line_2.refresh()
        self.assertEqual(
            self.product.qty_available,
            target_quantity)
        self.assertEqual(
            self.order_line_2.qty_available,
            target_quantity)
