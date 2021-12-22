###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestAccountInvoiceSupplierReferenceYear(TransactionCase):

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
        self.journal = self.env['account.journal'].search([
            ('company_id', '=', self.env.user.company_id.id),
            ('type', '=', 'sale')], limit=1)
        self.account = self.env.user.company_id.get_chart_of_accounts_or_fail()
        self.invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'reference': 'Reference test',
            'type': 'in_invoice',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        self.invoice.action_invoice_open()

    def test_same_reference_same_type(self):
        self.invoice2 = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'type': 'in_invoice',
            'reference': 'Reference test',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        with self.assertRaises(UserError):
            self.invoice2.action_invoice_open()

    def test_different_reference_same_type(self):
        invoice2 = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'type': 'in_invoice',
            'reference': 'Reference test2',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice2.action_invoice_open()
        self.assertEquals(invoice2.state, 'open')

    def test_same_reference_different_type(self):
        invoice2 = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'reference': 'Reference test',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice2.action_invoice_open()
        self.assertEquals(invoice2.state, 'open')
