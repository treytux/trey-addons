###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests import common


class TestDeliveryDHL(common.TransactionCase):
    def setUp(self):
        super().setUp()
        type_revenue = self.env.ref('account.data_account_type_revenue')
        self.account_sale = self.env['account.account'].create({
            'name': 'Sale',
            'code': 'XX_700',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': self.account_sale.id,
            'default_credit_account_id': self.account_sale.id,
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })

    def test_invoices(self):
        self.journal.limit_amount_total = 100
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account_sale.id,
                'price_unit': 101,
                'quantity': 1
            })],
        })
        with self.assertRaises(UserError):
            invoice.action_invoice_open()
        self.journal.limit_amount_total = 101
        invoice.action_invoice_open()

    def test_invoices_when_type_is_cash(self):
        self.journal.write({
            'type': 'cash',
            'limit_amount_total': 100,
        })
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account_sale.id,
                'price_unit': 101,
                'quantity': 1
            })],
        })
        invoice.action_invoice_open()
        self.assertEquals(invoice.state, 'open')
