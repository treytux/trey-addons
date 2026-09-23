###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests import common


class TestSaleInvoiceAdvanceDate(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'picking_policy': 'direct',
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 15,
                }),
            ],
        })
        self.sale.action_confirm()

    def create_wizard(self, sales, method='all'):
        ctx = {
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': sales.ids,
            'active_id': sales[0].id,
        }
        payment_obj = self.env['sale.advance.payment.inv'].with_context(ctx)
        payment = payment_obj.create({
            'advance_payment_method': method
        })
        return payment.with_context(ctx)

    def test_sale_invoice_advance_date(self):
        wizard = self.create_wizard(self.sale)
        self.assertFalse(wizard.date_invoice)
        date = fields.Date.today() + relativedelta(days=3)
        wizard.date_invoice = date
        self.assertTrue(wizard.date_invoice)
        self.assertEqual(wizard.date_invoice, date)
        wizard.create_invoices()
        self.assertEqual(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        self.assertEqual(invoice.date_invoice, date)
        self.assertNotEqual(invoice.date_invoice, fields.Date.today())

    def test_sale_invoice_advance_not_date(self):
        wizard = self.create_wizard(self.sale)
        self.assertFalse(wizard.date_invoice)
        wizard.create_invoices()
        self.assertEqual(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        self.assertEqual(invoice.date_invoice, fields.Date.today())

    def test_sale_invoice_advance_old_date(self):
        wizard = self.create_wizard(self.sale)
        self.assertFalse(wizard.date_invoice)
        date = fields.Date.today() - relativedelta(days=3)
        wizard.date_invoice = date
        self.assertTrue(wizard.date_invoice)
        self.assertEqual(wizard.date_invoice, date)
        wizard.create_invoices()
        self.assertEqual(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        self.assertEqual(invoice.date_invoice, date)
        self.assertNotEqual(invoice.date_invoice, fields.Date.today())
