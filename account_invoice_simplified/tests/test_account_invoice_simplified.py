###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleReturn(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'type': 'service',
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'vat': 'NUMBER',
        })
        type_revenue = self.env.ref('account.data_account_type_revenue')
        type_payable = self.env.ref('account.data_account_type_payable')
        account_customer = self.env['account.account'].create({
            'name': 'Customer',
            'code': 'XX_430',
            'user_type_id': type_payable.id,
            'reconcile': True,
        })
        account_supplier = self.env['account.account'].create({
            'name': 'Supplier',
            'code': 'XX_400',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        self.account_sale = self.env['account.account'].create({
            'name': 'Sale',
            'code': 'XX_700',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        self.partner.property_account_receivable_id = account_customer.id
        self.partner.property_account_payable_id = account_supplier.id
        self.journal_simplified = self.env['account.journal'].create({
            'name': 'Test journal simplified for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': self.account_sale.id,
            'default_credit_account_id': self.account_sale.id,
            'journal_simplified_id': False,
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': self.account_sale.id,
            'default_credit_account_id': self.account_sale.id,
            'journal_simplified_id': self.journal_simplified.id,
        })
        tax_group_taxes = self.env.ref('account.tax_group_taxes')
        self.tax = self.env['account.tax'].create({
            'name': 'Tax for sale 10%',
            'type_tax_use': 'sale',
            'tax_group_id': tax_group_taxes.id,
            'amount_type': 'percent',
            'amount': 10.0,
        })
        self.product.taxes_id = [(6, 0, self.tax.ids)]
        self.env.user.company_id.simplified_journal_id = (
            self.journal_simplified)

    def test_invoice_not_simplified(self):
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account_sale.id,
                'price_unit': 100,
                'quantity': 1})],
        })
        invoice.action_invoice_open()
        self.assertEquals(invoice.journal_id, self.journal)

    def test_invoice_simplified(self):
        self.partner.vat = False
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account_sale.id,
                'price_unit': 100,
                'quantity': 1})],
        })
        invoice.action_invoice_open()
        self.assertEquals(invoice.journal_id, self.journal_simplified)
