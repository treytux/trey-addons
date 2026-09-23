###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestSaleOrderLineLimitDiscount(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
        })
        self.sale_order = self.env['sale.order'].create({
            'name': 'Test Sale',
            'partner_id': self.partner.id,
        })
        self.sale_order_line = self.env['sale.order.line'].create({
            'name': 'Test Line',
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
            'price_unit': 100.0
        })

    def test_less_to_zero(self):
        with self.assertRaises(exceptions.ValidationError) as context:
            self.sale_order_line.write({
                'discount': -1.0,
            })
        warning = context.exception.name
        self.assertEqual(warning, 'Discount must be between 0 and 100.')

    def test_upper_to_one_hundred(self):
        with self.assertRaises(exceptions.ValidationError) as context:
            self.sale_order_line.write({
                'discount': 101.0,
            })
        warning = context.exception.name
        self.assertEqual(warning, 'Discount must be between 0 and 100.')

    def test_correct_discount(self):
        self.sale_order_line.write({
            'discount': 50.0,
        })
        self.assertEqual(self.sale_order_line.price_reduce, 50.0)
