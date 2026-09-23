###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleOrderInvoiceJournal(TransactionCase):
    def setUp(self):
        super().setUp()
        self.journal = self.env['account.journal'].create({
            'name': 'Test Journal',
            'type': 'sale',
            'code': 'TEST JOURNAL',
        })
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
            'active_id': sales[0].id}
        payment_obj = self.env['sale.advance.payment.inv'].with_context(ctx)
        payment = payment_obj.create({
            'advance_payment_method': method})
        return payment.with_context(ctx)

    def test_sale_invoice_all_with_journal(self):
        wizard = self.create_wizard(self.sale)
        wizard.journal_id = self.journal
        wizard.create_invoices()
        self.assertEquals(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        self.assertEquals(invoice.journal_id, self.journal)

    def test_sale_invoice_delivered_with_journal(self):
        wizard = self.create_wizard(self.sale, 'delivered')
        wizard.journal_id = self.journal
        wizard.create_invoices()
        self.assertEquals(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        self.assertEquals(invoice.journal_id, self.journal)

    def test_sale_invoice_percentage_with_journal(self):
        wizard = self.create_wizard(self.sale, 'percentage')
        wizard.journal_id = self.journal
        wizard.amount = 10
        wizard.create_invoices()
        self.assertEquals(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        self.assertEquals(invoice.journal_id, self.journal)

    def test_sale_invoice_fixed_with_journal(self):
        wizard = self.create_wizard(self.sale, 'fixed')
        wizard.journal_id = self.journal
        wizard.amount = 10
        wizard.create_invoices()
        self.assertEquals(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        self.assertEquals(invoice.journal_id, self.journal)

    def test_sale_invoice_all_without_journal(self):
        wizard = self.create_wizard(self.sale)
        wizard.create_invoices()
        self.assertEquals(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        self.assertEquals(invoice.journal_id.id, 1)
        self.assertNotEquals(invoice.journal_id, self.journal)

    def test_sale_invoice_delivered_without_journal(self):
        wizard = self.create_wizard(self.sale, 'delivered')
        wizard.create_invoices()
        self.assertEquals(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        self.assertEquals(invoice.journal_id.id, 1)
        self.assertNotEquals(invoice.journal_id, self.journal)

    def test_sale_invoice_percentage_without_journal(self):
        wizard = self.create_wizard(self.sale, 'percentage')
        wizard.amount = 10
        wizard.create_invoices()
        self.assertEquals(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        self.assertEquals(invoice.journal_id.id, 1)
        self.assertNotEquals(invoice.journal_id, self.journal)

    def test_sale_invoice_fixed_without_journal(self):
        wizard = self.create_wizard(self.sale, 'fixed')
        wizard.amount = 10
        wizard.create_invoices()
        self.assertEquals(len(self.sale.invoice_ids), 1)
        invoice = self.sale.invoice_ids[0]
        self.assertEquals(invoice.journal_id.id, 1)
        self.assertNotEquals(invoice.journal_id, self.journal)
