###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestSaleOrderClientOrderRefRequired(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product_a = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product a',
            'default_code': 'TESTPR_A',
            'standard_price': 10,
            'list_price': 30,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'customer': True,
            'is_company': True,
            'require_client_order_ref': True,
        })
        self.partner_2 = self.env['res.partner'].create({
            'name': 'Test partner 2',
            'customer': True,
            'is_company': True,
            'require_client_order_ref': False,
        })

    def test_sale_confirm_required_order_ref(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        self.assertTrue(sale.partner_id.require_client_order_ref)
        self.assertFalse(sale.client_order_ref)
        with self.assertRaises(exceptions.ValidationError) as result:
            sale.action_confirm()
        self.assertIn('client order number is required', result.exception.name)
        sale.client_order_ref = 'REF01'
        self.assertTrue(sale.client_order_ref)
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')

    def test_sale_confirm_not_required_order_ref(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner_2.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        self.assertFalse(sale.client_order_ref)
        self.assertFalse(sale.partner_id.require_client_order_ref)
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
