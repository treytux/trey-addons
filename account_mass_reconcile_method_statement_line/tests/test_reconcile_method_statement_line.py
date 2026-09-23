###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import odoo.tests
from odoo.addons.account.tests.common import TestAccountReconciliationCommon


@odoo.tests.tagged('post_install', '-at_install')
class TestReconcileMethodStatementLine(TestAccountReconciliationCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(
            chart_template_ref='l10n_es.account_chart_template_pymes')

    def test_mass_reconcile_method_statement_line(self):
        bank_journal = self.env['account.journal'].search(
            [('name', 'ilike', 'bank')], limit=1)
        line_1 = self.env['account.bank.statement.line'].create({
            'journal_id': bank_journal.id,
            'date': '2024-01-01',
            'payment_ref': 'Pay Invoice number 001',
            'amount': 100.0,
        })
        line_2 = self.env['account.bank.statement.line'].create({
            'journal_id': bank_journal.id,
            'date': '2024-01-01',
            'payment_ref': 'Other payment invoice',
            'amount': 200.0,
        })
        move = self.env['account.move'].create({
            'journal_id': bank_journal.id,
            'date': '2024-01-01',
            'line_ids': [
                (0, 0, {
                    'name': 'Pay Invoice number 002',
                    'account_id': bank_journal.default_account_id.id,
                    'debit': 0,
                    'credit': 300,
                }),
                (0, 0, {
                    'name': 'Pay Invoice number 002',
                    'account_id': bank_journal.suspense_account_id.id,
                    'debit': 300,
                    'credit': 0,
                }),
            ],
        })
        account_628 = self.env.ref(
            f'l10n_es.{bank_journal.company_id.id}_account_common_628')
        mass_rec = self.env['account.mass.reconcile'].create({
            'name': 'mass_reconcile_1',
            'account': line_1.move_id.line_ids[0].account_id.id,
            'reconcile_method': [
                (0, 0, {
                    'name': 'mass.reconcile.statement.line',
                    'date_base_on': 'newest',
                    'sql_filter': 'Pay Invoice %',
                    'account_profit_id': account_628.id,
                    'account_lost_id': account_628.id,
                }),
            ],
        })
        self.assertFalse(mass_rec.last_history)
        mass_rec.run_reconcile()
        self.assertTrue(line_1.is_reconciled)
        self.assertIn(
            account_628, line_1.move_id.line_ids.mapped('account_id'))
        self.assertEqual(len(mass_rec.last_history), 1)
        self.assertNotIn(
            account_628, line_2.move_id.line_ids.mapped('account_id'))
        self.assertIn(
            bank_journal.default_account_id,
            move.line_ids.mapped('account_id'))
        self.assertIn(
            bank_journal.suspense_account_id,
            move.line_ids.mapped('account_id'))
        mass_rec.reconcile_method[0].write({
            'account_profit_id': bank_journal.default_account_id.id,
            'account_lost_id': bank_journal.suspense_account_id.id,
        })
        mass_rec.run_reconcile()
        self.assertIn(
            account_628, line_1.move_id.line_ids.mapped('account_id'))
