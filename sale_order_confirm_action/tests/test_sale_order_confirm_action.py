###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleOrderConfirmAction(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner_01 = self.env['res.partner'].create({
            'name': 'Test partner 01',
            'is_company': False,
        })
        self.partner_02 = self.env['res.partner'].create({
            'name': 'Test partner 02',
            'is_company': False,
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 30,
        })
        self.sale_01 = self.env['sale.order'].create({
            'partner_id': self.partner_01.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        self.sale_02 = self.env['sale.order'].create({
            'partner_id': self.partner_02.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 5,
                    'product_uom_qty': 4,
                })
            ]
        })

    def test_confirm_sale_orders_valid_state(self):
        self.assertEqual(self.sale_01.state, 'draft')
        self.assertEqual(self.sale_02.state, 'draft')
        wizard = self.env['sale.order.confirm'].with_context(
            active_ids=[self.sale_01.id, self.sale_02.id]).create({})
        wizard.button_accept()
        self.assertEqual(self.sale_01.state, 'sale')
        self.assertEqual(self.sale_02.state, 'sale')

    def test_confirm_sale_orders_no_valid_state_01(self):
        self.assertEqual(self.sale_01.state, 'draft')
        self.assertEqual(self.sale_02.state, 'draft')
        self.sale_01.action_confirm()
        self.assertEqual(self.sale_01.state, 'sale')
        wizard = self.env['sale.order.confirm'].with_context(
            active_ids=[self.sale_01.id, self.sale_02.id]).create({})
        wizard.button_accept()
        self.assertEqual(self.sale_01.state, 'sale')
        self.assertEqual(self.sale_02.state, 'sale')

    def test_confirm_sale_orders_no_valid_state_02(self):
        self.assertEqual(self.sale_01.state, 'draft')
        self.assertEqual(self.sale_02.state, 'draft')
        self.sale_01.action_cancel()
        self.assertEqual(self.sale_01.state, 'cancel')
        wizard = self.env['sale.order.confirm'].with_context(
            active_ids=[self.sale_01.id, self.sale_02.id]).create({})
        wizard.button_accept()
        self.assertEqual(self.sale_01.state, 'cancel')
        self.assertEqual(self.sale_02.state, 'sale')

    def test_confirm_sale_orders_no_valid_state_03(self):
        self.assertEqual(self.sale_01.state, 'draft')
        self.assertEqual(self.sale_02.state, 'draft')
        self.sale_01.action_done()
        self.assertEqual(self.sale_01.state, 'done')
        wizard = self.env['sale.order.confirm'].with_context(
            active_ids=[self.sale_01.id, self.sale_02.id]).create({})
        wizard.button_accept()
        self.assertEqual(self.sale_01.state, 'done')
        self.assertEqual(self.sale_02.state, 'sale')
