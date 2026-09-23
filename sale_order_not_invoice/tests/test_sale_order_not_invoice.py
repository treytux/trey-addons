###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestSaleOrderNotInvoice(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Product test',
            'standard_price': 10,
            'list_price': 10,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner 1',
        })

    def create_wizard(self, sales, method='all'):
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sales.ids,
            'active_id': sales[0].id}
        payment_obj = self.env['sale.advance.payment.inv'].with_context(ctx)
        payment = payment_obj.create({
            'advance_payment_method': method})
        return payment.with_context(ctx)

    def test_sales_orders_not_invoice(self):
        sale_1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 10,
                    'product_uom_qty': 1}),
            ],
            'not_invoice': True
        })
        sale_1.action_confirm()
        wizard = self.create_wizard(sale_1)
        with self.assertRaises(ValidationError):
            wizard.create_invoices()
        self.assertEqual(sale_1.state, 'sale')
        self.assertEqual(len(sale_1.invoice_ids), 0)
        sale_2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 10,
                    'product_uom_qty': 1}),
            ],
            'not_invoice': True
        })
        sales = self.env['sale.order'].browse([sale_1.id, sale_2.id])
        sale_2.action_confirm()
        wizard = self.create_wizard(sales)
        with self.assertRaises(ValidationError):
            wizard.create_invoices()
        self.assertEqual(sale_1.state, 'sale')
        self.assertEqual(len(sale_1.invoice_ids), 0)
        self.assertEqual(sale_2.state, 'sale')
        self.assertEqual(len(sale_2.invoice_ids), 0)
        sale_3 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 10,
                    'product_uom_qty': 1}),
            ],
            'not_invoice': False
        })
        sales = self.env['sale.order'].browse([sale_1.id, sale_2.id, sale_3.id])
        sale_3.action_confirm()
        wizard = self.create_wizard(sales)
        wizard.create_invoices()
        self.assertEqual(sale_1.state, 'sale')
        self.assertEqual(len(sale_1.invoice_ids), 0)
        self.assertEqual(sale_2.state, 'sale')
        self.assertEqual(len(sale_2.invoice_ids), 0)
        self.assertEqual(sale_3.state, 'sale')
        self.assertEqual(len(sale_3.invoice_ids), 1)
        invoice = sale_3.invoice_ids[0]
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(len(invoice.invoice_line_ids), 1)
