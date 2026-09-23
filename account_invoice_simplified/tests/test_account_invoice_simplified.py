###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleReturn(TransactionCase):

    def setUp(self):
        super(TestSaleReturn, self).setUp()
        self.product = self.env['product.product'].create({
            'type': 'service',
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test VAT',
            'vat': 'NUMBER',
        })
        self.partner_novat = self.env['res.partner'].create({
            'name': 'Partner test NO VAT',
            'vat': False,
        })
        self.currency_usd = self.env.ref('base.USD')
        self.currency_eur = self.env.ref('base.EUR')
        self.currency_rub = self.env.ref('base.RUB')
        self.currency_rub.active = True
        self.journal_simplified = self.env['account.journal'].create({
            'name': 'Test journal simplified for sale',
            'type': 'sale',
            'code': 'TSALE',
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TJ',
            'journal_simplified_id': self.journal_simplified.id,
        })

    def test_invoice_not_simplified(self):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice.action_post()
        self.assertEqual(invoice.journal_id, self.journal)

    def test_invoice_simplified(self):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'journal_id': self.journal.id,
            'partner_id': self.partner_novat.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice.action_post()
        self.assertEqual(invoice.journal_id, self.journal_simplified)

    def test_invoice_not_simplified_change_currency(self):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'currency_id': self.currency_eur.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        self.assertEqual(
            self.env.company.currency_id, self.currency_usd)
        self.assertEqual(invoice.currency_id, self.currency_eur)
        self.assertFalse(self.journal.currency_id)
        invoice.action_post()
        self.assertEqual(invoice.journal_id, self.journal)
        self.assertEqual(invoice.currency_id, self.currency_eur)

    def test_invoice_simplified_change_currency(self):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'journal_id': self.journal.id,
            'partner_id': self.partner_novat.id,
            'currency_id': self.currency_eur.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        self.assertEqual(
            self.env.company.currency_id, self.currency_usd)
        self.assertEqual(invoice.currency_id, self.currency_eur)
        self.assertFalse(self.journal.currency_id)
        invoice.action_post()
        self.assertEqual(invoice.journal_id, self.journal_simplified)
        self.assertEqual(invoice.currency_id, self.currency_eur)

    def test_several_invoices(self):
        invoices = self.env['account.move']
        invoice_01 = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice_02 = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'journal_id': self.journal.id,
            'partner_id': self.partner_novat.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoices |= invoice_01
        invoices |= invoice_02
        invoices.action_post()
        self.assertEqual(invoice_01.journal_id, self.journal)
        self.assertEqual(invoice_02.journal_id, self.journal_simplified)
