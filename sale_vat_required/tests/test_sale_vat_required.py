###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests import common


class TestSaleVatRequired(common.TransactionCase):

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
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ]
        })

    def test_sale_order_print_without_vat(self):
        self.assertEqual(self.sale_order.state, 'draft')
        self.assertFalse(self.partner.vat)
        with self.assertRaises(exceptions.ValidationError) as result:
            self.sale_order.print_quotation()
        self.assertEqual(
            result.exception.name,
            'The partner %s has not set their VAT' % self.partner.name)
        self.assertEqual(self.sale_order.state, 'draft')

    def test_sale_order_send_mail_without_vat(self):
        self.assertEqual(self.sale_order.state, 'draft')
        self.assertFalse(self.partner.vat)
        with self.assertRaises(exceptions.ValidationError) as result:
            self.sale_order.action_quotation_send()
        self.assertEqual(
            result.exception.name,
            'The partner %s has not set their VAT' % self.partner.name)
        self.assertEqual(self.sale_order.state, 'draft')

    def test_confirm_sale_order_without_vat(self):
        self.assertEqual(self.sale_order.state, 'draft')
        self.assertFalse(self.partner.vat)
        with self.assertRaises(exceptions.ValidationError) as result:
            self.sale_order.action_confirm()
        self.assertEqual(
            result.exception.name,
            'The partner %s has not set their VAT' % self.partner.name)
        self.assertEqual(self.sale_order.state, 'draft')

    def test_preview_sale_order_without_vat(self):
        self.assertEqual(self.sale_order.state, 'draft')
        self.assertFalse(self.partner.vat)
        with self.assertRaises(exceptions.ValidationError) as result:
            self.sale_order.preview_sale_order()
        self.assertEqual(
            result.exception.name,
            'The partner %s has not set their VAT' % self.partner.name)
        self.assertEqual(self.sale_order.state, 'draft')
