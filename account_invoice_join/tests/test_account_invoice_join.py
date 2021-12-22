###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestAccountInvoiceJoin(TransactionCase):

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
            ('type', '=', 'sale'),
        ], limit=1)
        self.account = self.env.user.company_id.get_chart_of_accounts_or_fail()
        self.invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'origin': 'Test origin',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })

    def test_raise_errors_not_draft(self):
        invoice2 = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        self.invoice.action_invoice_open()
        invoice_ids = [self.invoice.id, invoice2.id]
        self.joiner = self.env['account.invoice.join'].create({})
        with self.assertRaises(UserError):
            self.joiner.with_context(active_ids=invoice_ids).action_join()

    def test_raise_errors_not_same_partner(self):
        partner2 = self.env['res.partner'].create({
            'name': 'Partner test2',
        })

        invoice2 = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': partner2.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice_ids = [self.invoice.id, invoice2.id]
        self.joiner = self.env['account.invoice.join'].create({})
        with self.assertRaises(UserError):
            self.joiner.with_context(active_ids=invoice_ids).action_join()

    def test_raise_errors_not_same_type(self):
        invoice2 = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'type': 'in_refund',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice_ids = [self.invoice.id, invoice2.id]
        self.joiner = self.env['account.invoice.join'].create({})
        with self.assertRaises(UserError):
            self.joiner.with_context(active_ids=invoice_ids).action_join()

    def test_correct_prices_and_origin(self):
        invoice2 = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'origin': 'Test origin2',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice_ids = [self.invoice.id, invoice2.id]
        self.joiner = self.env['account.invoice.join'].create({})
        amount = self.invoice.amount_total + invoice2.amount_total
        origin_master = '%s, %s' % (self.invoice.origin, invoice2.origin)
        self.joiner.with_context(active_ids=invoice_ids).action_join()
        self.assertEquals(self.invoice.amount_total, amount)
        self.assertEquals(self.invoice.origin, origin_master)

    def test_different_origin_and_correct_number_lines(self):
        invoice2 = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        invoice_ids = [invoice2.id, self.invoice.id]
        self.joiner = self.env['account.invoice.join'].create({})
        origin_invoice1 = self.invoice.origin
        self.joiner.with_context(active_ids=invoice_ids).action_join()
        self.assertEquals(invoice2.origin, origin_invoice1)
        self.assertEquals(len(invoice2.invoice_line_ids), 2)
