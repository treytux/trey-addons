###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import datetime

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestAccountInvoiceAssignDateInvoice(TransactionCase):
    def setUp(self):
        super().setUp()
        self.today = datetime.date.today()
        self.date = self.today - datetime.timedelta(10)
        self.number_invoice = '1234XXX'
        self.partner = self.env.ref('base.res_partner_12')
        self.product = self.env.ref('product.product_product_4d')
        type_revenue = self.env.ref('account.data_account_type_revenue')
        self.account_sale = self.env['account.account'].create({
            'name': 'Sale',
            'code': 'XX_700',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': self.account_sale.id,
            'default_credit_account_id': self.account_sale.id,
        })
        self.assign_date_obj = self.env['account.invoice.assign.date.invoice']
        type_revenue = self.env.ref('account.data_account_type_revenue')
        type_payable = self.env.ref('account.data_account_type_payable')
        account_customer = self.env['account.account'].create({
            'name': 'Customer',
            'code': 'XX_430',
            'user_type_id': type_payable.id,
            'reconcile': True,
        })
        self.partner.property_account_receivable_id = account_customer.id
        account_supplier = self.env['account.account'].create({
            'name': 'Supplier',
            'code': 'XX_400',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        self.partner.property_account_payable_id = account_supplier.id

    def create_invoice(self):
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'price_unit': self.product.lst_price,
                'account_id': self.account_sale.id,
                'quantity': 1,
            })],
        })
        return invoice

    def test_invoice_assign_date(self):
        invoice1 = self.create_invoice()
        invoice2 = self.create_invoice()
        invoices = [invoice1, invoice2]
        wizard = self.assign_date_obj.with_context({
            'active_ids': [invoice1.id, invoice2.id],
        }).create({
            'date_invoice': self.today,
        })
        wizard.assign_values_invoice()
        for invoice in invoices:
            self.assertEqual(invoice.date_invoice, self.today)

    def test_invoice_assign_date_open_raise(self):
        invoice1 = self.create_invoice()
        invoice2 = self.create_invoice()
        invoice1.action_invoice_open()
        self.assertEqual(invoice1.state, 'open')
        wizard = self.assign_date_obj.with_context({
            'active_ids': [invoice1.id, invoice2.id],
        }).create({
            'date_invoice': self.today,
        })
        with self.assertRaises(UserError) as result:
            wizard.assign_values_invoice()
        text = 'The following invoices are not in draft state'
        self.assertIn(text, result.exception.name)

    def test_invoice_assign_date_one_invoice_selected(self):
        invoice = self.create_invoice()
        wizard = self.assign_date_obj.with_context({
            'active_ids': [invoice.id],
        }).create({
            'date_invoice': self.today,
            'number_invoice': '1234XXX',
        })
        wizard.assign_values_invoice()
        self.assertEqual(invoice.date_invoice, self.today)
        self.assertEqual(invoice.number, '1234XXX')
        self.assertEqual(invoice.state, 'draft')

    def test_invoice_assign_number_invoice_raise(self):
        with self.assertRaises(UserError) as result:
            invoice1 = self.create_invoice()
            invoice2 = self.create_invoice()
            wizard = self.assign_date_obj.with_context({
                'active_ids': [invoice1.id, invoice2.id],
            }).create({
                'date_invoice': self.date,
                'number_invoice': '1234XXX',
            })
            wizard.assign_values_invoice()
        text = 'If you want to change a invoice number, you can\'t select more'
        text += ' than one invoice'
        self.assertIn(text, result.exception.name)

    def test_invoice_assign_number_invoice_draft_raise(self):
        with self.assertRaises(UserError) as result:
            invoice = self.create_invoice()
            invoice.action_invoice_open()
            self.assertEqual(invoice.state, 'open')
            wizard = self.assign_date_obj.with_context({
                'active_ids': [invoice.id],
            }).create({
                'date_invoice': self.date,
                'number_invoice': '1234XXX',
            })
            wizard.assign_values_invoice()
        text = 'The invoice isn\'t in draft state, it can\'t be modified'
        self.assertIn(text, result.exception.name)
