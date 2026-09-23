###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestCurrencyRateOverride(TransactionCase):

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.currency_usd = self.env.ref('base.USD')
        self.currency_eur = self.env.ref('base.EUR')
        company_currency = self.company.currency_id
        if company_currency == self.currency_usd:
            self.fc_currency = self.currency_eur
            self.fc_rate = 1.0 / 0.85
        else:
            self.fc_currency = self.currency_usd
            self.fc_rate = 0.85
        self.company.account_sale_tax_id = False
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.product = self.env['product.product'].create({
            'name': 'Test Service',
            'type': 'service',
            'company_id': False,
        })
        self.account_income = self.env['account.account'].search([
            ('company_id', '=', self.company.id),
            ('account_type', '=', 'income'),
        ], limit=1)
        self.account_receivable = self.env['account.account'].search([
            ('company_id', '=', self.company.id),
            ('account_type', '=', 'asset_receivable'),
        ], limit=1)
        self.journal = self.env['account.journal'].search([
            ('company_id', '=', self.company.id),
            ('type', '=', 'sale'),
        ], limit=1)
        self.payment_term = self.env.ref(
            'account.account_payment_term_immediate', raise_if_not_found=False
        )
        self._set_currency_rate(self.fc_currency, self.fc_rate)
        self.invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'currency_id': self.fc_currency.id,
            'journal_id': self.journal.id,
            'invoice_date': '2026-08-01',
            'date': '2026-08-01',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 10,
                'price_unit': 100.0,
                'name': 'Test line',
                'account_id': self.account_income.id,
                'tax_ids': False,
            })],
        })
        self.invoice.action_post()

    def _set_currency_rate(self, currency, rate):
        self.env['res.currency.rate'].create({
            'currency_id': currency.id,
            'company_id': self.company.id,
            'rate': 1.0 / rate,
            'name': '2026-08-01',
        })

    def _get_invoice_fc_total(self, invoice):
        receivable = invoice.line_ids.filtered(
            lambda ln: ln.account_id.account_type == 'asset_receivable'
        )
        return abs(sum(receivable.mapped('amount_currency')))

    def _get_invoice_cc_total(self, invoice):
        receivable = invoice.line_ids.filtered(
            lambda ln: ln.account_id.account_type == 'asset_receivable'
        )
        return abs(sum(receivable.mapped('balance')))

    def test_wizard_default_values(self):
        ctx = {'default_move_id': self.invoice.id}
        wizard = self.env['currency.rate.override.wizard'].with_context(ctx).new()
        fc_total = self._get_invoice_fc_total(self.invoice)
        cc_total = self._get_invoice_cc_total(self.invoice)
        self.assertEqual(wizard.amount_currency_total, fc_total)
        self.assertEqual(wizard.amount_company_total, cc_total)
        self.assertAlmostEqual(
            wizard.current_rate, cc_total / fc_total, places=4)

    def test_onchange_new_amount_updates_rate(self):
        ctx = {'default_move_id': self.invoice.id}
        wizard = self.env['currency.rate.override.wizard']\
            .with_context(ctx).new()
        fc_total = self._get_invoice_fc_total(self.invoice)
        wizard.new_amount_company = 800.0
        wizard._onchange_new_amount_company()
        expected_rate = 800.0 / fc_total
        self.assertAlmostEqual(wizard.new_rate, expected_rate, places=4)

    def test_apply_recalculates_lines(self):
        fc_total = self._get_invoice_fc_total(self.invoice)
        cc_total = self._get_invoice_cc_total(self.invoice)
        wizard = self.env['currency.rate.override.wizard'].create({
            'move_id': self.invoice.id,
            'new_amount_company': 800.0,
            'amount_currency_total': fc_total,
            'amount_company_total': cc_total,
            'current_rate': cc_total / fc_total if fc_total else 1.0,
        })
        wizard.action_apply()
        self.assertEqual(self.invoice.state, 'posted')
        new_cc_total = self._get_invoice_cc_total(self.invoice)
        self.assertAlmostEqual(new_cc_total, 800.0, places=2)
        new_fc_total = self._get_invoice_fc_total(self.invoice)
        self.assertAlmostEqual(new_fc_total, fc_total, places=2)
        factor = 800.0 / cc_total
        for line in self.invoice.line_ids:
            old_balance = line.balance / factor
            self.assertAlmostEqual(line.balance, old_balance * factor, places=2)

    def test_apply_same_amount_raises_error(self):
        fc_total = self._get_invoice_fc_total(self.invoice)
        cc_total = self._get_invoice_cc_total(self.invoice)
        wizard = self.env['currency.rate.override.wizard'].create({
            'move_id': self.invoice.id,
            'new_amount_company': cc_total,
            'amount_currency_total': fc_total,
            'amount_company_total': cc_total,
            'current_rate': cc_total / fc_total if fc_total else 1.0,
        })
        with self.assertRaises(UserError) as cm:
            wizard.action_apply()
        self.assertEqual(
            cm.exception.name,
            'The new amount is the same as the current amount. Nothing to do.')

    def test_fails_on_unposted_invoice(self):
        invoice2 = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'currency_id': self.fc_currency.id,
            'journal_id': self.journal.id,
            'invoice_date': '2026-08-01',
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 1,
                    'price_unit': 100.0,
                    'name': 'Test',
                    'account_id': self.account_income.id,
                }),
            ],
        })
        fc_total2 = self._get_invoice_fc_total(invoice2)
        cc_total2 = self._get_invoice_cc_total(invoice2)
        wizard = self.env['currency.rate.override.wizard'].create({
            'move_id': invoice2.id,
            'new_amount_company': 80.0,
            'amount_currency_total': fc_total2,
            'amount_company_total': cc_total2,
            'current_rate': cc_total2 / fc_total2 if fc_total2 else 1.0,
        })
        with self.assertRaises(UserError) as cm:
            wizard.action_apply()
        self.assertEqual(
            cm.exception.name, 'The invoice must be in posted state.')

    def test_fails_on_same_currency_invoice(self):
        invoice_cc = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'currency_id': self.company.currency_id.id,
            'journal_id': self.journal.id,
            'invoice_date': '2026-08-01',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100.0,
                'name': 'Test',
                'account_id': self.account_income.id,
            })],
        })
        invoice_cc.action_post()
        fc_total_cc = self._get_invoice_fc_total(invoice_cc)
        cc_total_cc = self._get_invoice_cc_total(invoice_cc)
        current_rate_cc = (
            cc_total_cc / fc_total_cc if fc_total_cc else 1.0
        )
        wizard = self.env['currency.rate.override.wizard'].create({
            'move_id': invoice_cc.id,
            'new_amount_company': 90.0,
            'amount_currency_total': fc_total_cc,
            'amount_company_total': cc_total_cc,
            'current_rate': current_rate_cc,
        })
        with self.assertRaises(UserError) as cm:
            wizard.action_apply()
        self.assertEqual(
            cm.exception.name,
            'The invoice is not in a foreign currency.')
