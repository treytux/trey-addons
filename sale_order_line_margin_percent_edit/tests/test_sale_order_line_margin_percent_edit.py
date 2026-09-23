###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests.common import Form, HttpCase


class TestSaleOrderLineMarginPercentEdit(HttpCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_3')
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 50,
            'list_price': 50,
        })

    def test_sale(self):
        with Form(self.env['sale.order']) as sale:
            sale.partner_id = self.partner
        with sale.order_line.new() as line:
            line.product_id = self.product
            line.product_uom_qty = 1
            line.price_unit = 125
            line.purchase_price = 100
        sale_obj = sale.save()
        self.assertEqual(sale_obj.order_line.margin_percent, 0.20)
        sale_obj.order_line.margin_percent = 0.50
        self.assertEqual(sale_obj.order_line.price_unit, 200)
        sale_obj.order_line.margin_percent = 0.60
        self.assertEqual(sale_obj.order_line.price_unit, 250)
        with self.assertRaises(exceptions.ValidationError) as e:
            sale_obj.order_line.margin_percent = 1.0
        self.assertEqual(
            str(e.exception), 'Margin percent must be less than 100%.')

    def test_sale_without_cost(self):
        with Form(self.env['sale.order']) as sale:
            sale.partner_id = self.partner
        self.product.standard_price = 0
        with sale.order_line.new() as line:
            line.product_id = self.product
            line.product_uom_qty = 1
            line.price_unit = 125
        sale_obj = sale.save()
        self.assertEqual(sale_obj.order_line.purchase_price, 0)
        self.assertEqual(sale_obj.order_line.margin_percent, 1.0)
        sale_obj.order_line.margin_percent = 0.50
        self.assertEqual(sale_obj.order_line.price_unit, 125)
        sale_obj.order_line.purchase_price = 100
        self.assertEqual(sale_obj.order_line.margin_percent, .20)
