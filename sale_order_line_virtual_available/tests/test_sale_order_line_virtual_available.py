###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleOrderLineVirtualAvailable(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.location = self.env.ref('stock.stock_location_stock')

    def test_sale_order_line_virtual_available(self):
        qty = 10.0
        quant = self.env['stock.quant']
        quant._update_available_quantity(
            self.product, self.location, qty)
        self.assertEqual(self.product.virtual_available, qty)
        product_uom_qty = 5.0
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': product_uom_qty})]
        })
        order.action_confirm()
        self.assertEqual(
            self.product.virtual_available,
            qty - product_uom_qty)
