###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleUserLimits(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'user@test.com',
            'email': 'user@test.com',
            'company_id': self.env.company.id,
        })

    def test_limits(self):
        sale_obj = self.env['sale.order'].with_user(self.user)
        sale = sale_obj.create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'pending-approve')
        sale.action_approve()
        self.assertEqual(sale.state, 'pending-approve')
        self.user.sales_amount_limit = 1000
        sale.action_approve()
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')

    def test_check_limits_multiple_orders(self):
        sale_obj = self.env['sale.order'].with_user(self.user)
        sales = sale_obj.create([
            {
                'partner_id': self.partner.id,
                'order_line': [
                    (0, 0, {
                        'product_id': self.product.id,
                        'price_unit': 100,
                        'product_uom_qty': 1,
                    }),
                ],
            },
            {
                'partner_id': self.partner.id,
                'order_line': [
                    (0, 0, {
                        'product_id': self.product.id,
                        'price_unit': 100,
                        'product_uom_qty': 1,
                    }),
                ],
            },
        ])
        self.assertFalse(sales.check_limits())
        self.assertEqual(
            sales.mapped('state'), ['pending-approve', 'pending-approve'])
        self.assertTrue(all(sales.mapped('exception_limit_reason')))

    def test_check_limits_empty_orders(self):
        sale_obj = self.env['sale.order'].with_user(self.user)
        self.assertFalse(sale_obj.browse().check_limits())

    def test_limits_loocked(self):
        sale_obj = self.env['sale.order'].with_user(self.user)
        sale = sale_obj.create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'pending-approve')
        sale.action_approve()
        self.assertEqual(sale.state, 'pending-approve')
        self.user.sales_amount_limit = 1000
        sale.action_approve()
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')

    def test_limits_discount(self):
        sale_obj = self.env['sale.order'].with_user(self.user)
        tax = self.env['account.tax'].create({
            'name': 'Tax Test 21%',
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'amount': 21,
        })
        sale = sale_obj.create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 5.75,
                    'tax_id': [(6, 0, tax.ids)],
                    'discount': 35.20,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 510,
                    'tax_id': [(6, 0, tax.ids)],
                    'discount': 0,
                    'product_uom_qty': 40,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(sale.state, 'pending-approve')
        sale.action_approve()
        self.assertEqual(sale.state, 'pending-approve')
        self.user.sales_amount_limit = 100000
        sale.action_approve()
        self.assertEqual(sale.state, 'pending-approve')
        self.user.sales_discount_limit = 40
        sale.action_approve()
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')

    def test_limits_discount_100(self):
        sale_obj = self.env['sale.order'].with_user(self.user)
        tax = self.env['account.tax'].create({
            'name': 'Tax Test 21%',
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'amount': 21,
        })
        sale = sale_obj.create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 5.75,
                    'tax_id': [(6, 0, tax.ids)],
                    'discount': 100,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.user.sales_amount_limit = 100000
        self.user.sales_discount_limit = 10
        sale.action_confirm()
        self.assertEqual(sale.state, 'pending-approve')
        sale.action_approve()
        self.assertEqual(sale.state, 'pending-approve')
        self.user.sales_discount_limit = 99.99
        sale.action_approve()
        self.assertEqual(sale.state, 'pending-approve')
        self.user.sales_discount_limit = 100
        sale.action_approve()
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')

    def test_remove_msg_exception_confirm_01(self):
        sale_obj = self.env['sale.order'].with_user(self.user)
        sale = sale_obj.create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 60,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.assertEqual(self.user.sales_amount_limit, 0)
        self.assertFalse(sale.exception_limit_reason)
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'pending-approve')
        self.assertTrue(sale.exception_limit_reason)
        sale.with_context(disable_cancel_warning=True).action_cancel()
        self.assertEqual(sale.state, 'cancel')
        self.assertTrue(sale.exception_limit_reason)
        sale.action_draft()
        self.assertEqual(sale.state, 'draft')
        self.assertTrue(sale.exception_limit_reason)
        self.user.sales_amount_limit = 100
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertFalse(sale.exception_limit_reason)

    def test_remove_msg_exception_confirm_02(self):
        sale_obj = self.env['sale.order'].with_user(self.user)
        sale = sale_obj.create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 60,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.assertEqual(self.user.sales_amount_limit, 0)
        self.assertFalse(sale.exception_limit_reason)
        self.assertEqual(sale.state, 'draft')
        sale.action_confirm()
        self.assertEqual(sale.state, 'pending-approve')
        self.assertTrue(sale.exception_limit_reason)
        self.user.sales_amount_limit = 100
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        self.assertFalse(sale.exception_limit_reason)
