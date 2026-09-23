###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestAccountInvoiceTaxManual(common.TransactionCase):

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
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': self.account_sale.id,
            'default_credit_account_id': self.account_sale.id,
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

    def test_modify_invoice(self):
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account_sale.id,
                'price_unit': 100,
                'invoice_line_tax_ids': [(6, 0, self.tax.ids)],
                'quantity': 1})],
        })
        self.assertEquals(invoice.amount_total, 110)
        self.assertEquals(len(invoice.tax_line_ids), 1)
        tax_line = invoice.tax_line_ids[0]
        self.assertEquals(tax_line.tax_id, self.tax)
        self.assertEquals(tax_line.base, 100)
        self.assertEquals(tax_line.amount, 10)
        self.assertEquals(tax_line.amount_total, 10)
        self.assertEquals(invoice.amount_untaxed, 100)
        self.assertEquals(invoice.amount_tax, 10)
        self.assertEquals(invoice.amount_total, 110)
        tax_line.write({
            'amount': 20,
        })
        self.assertEquals(tax_line.tax_id, self.tax)
        self.assertEquals(tax_line.base, 100)
        self.assertEquals(tax_line.amount, 20)
        self.assertEquals(tax_line.amount_total, 20)
        self.assertEquals(invoice.amount_untaxed, 100)
        self.assertEquals(invoice.amount_tax, 20)
        self.assertEquals(invoice.amount_total, 120)
        invoice.compute_taxes()
        tax_line = invoice.tax_line_ids[0]
        self.assertEquals(tax_line.tax_id, self.tax)
        self.assertEquals(tax_line.base, 100)
        self.assertEquals(tax_line.amount, 10)
        self.assertEquals(tax_line.amount_total, 10)
        self.assertEquals(invoice.amount_untaxed, 100)
        self.assertEquals(invoice.amount_tax, 10)
        self.assertEquals(invoice.amount_total, 110)
