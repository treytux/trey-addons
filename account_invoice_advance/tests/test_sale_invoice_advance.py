###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

_log = logging.getLogger(__name__)

# Important note! Install an account package


class TestSaleReturn(TransactionCase):

    def setUp(self):
        super().setUp()
        domain = [('company_id', '=', self.env.ref('base.main_company').id)]
        if not self.env['account.account'].search_count(domain):
            _log.warn(
                'Test skipped because there is no chart of account defined')
            self.skipTest('No Chart of account found')
            return
        self.partner = self.env.ref('base.res_partner_3')
        self.product = self.env.ref('product.expense_hotel')
        self.journal = self.env['account.journal'].search([
            ('company_id', '=', self.env.user.company_id.id)], limit=1)
        self.account = self.env.user.company_id.get_chart_of_accounts_or_fail()

    def create_wizard(self, invoice, formula):
        wizard = self.env['account.invoice.make_advance'].with_context({
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'sale.order',
            'active_ids': invoice.ids,
            'active_id': invoice[0].id})
        return wizard.create({'formula': formula})

    def test_invoice_advance_more_that_100(self):
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 50.,
                'quantity': 2})],
        })
        self.assertEquals(len(invoice.invoice_line_ids), 1)
        self.assertEquals(invoice.amount_untaxed, 100)
        self.assertEquals(invoice.amount_total, 100)
        wizard = self.create_wizard(invoice, '10+10')
        wizard.create_advance_invoices()
        self.assertEquals(len(invoice.advance_invoice_ids), 2)
        product_advance = self.env.ref(
            'account_invoice_advance.advance_product')
        for advance in invoice.advance_invoice_ids:
            self.assertEquals(advance.advance_invoice_id, invoice)
            self.assertEquals(advance.amount_untaxed, 10)
            self.assertEquals(advance.amount_advanced, 0)
            self.assertEquals(advance.percent_advanced, 0)
            self.assertEquals(len(advance.invoice_line_ids), 1)
            line = advance.invoice_line_ids
            self.assertFalse(line.advance_line_id)
            self.assertEquals(len(line.advance_line_ids), 1)
            self.assertEquals(line.name, 'Advance 10%')
            self.assertEquals(line.price_unit, 10)
            self.assertEquals(line.product_id, product_advance)
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        for line in invoice.mapped('invoice_line_ids.advance_line_id'):
            line.unlink()
        self.assertEquals(len(invoice.invoice_line_ids), 1)
        self.assertEquals(len(invoice.advance_invoice_ids), 0)
        wizard = self.create_wizard(invoice, '25+25')
        wizard.create_advance_invoices()
        self.assertEquals(len(invoice.advance_invoice_ids), 2)
        self.assertEquals(len(invoice.invoice_line_ids), 3)
        self.assertEquals(invoice.amount_advanced, 50)
        self.assertEquals(invoice.percent_advanced, 50)
        lines = invoice.mapped('invoice_line_ids.advance_line_id')
        self.assertEquals(len(lines), 2)
        lines[0].unlink()
        self.assertEquals(len(invoice.invoice_line_ids), 2)
        self.assertEquals(invoice.percent_advanced, 25)
        self.assertEquals(invoice.amount_advanced, 25)
        lines[1].unlink()
        self.assertEquals(len(invoice.invoice_line_ids), 1)
        self.assertEquals(invoice.percent_advanced, 0)
        self.assertEquals(invoice.amount_advanced, 0)
        wizard = self.create_wizard(invoice, '15.0+15,')
        wizard.create_advance_invoices()
        self.assertEquals(len(invoice.advance_invoice_ids), 2)
        self.assertEquals(invoice.percent_advanced, 30)
        self.assertEquals(invoice.amount_advanced, 30)
        invoice.advance_invoice_ids[0].unlink()
        self.assertEquals(len(invoice.advance_invoice_ids), 1)
        self.assertEquals(len(invoice.invoice_line_ids), 2)
        self.assertEquals(invoice.percent_advanced, 15)
        self.assertEquals(invoice.amount_advanced, 15)
        invoice.advance_invoice_ids.unlink()
        wizard = self.create_wizard(invoice, '+15,0+15.')
        wizard.create_advance_invoices()
        self.assertEquals(len(invoice.advance_invoice_ids), 2)
        self.assertEquals(invoice.percent_advanced, 30)
        self.assertEquals(invoice.amount_advanced, 30)
        advance_line = invoice.invoice_line_ids[-1:].advance_line_id
        invoice.state = 'open'
        with self.assertRaises(UserError):
            advance_line.unlink()
        invoice.state = 'draft'
        advance_line.invoice_id.state = 'open'
        with self.assertRaises(UserError):
            advance_line.unlink()
        advance_line.invoice_id.state = 'draft'
        advance_line.unlink()
        self.assertEquals(len(invoice.advance_invoice_ids), 1)
        self.assertEquals(len(invoice.invoice_line_ids), 2)
        self.assertEquals(invoice.percent_advanced, 15)
        self.assertEquals(invoice.amount_advanced, 15)
        wizard = self.create_wizard(invoice, '+15,0+15.')
        wizard.create_advance_invoices()
        invoices = invoice.advance_invoice_ids
        invoices[0].state = 'open'
        with self.assertRaises(UserError):
            invoice.unlink()
        invoices[0].state = 'draft'
        invoice.unlink()
        self.assertFalse(invoices.exists())

    def test_formula_get_percent_values(self):
        def formula(wizard, formula):
            wizard.formula = formula
            return wizard._get_percent_values()

        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 50.,
                'quantity': 2})],
        })
        wizard = self.create_wizard(invoice, '10+10')
        self.assertEquals(formula(wizard, '10+10'), [10, 10])
        self.assertEquals(formula(wizard, '+99,2+0.1'), [99.2, 0.1])
        with self.assertRaises(UserError):
            formula(wizard, '50+50')
        with self.assertRaises(UserError):
            formula(wizard, '+50+50')
        with self.assertRaises(UserError):
            formula(wizard, '99,2+0.8')

    def test_multicompany(self):
        company = self.env['res.company'].create({
            'name': 'New test company'
        })
        templates = self.env['account.chart.template'].search([])
        if not templates:
            _log.warn(
                'Test skipped because there is no chart of account defined '
                'new company')
            self.skipTest('No Chart of account found')
            return
        self.env.user.company_id = company.id
        templates[0].try_loading_for_current_company()
        self.env.user.company_id = self.env.ref('base.main_company').id
        journal = self.env['account.journal'].search([
            ('company_id', '=', company.id)], limit=1)
        account = company.get_chart_of_accounts_or_fail()
        invoice = self.env['account.invoice'].create({
            'company_id': company.id,
            'journal_id': journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': account.id,
                'price_unit': 50.,
                'quantity': 2})],
        })
        wizard = self.create_wizard(invoice, '+15,0+15.')
        wizard.create_advance_invoices()
        invoices = invoice.advance_invoice_ids
        wizard = self.env['account.invoice.confirm'].with_context({
            'tracking_disable': True,
            'mail_notrack': True,
            'mail_create_nolog': True,
            'active_model': 'account.invoice',
            'active_ids': invoices.ids,
            'active_id': 0}).create({})
        wizard.invoice_confirm()

    def test_invoice_advance_in_two_steps(self):
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'invoice_line_tax_ids': False,
                'price_unit': 50.,
                'quantity': 2})],
        })
        wizard = self.create_wizard(invoice, '10+10')
        wizard.create_advance_invoices()
        self.assertEquals(len(invoice.advance_invoice_ids), 2)
        self.assertEquals(invoice.percent_advanced, 20)
        self.assertEquals(invoice.amount_advanced, 20)
        wizard = self.create_wizard(invoice, '10,')
        wizard.create_advance_invoices()
        self.assertEquals(len(invoice.advance_invoice_ids), 3)
        self.assertEquals(invoice.percent_advanced, 30)
        self.assertEquals(invoice.amount_advanced, 30)

    def test_invoice_advance_with_taxes(self):
        tax = self.env['account.tax'].create({
            'name': '10% Tax',
            'amount_type': 'percent',
            'amount': 10,
            'type_tax_use': 'sale',
        })
        invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'invoice_line_tax_ids': [(6, 0, [tax.id])],
                'price_unit': 50.,
                'quantity': 2})],
        })
        self.assertEquals(invoice.amount_total, 110)
        wizard = self.create_wizard(invoice, '10+10')
        wizard.create_advance_invoices()
        self.assertEquals(invoice.amount_total, 87)
        self.assertEquals(len(invoice.advance_invoice_ids), 2)
        advance = invoice.advance_invoice_ids[0]
        self.assertEquals(advance.amount_total, 11.5)
        advance.invoice_line_ids.unlink()
        self.assertEquals(invoice.amount_total, 98.5)
