###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)


class TestAccountIntercompany(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company1 = self.create_company('Test company 1')
        self.journal1 = self.env['account.journal'].search([
            ('company_id', '=', self.company1.id),
            ('type', '=', 'sale')], limit=1)
        self.account1 = self.company1.get_chart_of_accounts_or_fail()
        self.company2 = self.create_company('Test company 2')
        self.journal2 = self.env['account.journal'].search([
            ('company_id', '=', self.company2.id),
            ('type', '=', 'sale')], limit=1)
        self.account2 = self.company2.get_chart_of_accounts_or_fail()
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

    def create_company(self, name):
        templates = self.env['account.chart.template'].search([])
        if not templates:
            _log.warn(
                'Test skipped because there is no chart of account defined '
                'new company')
            self.skipTest('No Chart of account found')
            return
        company = self.env['res.company'].create({
            'name': name
        })
        company_before = self.env.user.company_id
        self.env.user.company_id = company.id
        templates[0].try_loading_for_current_company()
        self.env.user.company_id = company_before.id
        return company

    def create_invoice(self, company, journal, account, no_product=False):
        return self.env['account.invoice'].create({
            'company_id': company.id,
            'journal_id': journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'account_id': account.id,
                'product_id': False if no_product else self.product.id,
                'name': 'Test line' if no_product else self.product.name,
                'price_unit': 100,
                'quantity': 1})],
        })

    def test_invoice_ok(self):
        invoice = self.create_invoice(
            self.company1, self.journal1, self.account1)
        self.assertEquals(invoice.state, 'draft')
        invoice.action_invoice_open()
        self.assertEquals(invoice.state, 'open')
        invoice = self.create_invoice(
            self.company2, self.journal2, self.account2)

    def test_invoice_journal_error(self):
        with self.assertRaises(UserError):
            self.create_invoice(self.company1, self.journal2, self.account1)
        self.journal2.intercompany_map_ids = [(6, 0, self.journal1.ids)]
        invoice = self.create_invoice(
            self.company1, self.journal2, self.account1)
        self.assertEquals(invoice.journal_id, self.journal1)
        self.assertEquals(invoice.company_id, self.company1)
        with self.assertRaises(UserError):
            invoice.company_id = self.company2.id
        self.journal1.intercompany_map_ids = [(6, 0, self.journal2.ids)]
        invoice.company_id = self.company2.id
        self.assertEquals(invoice.company_id, self.company2)
        self.assertEquals(invoice.journal_id, self.journal2)

    def test_invoice_account_error(self):
        self.create_invoice(self.company1, self.journal1, self.account2)
        with self.assertRaises(UserError):
            self.create_invoice(
                self.company1, self.journal1, self.account2, no_product=True)
        self.account2.intercompany_map_ids = [(6, 0, self.account1.ids)]
        invoice = self.create_invoice(
            self.company1, self.journal1, self.account2, no_product=True)
        line = invoice.invoice_line_ids[0]
        self.assertEquals(line.account_id, self.account1)
        line.write({
            'account_id': self.account2.id,
        })
        self.assertEquals(invoice.company_id, self.company1)
        self.assertEquals(line.account_id, self.account1)

    def test_invoice_tax_error(self):
        tax1 = self.env['account.tax'].create({
            'company_id': self.company1.id,
            'name': 'Tax Test 10%',
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'amount': 10,
        })
        tax2 = self.env['account.tax'].create({
            'company_id': self.company2.id,
            'name': 'Tax Test 20%',
            'type_tax_use': 'sale',
            'amount_type': 'percent',
            'amount': 20,
        })
        self.product.taxes_id = [(6, 0, [tax1.id, tax2.id])]
        invoice = self.create_invoice(
            self.company1, self.journal1, self.account1)
        invoice.invoice_line_ids[0].invoice_line_tax_ids = [(6, 0, tax1.ids)]
        taxes = invoice.mapped('invoice_line_ids.invoice_line_tax_ids')
        self.assertEquals(taxes, tax1)
        invoice.compute_taxes()
        self.assertEquals(invoice.tax_line_ids.company_id, tax1.company_id)
        invoice.invoice_line_ids[0].product_id = False
        with self.assertRaises(UserError):
            invoice.invoice_line_ids[0].invoice_line_tax_ids = [
                (6, 0, tax2.ids)]
        tax2.intercompany_map_ids = [(6, 0, tax1.ids)]
        invoice.invoice_line_ids[0].invoice_line_tax_ids = [(6, 0, tax2.ids)]
        self.assertEquals(invoice.tax_line_ids.company_id, tax1.company_id)
        invoice.invoice_line_ids[0].product_id = self.product.id
        invoice.invoice_line_ids[0].invoice_line_tax_ids = [(6, 0, tax2.ids)]
        self.assertEquals(invoice.tax_line_ids.company_id, tax1.company_id)
        invoice.compute_taxes()
        invoice.action_invoice_open()
