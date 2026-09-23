###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests.common import TransactionCase


class TestSaleOrderInvoiceDateDue(TransactionCase):
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
        self.partner_a = self.env['res.partner'].create({
            'name': 'Test partner A',
            'customer': True,
            'is_company': True,
        })

    def test_sale_with_invoice_date_due(self):
        date_invoice = fields.Date.today()
        sale = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'invoice_date_due': date_invoice,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 1,
                    'product_uom_qty': 1}),
            ]
        })
        sale.onchange_partner_id()
        sale.action_confirm()
        sale.action_invoice_create()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEquals(sale.invoice_date_due, date_invoice)
        self.assertEquals(sale.invoice_date_due, invoice.date_due)

    def test_sale_without_invoice_date_due(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 1,
                    'product_uom_qty': 1}),
            ]
        })
        sale.onchange_partner_id()
        sale.action_confirm()
        sale.action_invoice_create()
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertFalse(sale.invoice_date_due)
        self.assertEquals(sale.invoice_date_due, invoice.date_due)
