###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSalesTeamInvoiceJournal(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.account_receivable = self.env['account.account'].create({
            'code': 'RCV430',
            'name': 'Account Receivable',
            'account_type': 'asset_receivable',
            'reconcile': True,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'property_account_receivable_id': self.account_receivable.id,
        })
        self.account_income = self.env['account.account'].create({
            'code': 'INC700',
            'name': 'Product Sales',
            'account_type': 'income',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'list_price': 100.0,
            'standard_price': 50.0,
            'property_account_income_id': self.account_income.id,
        })
        self.journal_1 = self.env['account.journal'].create({
            'name': 'Test Sales Journal 1',
            'type': 'sale',
            'code': 'TSJ1',
        })
        self.journal_2 = self.env['account.journal'].create({
            'name': 'Test Sales Journal 2',
            'type': 'sale',
            'code': 'TSJ2',
        })
        self.sales_team = self.env['crm.team'].create({
            'name': 'Test Sales Team',
            'invoice_journal_id': self.journal_1.id,
        })

    def _create_sale_order(self, team=None):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'team_id': team.id if team else False,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        })

    def test_sales_team_invoice_journal_field(self):
        self.assertEqual(
            self.sales_team.invoice_journal_id.id, self.journal_1.id)
        self.sales_team.write({
            'invoice_journal_id': self.journal_2.id,
        })
        self.assertEqual(
            self.sales_team.invoice_journal_id.id, self.journal_2.id)

    def test_invoice_with_team_journal(self):
        sale = self._create_sale_order(self.sales_team)
        self.assertEqual(sale.team_id.id, self.sales_team.id)
        sale.action_confirm()
        invoice = sale._create_invoices()
        self.assertEqual(invoice.journal_id.id, self.journal_1.id)

    def test_invoice_without_team(self):
        sale = self._create_sale_order()
        self.assertFalse(sale.team_id)
        sale.action_confirm()
        invoice = sale._create_invoices()
        default_journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        self.assertEqual(invoice.journal_id.id, default_journal.id)

    def test_invoice_with_team_without_journal(self):
        team_without_journal = self.env['crm.team'].create({
            'name': 'Test Team Without Journal',
        })
        sale = self._create_sale_order(team_without_journal)
        self.assertEqual(sale.team_id.id, team_without_journal.id)
        self.assertFalse(team_without_journal.invoice_journal_id)
        sale.action_confirm()
        invoice = sale._create_invoices()
        default_journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        self.assertEqual(invoice.journal_id.id, default_journal.id)

    def test_multiple_sales_same_team(self):
        sale_1 = self._create_sale_order(self.sales_team)
        sale_2 = self._create_sale_order(self.sales_team)
        sale_1.action_confirm()
        sale_2.action_confirm()
        invoice_1 = sale_1._create_invoices()
        invoice_2 = sale_2._create_invoices()
        self.assertEqual(invoice_1.journal_id.id, self.journal_1.id)
        self.assertEqual(invoice_2.journal_id.id, self.journal_1.id)

    def test_change_team_journal(self):
        sale = self._create_sale_order(self.sales_team)
        self.assertEqual(
            self.sales_team.invoice_journal_id.id, self.journal_1.id)
        self.sales_team.write({
            'invoice_journal_id': self.journal_2.id,
        })
        sale.action_confirm()
        invoice = sale._create_invoices()
        self.assertEqual(invoice.journal_id.id, self.journal_2.id)

    def test_prepare_invoice_values(self):
        sale = self._create_sale_order(self.sales_team)
        invoice_vals = sale._prepare_invoice()
        self.assertEqual(invoice_vals['journal_id'], self.journal_1.id)
        self.assertEqual(invoice_vals['partner_id'], self.partner.id)
