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
            'company_id': self.env.user.company_id.id,
        })

    def test_limits(self):
        sale_obj = self.env['sale.order'].sudo(self.user)
        auto_done = self.env['ir.config_parameter'].sudo().get_param(
            'sale.auto_done_setting')
        self.assertEquals(auto_done, False)
        sale = sale_obj.create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 100,
                'product_uom_qty': 1})]
        })
        sale.action_confirm()
        self.assertEquals(sale.state, 'pending-approve')
        sale.action_approve()
        self.assertEquals(sale.state, 'pending-approve')
        self.user.sales_amount_limit = 1000
        sale.action_approve()
        self.assertEquals(sale.state, 'draft')
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')

    def test_limits_loocked(self):
        sale_obj = self.env['sale.order'].sudo(self.user)
        self.env['ir.config_parameter'].sudo().set_param(
            'sale.auto_done_setting', True)
        auto_done = self.env['ir.config_parameter'].sudo().get_param(
            'sale.auto_done_setting')
        self.assertEquals(auto_done, 'True')
        sale = sale_obj.create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 100,
                'product_uom_qty': 1})]
        })
        sale.action_confirm()
        self.assertEquals(sale.state, 'pending-approve')
        sale.action_approve()
        self.assertEquals(sale.state, 'pending-approve')
        self.user.sales_amount_limit = 1000
        sale.action_approve()
        self.assertEquals(sale.state, 'draft')
        sale.action_confirm()
        self.assertEquals(sale.state, 'done')

    def test_limits_discount(self):
        sale_obj = self.env['sale.order'].sudo(self.user)
        self.env['ir.config_parameter'].sudo().set_param(
            'sale.auto_done_setting', True)
        auto_done = self.env['ir.config_parameter'].sudo().get_param(
            'sale.auto_done_setting')
        self.assertEquals(auto_done, 'True')
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
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 510,
                    'tax_id': [(6, 0, tax.ids)],
                    'discount': 0,
                    'product_uom_qty': 40}),
            ],
        })
        sale.action_confirm()
        self.assertEquals(sale.state, 'pending-approve')
        sale.action_approve()
        self.assertEquals(sale.state, 'pending-approve')
        self.user.sales_amount_limit = 100000
        sale.action_approve()
        self.assertEquals(sale.state, 'pending-approve')
        self.user.sales_discount_limit = 40
        sale.action_approve()
        self.assertEquals(sale.state, 'draft')
        sale.action_confirm()
        self.assertEquals(sale.state, 'done')

    def test_limits_discount_100(self):
        sale_obj = self.env['sale.order'].sudo(self.user)
        self.env['ir.config_parameter'].sudo().set_param(
            'sale.auto_done_setting', True)
        auto_done = self.env['ir.config_parameter'].sudo().get_param(
            'sale.auto_done_setting')
        self.assertEquals(auto_done, 'True')
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
                    'product_uom_qty': 1}),
            ],
        })
        self.user.sales_amount_limit = 100000
        self.user.sales_discount_limit = 10
        sale.action_confirm()
        self.assertEquals(sale.state, 'pending-approve')
        sale.action_approve()
        self.assertEquals(sale.state, 'pending-approve')
        self.user.sales_discount_limit = 99.99
        sale.action_approve()
        self.assertEquals(sale.state, 'pending-approve')
        self.user.sales_discount_limit = 100
        sale.action_approve()
        self.assertEquals(sale.state, 'draft')
        sale.action_confirm()
        self.assertEquals(sale.state, 'done')

    def test_limits_sale_order_cumulative_discount_legacy(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'sale_order_cumulative_discount')])
        self.assertTrue(module)
        if module.state != 'installed':
            self.skipTest(
                'Module sale_order_cumulative_discount not installed')
            return
        sale_obj = self.env['sale.order'].sudo(self.user)
        self.env['ir.config_parameter'].sudo().set_param(
            'sale.auto_done_setting', True)
        auto_done = self.env['ir.config_parameter'].sudo().get_param(
            'sale.auto_done_setting')
        self.assertEquals(auto_done, 'True')
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
                    'multiple_discount': '10+20+30',
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 510,
                    'tax_id': [(6, 0, tax.ids)],
                    'discount': 0,
                    'product_uom_qty': 40}),
            ],
        })
        sale.order_line.onchange_multiple_discount()
        sale.action_confirm()
        self.assertEquals(sale.state, 'pending-approve')
        sale.action_approve()
        self.assertEquals(sale.state, 'pending-approve')
        self.user.sales_amount_limit = 100000
        sale.action_approve()
        self.assertEquals(sale.state, 'pending-approve')
        self.user.sales_discount_limit = 50
        sale.action_approve()
        self.assertEquals(sale.state, 'draft')
        self.assertGreater(
            sum(sale.order_line.mapped('amount_discount_approve')), 0)
        sale.action_confirm()
        self.assertEquals(sale.state, 'done')
