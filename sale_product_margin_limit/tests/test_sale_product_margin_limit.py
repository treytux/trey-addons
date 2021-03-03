###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProductListPriceFromMargin(TransactionCase):

    def test_margin_price_unit(self):
        def compute(standard, margin):
            product = self.env['product.template'].create({
                'name': 'Test Product',
                'standard_price': standard,
                'margin_limit': margin,
                'margin_price_limit': 0.,
            })
            return product.margin_price_limit

        self.assertEquals(compute(0, 0), 0)
        self.assertEquals(compute(100, 0), 100)
        self.assertEquals(compute(100, 25), 133.33)
        self.assertEquals(compute(100, 20), 125)
        self.assertEquals(compute(100, 100), 1000000.0)
        self.assertEquals(compute(100, 200), 1000000.0)
        self.assertEquals(compute(100, -100), 50)

    def test_margin(self):
        self.env.user.sales_amount_limit = 99999999
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        product = self.env['product.product'].create({
            'name': 'Test Product',
            'standard_price': 100,
            'margin_limit': 25,
        })
        self.assertEquals(product.margin_price_limit, 133.33)
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        sale.action_confirm()
        self.assertEquals(sale.state, 'pending-approve')
        sale.order_line[0].price_unit = 140
        sale.action_approve()
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')

    def test_margin_user_ignore(self):
        self.env.user.sales_amount_limit = 99999999
        self.env.user.sales_discount_limit = 99.99
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        product = self.env['product.product'].create({
            'name': 'Test Product',
            'standard_price': 100,
            'margin_limit': 25,
        })
        self.assertEquals(product.margin_price_limit, 133.33)
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 100,
                    'discount': 10,
                    'product_uom_qty': 10}),
            ]
        })
        sale.action_confirm()
        self.assertEquals(sale.state, 'pending-approve')
        self.env.user.ignore_margin_price_limit = True
        sale.action_approve()
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
